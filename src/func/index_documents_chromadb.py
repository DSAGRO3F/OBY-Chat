"""
Indexation des sources (DOCX & WEB) dans ChromaDB.

Ce module parcourt un répertoire de fichiers JSON structurés et alimente deux
collections ChromaDB persistantes :
- BASE_DOCX_COLLECTION (contenus "docx" : fiches/chapitres, champ `texte_complet`)
- BASE_WEB_COLLECTION  (contenus "web" : sections de pages, champ `sections[].texte`)

Caractéristiques :
- Utilise un VectorStore LangChain (`langchain_chroma.Chroma`) connecté à un client
  Chroma persistant fourni par `src.utils.chroma_client.get_chroma_client`.
- Les embeddings sont centralisés par `src.utils.chroma_client.get_embedding_model`
  (OpenAI ou HuggingFace selon la configuration). Cela garantit que l’indexation et
  la recherche utilisent exactement le même modèle d’embedding.
- Insertion par lots (batching) pour de bonnes performances et une utilisation
  mémoire maîtrisée.
- Métadonnées nettoyées/normalisées (titres, types, sources, URL absolues/domaines
  pour le web, identifiants, etc.).
- Journalisation simple (progression, erreurs d’E/S ou d’indexation).

Prérequis :
- Les chemins de persistance Chroma et les noms de collections sont définis dans
  la configuration (cf. `config.config`).
- Si EMBEDDING_PROVIDER="openai", l’environnement doit contenir la clé
  `OPENAI_API_KEY`.

Exemple minimal :
    from src.utils.chroma_client import get_chroma_client
    client = get_chroma_client()
    index_documents("data/input/poa_docx", "docx", client)
    index_documents("data/input/web_pages", "web", client)
"""



from uuid import uuid4
from datetime import datetime
import os, json
from chromadb.api import ClientAPI
import hashlib
from pathlib import Path
from urllib.parse import urlparse, urljoin, urldefrag
import re, unicodedata
from langchain_chroma import Chroma

from src.utils.chroma_client import get_chroma_client, get_embedding_model, get_collection_names


# ======================== #
# --- Normaliser texte --- #
# ======================== #

def _norm_for_eq(s: str) -> str:
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    # supprime zero-width chars les plus courants
    s = s.replace("\u200b", "").replace("\ufeff", "")
    # compresse tous les espaces unicode
    s = re.sub(r"\s+", " ", s, flags=re.UNICODE)
    return s.strip().casefold()

# ============================================================#
# --- Pour éviter de remonter des None dans metadata/chroma---#
# ============================================================#

def _safe_str(v, default=""):
    # Si v est None ou chaîne vide, retourne default
    if v is None:
        return default
    if isinstance(v, str):
        return v if v.strip() else default
    return str(v)


def _sanitize_meta(d: dict) -> dict:
    """Garde uniquement Bool/Int/Float/Str, enlève les None et vide."""
    out = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, (bool, int, float)):
            out[k] = v
        elif isinstance(v, str):
            vv = v.strip()
            if vv != "":
                out[k] = vv
        else:
            # si c'est un autre type (list/dict/None), on le convertit en str propre
            s = str(v).strip()
            if s:
                out[k] = s
    return out


# ============================================================#
# ---Pour arriver à capturer les url valides pour metadata ---#
# ============================================================#

CANDIDATE_URL_KEYS = ["source_url", "url", "page_url", "canonical_url", "canonical", "href", "permalink"]
CANDIDATE_BASE_KEYS = ["base_url", "site_url", "site", "origin"]

def _first_key(d: dict, keys: list[str]) -> str | None:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None

def _is_http_url(u: str | None) -> bool:
    return isinstance(u, str) and u.lower().startswith(("http://", "https://"))

def _infer_domain_from_filename(file: str) -> str | None:
    # ex: "www.has-sante.fr_jcms_c_1718248_fr_....json" -> "www.has-sante.fr"
    head = file.split("_", 1)[0]
    return head if "." in head else None

