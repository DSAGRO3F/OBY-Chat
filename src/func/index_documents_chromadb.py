"""
    Outils d’indexation ChromaDB pour OBY-IA.

    Ce module expose des utilitaires pour (ré)indexer des collections ChromaDB
    à partir de répertoires de JSON structurés :
    - `base_docx` : documents dérivés de fiches DOCX,
    - `base_web`  : documents dérivés du scraping de sites de confiance.

    Fournit notamment une fonction de reconstruction qui
    supprime la collection ciblée puis la reconstruit à partir des fichiers
    présents sur disque, garantissant l’absence de documents « fantômes »
    lorsqu’il y a des suppressions ou des changements de configuration.

    Fonctions attendues dans ce module (ou importées) :
    - `index_documents(source_dir, source_type, client)`: effectue l’indexation
      à partir d’un répertoire JSON (crée la collection si nécessaire).
    - `collection_name_for(source_type)`: mappe 'docx'/'web' vers le nom
      de collection ChromaDB (p. ex. 'base_docx' / 'base_web').
    - `rebuild_collection_from_disk(client, source_type, source_dir)`: supprime
      la collection puis réindexe depuis le disque (cf. docstring ci-dessous).

"""


from uuid import uuid4
from datetime import datetime
import os, json
from chromadb.api import ClientAPI
import hashlib
from pathlib import Path
from urllib.parse import urlparse, urljoin, urldefrag

from chromadb.utils import embedding_functions
from src.utils.chroma_client import get_chroma_client

from config.config import EMBEDDING_MODEL_NAME

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



def _collection_name_for(source_type: str) -> str:
    """Retourne le nom de collection ChromaDB pour un `source_type` donné.

        Args:
            source_type: 'docx' ou 'web'.

        Returns:
            Nom de collection (p. ex. 'base_docx' ou 'base_web').

        Raises:
            ValueError: si `source_type` n’est pas 'docx' ni 'web'.
    """

    if source_type not in {"docx", "web"}:
        raise ValueError(f"source_type invalide: {source_type!r} (attendus: 'docx' ou 'web')")
    return "base_docx" if source_type == "docx" else "base_web"



def rebuild_collection_from_disk(client: ClientAPI, source_type: str, source_dir: str) -> None:
    """
    Reconstruit entièrement la collection ChromaDB d’un type donné.

    Objectif: garantir la cohérence parfaite entre l’état
    disque (répertoire JSON) et l’index ChromaDB (par ex. après suppressions
    de fichiers, changements de configuration des sites, migration d’embedding,
    etc.).

    1) supprime la collection ciblée (si elle existe),
    2) (re)crée et réindexe la collection en appelant `index_documents`
       à partir des JSON présents dans `source_dir`.

    Args:
        client: instance ChromaDB (ClientAPI) déjà initialisée.
        source_type: 'docx' ou 'web' (détermine la collection à reconstruire).
        source_dir: chemin du répertoire contenant les JSON à indexer.

    Raises:
        ValueError: si `source_type` n’est pas 'docx' ni 'web'.
        Exception: si la suppression ou la réindexation échoue (erreurs du client
            ChromaDB ou d’E/S remontées telles quelles).

    Returns:
        None

    """

    name = _collection_name_for(source_type)
    try:
        client.delete_collection(name=name)
        print(f"🔴 Collection supprimée : {name}")
    except Exception as e:
        print(f"🔴 Impossible de supprimer (peut-être absente) {name} : {e}")
    # Réindexation complète depuis le répertoire (crée la collection si besoin)
    index_documents(source_dir=source_dir, source_type=source_type, client=client)
    print(f"✅ Collection reconstruite : {name}")


def index_documents(source_dir: str, source_type: str, client: ClientAPI):
    """
    Indexe les documents JSON contenus dans un répertoire dans une collection ChromaDB.

    Chaque document est découpé en sections (ou chunk unique dans le cas d'un fichier DOCX complet),
    puis inséré dans une base vectorielle avec ses métadonnées.

    Args:
        source_dir (str): Chemin du dossier contenant les fichiers JSON à indexer.
        source_type (str): Type de document à indexer, soit 'docx' soit 'web'.
        client (Client): Instance du client ChromaDB utilisée pour la persistance des données.

    Entrées :
        - source_dir (str) : Dossier contenant les fichiers JSON.
        - source_type (str) : 'docx' ou 'web' (détermine la collection cible).

    Sorties :
        - Indexation des chunks dans une collection nommée selon la source.


    Raises:
        ValueError: Si le type de source est invalide (autre que 'docx' ou 'web').
    """

    print("🟡 Lancement fonction -> index_documents()... ")
    if client is None:
        client = get_chroma_client()

    if source_type not in ("docx", "web"):
        raise ValueError("source_type doit être 'docx' ou 'web'.")

    collection_name = "base_docx" if source_type == "docx" else "base_web"

    # 🔹 Initialisation collection
    print(f'🟡Initialisation de la collection {collection_name}...')
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )

    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)

    print(f"🟡Indexation des documents depuis : {source_dir} (type: {source_type})")

    total_files, indexed_chunks = 0, 0

    for file in os.listdir(source_dir):
        if not file.endswith(".json"):
            continue
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
            print(
                f"➡️ Titre fiche : {fiche.get('titre', 'Sans titre')} - Source : {fiche.get('source_url', 'inconnue')}")

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
                }
                meta = _sanitize_meta(meta)

                try:
                    collection.add(documents=[chunk_text], ids=[chunk_id], metadatas=[meta])
                    indexed_chunks += 1
                except Exception as e:
                    print(f"❌ Erreur d’ajout depuis {file} : {e}\n[DEBUG meta]={meta}")

            elif source_type == "web":
                sections = fiche.get("sections") or []
                if not sections:
                    print(f"⚠️ Aucune section trouvée dans le fichier {file}, source_type : {source_type}")
                    continue

                # 1) extraire une URL brute parmis plusieurs clés possibles
                raw_url = _first_key(fiche, CANDIDATE_URL_KEYS)

                # 2) calculer une URL absolue + domaine
                url_val, domain = _normalize_abs_url(raw_url, file=file, fiche=fiche)

                titre = _safe_str(fiche.get("titre"), "Sans titre")
                type_document = _safe_str(fiche.get("type_document"), "page_web")
                source_for_histo = url_val or "Source inconnue"

                if not url_val:
                    # log pour debug: quelles clés présentait la fiche ?
                    print(f"🟡 [WEB] Pas d'URL exploitable pour {file} ; clés dispo: "
                          f"{[k for k in ['source_url', 'url', 'page_url', 'canonical_url', 'canonical', 'href', 'permalink', 'base_url'] if fiche.get(k)]}")

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
                    }
                    if url_val:
                        meta["url"] = url_val
                    if domain:
                        meta["domain"] = domain

                    meta = _sanitize_meta(meta)

                    try:
                        collection.add(documents=[chunk_text], ids=[chunk_id], metadatas=[meta])
                        indexed_chunks += 1
                    except Exception as e:
                        print(f"❌ Erreur d'ajout d'une section depuis {file}, section {i} : {e}\n[DEBUG meta]={meta}")

        total_files += 1

    print(f"✅ {indexed_chunks} sections indexées à partir de {total_files} fichiers.")