def _normalize_abs_url(raw_url: str | None, *, file: str, fiche: dict) -> tuple[str | None, str | None]:
    """Retourne (url_absolue_normalisée, domaine) ou (None, None)."""
    if not raw_url:
        return None, None
    raw = raw_url.strip()

    # URLs type "//example.com/..." -> les rendre absolues
    if raw.startswith("//"):
        raw = "https:" + raw

    # Cas déjà absolu
    if _is_http_url(raw):
        url, _frag = urldefrag(raw)          # enlève l’ancre
        if url.endswith("/"):
            url = url[:-1]                   # normalise sans slash final
        return url, urlparse(url).netloc

    # Cas relatif -> tenter une base
    base = _first_key(fiche, CANDIDATE_BASE_KEYS)
    if base and _is_http_url(base):
        absu = urljoin(base.rstrip("/") + "/", raw.lstrip("/"))
        url, _ = urldefrag(absu)
        if url.endswith("/"):
            url = url[:-1]
        return url, urlparse(url).netloc

    # Dernier recours : déduire le domaine depuis le nom du fichier
    dom = _infer_domain_from_filename(file)
    if dom:
        absu = f"https://{dom}/{raw.lstrip('/')}"
        url, _ = urldefrag(absu)
        if url.endswith("/"):
            url = url[:-1]
        return url, dom

    return None, None


def rebuild_collection_from_disk(client: ClientAPI, source_type: str, source_dir: str) -> None:
    """Reconstruit intégralement une collection Chroma à partir d’un répertoire local.

        Supprime/réinitialise la collection associée à `source_type`, puis relance
        l’indexation de tous les fichiers JSON présents dans `source_dir`. À utiliser
        après un changement de modèle d’embedding, une évolution du schéma de
        métadonnées ou pour repartir d’un index propre.

        Args:
            client: Instance du client Chroma persistant.
            source_type: Type de source à (re)construire. Doit valoir "docx" ou "web".
            source_dir: Chemin du répertoire contenant les fichiers JSON à indexer.

        Returns:
            None. La progression et les éventuelles erreurs sont journalisées.
        """

    name = get_collection_names(source_type)
    try:
        client.delete_collection(name=name)
        print(f"🔴 Collection supprimée : {name}")
    except Exception as e:
        print(f"🔴 Impossible de supprimer (peut-être absente) {name} : {e}")
    # Réindexation complète depuis le répertoire (crée la collection si besoin)
    index_documents(source_dir=source_dir, source_type=source_type, client=client)
    print(f"✅ Collection reconstruite : {name}")


def index_documents(source_dir: str, source_type: str, client: "ClientAPI|None"):
    """Indexe des fichiers JSON dans la collection Chroma correspondant au type de source.

        Pour `source_type="docx"`, lit `texte_complet` et ses métadonnées par fiche,
        puis ajoute les passages à la collection DOCX. Pour `source_type="web"`, lit
        les `sections[].texte`, normalise l’URL/le domaine si disponibles, puis ajoute
        les passages à la collection WEB. L’embedding utilisé est centralisé afin
        d’assurer la cohérence avec la phase de recherche.

        Args:
            source_dir: Chemin du répertoire contenant les fichiers JSON à indexer.
            source_type: Type de contenu à indexer ("docx" ou "web").
            client: Client Chroma persistant. S’il est None, un client sera obtenu
                via la fabrique interne.

        Returns:
            None. La progression, le nombre d’éléments indexés et les erreurs éventuelles
            sont journalisés.
        """

    print("🟡 Lancement fonction -> index_documents()... ")
    if client is None:
        client = get_chroma_client()

    if source_type not in ("docx", "web"):
        raise ValueError("source_type doit être 'docx' ou 'web'.")

    collection_name = get_collection_names(source_type)
    print(f"🟡Initialisation de la collection {collection_name}...")

    # 1) Vectorstore LangChain avec embedding centralisé (OpenAIEmbeddings si config openai)
    vectorstore = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=get_embedding_model(),
    )

    print(f"🟡Indexation des documents depuis : {source_dir} (type: {source_type})")

    total_files, indexed_chunks = 0, 0

    BATCH = 128
    batch_texts: list[str] = []
    batch_metas: list[dict] = []
    batch_ids: list[str] = []

    def _flush_batch():
        nonlocal batch_texts, batch_metas, batch_ids, indexed_chunks
        if not batch_texts:
            return
        try:
            vectorstore.add_texts(texts=batch_texts, metadatas=batch_metas, ids=batch_ids)
            indexed_chunks += len(batch_texts)
            print(f"   ↳ batch ajouté : {len(batch_texts)} docs (total indexés: {indexed_chunks})")
        except Exception as e:
            print(f"❌ Erreur d’ajout batch ({len(batch_texts)} docs) : {e}")
        finally:
            batch_texts.clear()
            batch_metas.clear()
            batch_ids.clear()

    for file in os.listdir(source_dir):
        if not file.endswith(".json"):
            continue
        total_files += 1
        print(f"🟡 Traitement du fichier JSON : {file}")

        file_path = os.path.join(source_dir, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Erreur de lecture {file}: {e}")
            continue

        fiches = data if isinstance(data, list) else [data]

        for fiche in fiches:

            # ✅ docx
            if source_type == "docx":
                chunk_text = (fiche.get("texte_complet") or "").strip()
                if not chunk_text:
                    print(f"⚠️ Texte vide pour le fichier {file}, source_type : {source_type}")
                    continue

                titre = _safe_str(fiche.get("titre"), "Titre inconnu")
                type_document = _safe_str(fiche.get("type_document"), "document")
                source = _safe_str(fiche.get("source_doc"), "source_docx_inconnue")

                chunk_id = f"{file}_{uuid4().hex[:8]}"
                basename = Path(file).name
                fiche_id = hashlib.md5(f"{source}|{titre}".encode("utf-8")).hexdigest()

                meta = {
                    "titre": titre,
                    "type_document": type_document,
                    "source": source,
                    "source_group": source,
                    "source_path": str(file),
                    "source_basename": basename,
                    "fiche_id": fiche_id,
                    "section_index": 0,
                    "source_type": "docx",
                    "date_indexation": datetime.now().strftime("%Y-%m-%d"),
                    "id": chunk_id,  # utile pour traçabilité
                }
                meta = _sanitize_meta(meta)

                batch_texts.append(chunk_text)
                batch_metas.append(meta)
                batch_ids.append(chunk_id)

                print(f"➡️ Titre fiche : {titre} - Source : {source}")

            if len(batch_texts) >= BATCH:
                _flush_batch()



            # ✅ WEB
            elif source_type == "web":
                sections = fiche.get("sections") or []
                if not sections:
                    print(f"⚠️ Aucune section trouvée dans le fichier {file}, source_type : {source_type}")
                    continue

                # 1) URL candidate
                raw_url = _first_key(fiche, CANDIDATE_URL_KEYS)

                # 2) Normalisation URL absolue + domaine
                url_val, domain = _normalize_abs_url(raw_url, file=file, fiche=fiche)

                titre = (
                        _safe_str(fiche.get("titre"), None)
                        or _safe_str(fiche.get("page_title"), None)
                        or _safe_str(fiche.get("title"), None)
                        or _safe_str((fiche.get("metadata") or {}).get("title"), "Sans titre")
                )
                titre = _norm_for_eq(titre)

                type_document = _safe_str(fiche.get("type_document"), "page_web")
                source_for_histo = url_val or "Source inconnue"

                print(f"➡️ Titre fiche : {titre} - Source : {source_for_histo}")

                if not url_val:
                    print(
                        f"🟡 [WEB] Pas d'URL exploitable pour {file} ; clés dispo: "
                        f"{[k for k in ['source_url', 'url', 'page_url', 'canonical_url', 'canonical', 'href', 'permalink', 'base_url'] if fiche.get(k)]}"
                    )

                basename = Path(file).name

                for i, section in enumerate(sections):
                    chunk_text = (section.get("texte") or "").strip()
                    if not chunk_text:
                        print(f"⚠️ Chunk vide dans section {i} du fichier {file}")
                        continue

                    chunk_id = f"{file}_{uuid4().hex[:8]}"

                    meta = {
                        "titre": titre,
                        "type_document": type_document,
                        "source": source_for_histo,  # compat historique
                        "section_index": int(i),
                        "source_type": "web",
                        "date_indexation": datetime.now().strftime("%Y-%m-%d"),
                        "source_path": str(file),
                        "source_basename": basename,
                        "id": chunk_id,
                    }
                    if url_val:
                        meta["url"] = url_val
                    if domain:
                        meta["domain"] = domain

                    meta = _sanitize_meta(meta)

                    batch_texts.append(chunk_text)
                    batch_metas.append(meta)
                    batch_ids.append(chunk_id)

                    if len(batch_texts) >= BATCH:
                        _flush_batch()

            # 🟠 flush final — une seule fois pour DOCX/WEB
            _flush_batch()

            print(f"✅ {indexed_chunks} sections indexées à partir de {total_files} fichiers.")