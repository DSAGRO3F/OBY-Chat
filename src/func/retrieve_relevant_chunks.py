"""
Outils de récupération et de formatage des extraits (“chunks”) pour le RAG.

Ce module interroge deux collections Chroma (DOCX prioritaire, WEB secondaire),
sélectionne les passages pertinents, puis garde côté WEB uniquement ceux qui
apportent une information complémentaire (TF-IDF “novelty”) et restent proches
de la requête (similarité embeddings). Les extraits sont formatés avec des
identifiants [DOCXn]/[WEBn], titres, sources/URLs et un fallback
[WEB_PERTINENCE] si aucun lien web pertinent n’est retenu. Seuils et top-K
sont pilotés par la configuration.
"""

from langchain_chroma import Chroma
from langchain.schema import Document

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except Exception:
    from langchain_community.embeddings import (
        HuggingFaceBgeEmbeddings as HuggingFaceEmbeddings
    )

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import unicodedata

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from src.utils.chroma_client import get_chroma_client
from src.utils.vector_db_utils import is_chroma_index_ready

from config.config import int_1 as DOCX_TOPK, int_2 as WEB_TOPK
from config.config import EMBEDDING_MODEL_NAME, NORMALIZE_EMBEDDINGS
from config.config import (
                           sim_threshold as SIM_THRESHOLD,
                           nov_min as NOV_MIN,
                           nov_max as NOV_MAX,
)




# --- 🟨 Sécurisation fonctions ---
# Garder la clé "embedding mismatch" en anglais dans le message pour que les tests la retrouvent.
EMBEDDING_MISMATCH_MESSAGE = (
    "Embedding mismatch: l'index Chroma n'a pas été construit avec le même modèle "
    "d'embeddings (ou la même dimension) que celui utilisé pour la requête."
)

MISSING_COLLECTION_MESSAGE_TEMPLATE = (
    "Collection introuvable : '{name}'. Veuillez (ré)indexer les données avant la recherche."
)

def missing_collection_message(name: str) -> str:
    return MISSING_COLLECTION_MESSAGE_TEMPLATE.format(name=name)

# alias francisé — même fonction
collection_absente_message = missing_collection_message

# idem pour les templates
COLLECTION_ABSENTE_MESSAGE_TEMPLATE = MISSING_COLLECTION_MESSAGE_TEMPLATE


__all__ = [
    "retrieve_relevant_chunks",
    "_format_results_with_ids",
    "_tfidf_novelty_scores",
    "_pick_title",
    "_display_domain",
    "missing_collection_message",
    "collection_absente_message",
    "EMBEDDING_MISMATCH_MESSAGE",
    "MISSING_COLLECTION_MESSAGE_TEMPLATE",
    "COLLECTION_ABSENTE_MESSAGE_TEMPLATE",
]


# --- 🟨 Helpers ----
def _url_norm(u: str | None) -> str:
    if not u:
        return ""
    return (u.strip().rstrip("/").lower())

def _slug_from_url(u: str) -> str:
    try:
        path = urlparse(u).path or ""
        slug = (path.strip("/").split("/")[-1] or "").replace("-", " ").strip()
        return f"{slug[:1].upper()}{slug[1:]}" if slug else ""
    except Exception:
        return ""



# --- 🟨 Etiquetage des chunks ---
def _display_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""

def _shorten(text: str, max_chars: int = 900) -> str:
    if not text:
        return ""
    t = " ".join(text.split())
    return (t[:max_chars-1] + "…") if len(t) > max_chars else t

def _pick_title(meta: dict, source: str, is_web: bool) -> str:
    title = meta.get("titre") or meta.get("title") or meta.get("doc_title")
    if (not title or not title.strip()) and is_web:
        from urllib.parse import urlparse
        host = urlparse(source).netloc.lower()
        if host.startswith("www."): host = host[4:]
        return f"[Titre indisponible] — {host}" if host else "[Titre indisponible]"
    return title or "Titre inconnu"



#  --- 🟨 Mesure de complémentarité des web documents versus docx documents ---
def _strip_accents(s: str) -> str:
    if not s:
        return s
    return "".join(
        ch for ch in unicodedata.normalize("NFD", s)
        if unicodedata.category(ch) != "Mn"
    )

FRENCH_STOPWORDS_RAW: List[str] = [
    "le","la","les","un","une","des","de","du","au","aux","en","dans","sur","sous","avec",
    "et","ou","mais","donc","or","ni","car","à","a","pour","par","chez","vers","sans",
    "ce","cet","cette","ces","son","sa","ses","leur","leurs","mon","ma","mes","ton","ta","tes",
    "il","elle","ils","elles","on","nous","vous","je","tu","y","se","d’","l’","qu’","n’","d","l","qu","n",
    "est","sont","été","etre","être","fait","faire","peut","peuvent","doit","doivent",
    "plus","moins","très","tres","bien","mal","afin","ainsi","dont","comme","si","sur",
]

FRENCH_STOPWORDS = sorted({
    _strip_accents(w.lower().replace("’", "'")).strip("'")
    for w in FRENCH_STOPWORDS_RAW
} | {"ete"})


def _tfidf_novelty_scores(docx_text_agg: str, web_texts: list[str]) -> np.ndarray:
    """
    Retourne un array de 'nouveauté' = 1 - cosine_sim(docx_agg, web_i).
    Plus c'est proche de 1, plus le web est 'différent' des DOCX -> donc complémentaire.
    """
    corpus = [docx_text_agg] + web_texts
    # n-grammes 1–2, accents normalisés, stopwords FR intégrés
    # token_pattern pour garder les mots ≥2 caractères avec apostrophes françaises
    vec = TfidfVectorizer(
        stop_words=FRENCH_STOPWORDS,
        strip_accents='unicode',
        ngram_range=(1, 2),
        min_df=1,
        max_features=30000,
        token_pattern=r"(?u)\b\w[\w’']+\b",
    )
    X = vec.fit_transform(corpus)  # row 0 = docx_agg, rows 1.. = webs
    if X.shape[1] == 0:
        return np.ones(len(web_texts))  # pas de voc -> considérer tout 'nouveau' pour ne pas bloquer
    sims = cosine_similarity(X[0], X[1:]).ravel()
    novelty = 1.0 - sims
    return novelty



# --- 🟨 Formatage chunks ---
def _format_results_with_ids(
        results_docx: list,
        results_web: list,
        docx_limit: int | None = None,  # si None -> DOCX_TOPK
        web_limit: int | None = None,  # si None -> WEB_TOPK
        separator: str = "\n\n",
        *,
        query: str | None = None,
        embedding_model: Any | None = None,
        sim_threshold: float = SIM_THRESHOLD,
        nov_min: float = NOV_MIN,
        nov_max: float = NOV_MAX,
) -> str:
    """
    - DOCX en premier, bornés à docx_limit.
    - WEB complémentaires uniquement (score de nouveauté >= seuil), bornés à web_limit.
    - Si aucun web pertinent retenu: insère un message explicite.
    """
    docx_limit = DOCX_TOPK if docx_limit is None else docx_limit # obj. chunks capturés pour docx
    web_limit = WEB_TOPK if web_limit is None else web_limit # obj. chunks capturés pour web

    # 1) Limiter le volume dès l’entrée pour docx
    results_docx = (results_docx or [])[:max(0, docx_limit)]

    # 2) Texte de référence DOCX (pour la mesure de complémentarité)
    docx_text_agg = " ".join([(getattr(d, "page_content", "") or "") for d in results_docx])

    blocks: list[str] = []
    counters = {"DOCX": 0, "WEB": 0}

    # 3) DOCX -> on considère ces documents comme les textes de référence
    # La mesure de complémentarité est mesurée par rapport à ces textes
    for doc in results_docx:
        meta = getattr(doc, "metadata", {}) or {}
        source = meta.get("source") or meta.get("source_url") or meta.get("resolved_url") or "Source inconnue"
        title = _pick_title(meta, source, is_web=False)
        extrait = _shorten((getattr(doc, "page_content", "") or "").strip())

        fiche_num = meta.get("fiche_numero") or meta.get("fiche")
        display_title = f"Fiche {fiche_num} — {title}" if fiche_num and not title.lower().startswith(
            "fiche") else title

        counters["DOCX"] += 1
        idx = counters["DOCX"]
        blocks.append(
            f"[DOCX{idx}] {display_title}\n"
            f"source: {source}\n"
            f"extrait: {extrait}"
        )

    # 4) WEB -> y a t-il dans ces textes un vocabulaire complémentaire ?
    # on ne garde que les documents web qui apportent une information nouvelle par rapport à docx
    # la décision se fait par la bande [nov_min, nov_max] + la sim au query.
    # if sim(query, web) >= 0.70 and 0.30 <= novelty(docx_agg, web) <= 0.75: --> garder(web)
    candidate_metas: List[Tuple[Dict[str, Any], str, str]] = []
    candidate_texts: List[str] = []
    selected_web_blocks: list[str] = []

    for doc in results_web or []:
        meta = getattr(doc, "metadata", {}) or {}
        source = meta.get("source") or meta.get("source_url") or meta.get("resolved_url") or ""
        text = (getattr(doc, "page_content", "") or "").strip()
        if not text:
            continue
        candidate_metas.append((meta, source, text))
        candidate_texts.append(text)

    if candidate_texts:
        # 4.1 Test apport info. nouvvelle par les web docs
        nov = _tfidf_novelty_scores(docx_text_agg, candidate_texts)

        # 4.2 Similarité requête↔web via embeddings (optionnelle)
        if query and embedding_model:
            try:
                q_vec = np.array(embedding_model.embed_query(query), dtype=np.float32)  # (D,)
                w_vecs = np.array(embedding_model.embed_documents(candidate_texts), dtype=np.float32)  # (N, D)
                qn = np.linalg.norm(q_vec) + 1e-8
                wn = np.linalg.norm(w_vecs, axis=1) + 1e-8
                sims = (w_vecs @ q_vec) / (wn * qn)  # (N,)
            except Exception as e:
                print(f"[WARN] Similarité requête↔web indisponible ({e}) — fallback sims=0")
                sims = np.zeros(len(candidate_texts), dtype=np.float32)
        else:
            sims = np.zeros(len(candidate_texts), dtype=np.float32)

        # 4.3 Ordre : pertinence d’abord
        order = np.argsort(-sims)

        # 4.4 Déduplication par URL normalisée
        seen_urls = set()

        for j in order:
            if len(selected_web_blocks) >= web_limit:
                break

            n = float(nov[j])
            s = float(sims[j])
            meta, source, text = candidate_metas[j]
            urln = _url_norm(source)

            # Gating : pertinence ET complémentarité modérée
            if s < sim_threshold:
                continue
            if not (nov_min <= n <= nov_max):
                continue
            if urln and urln in seen_urls:
                continue

            seen_urls.add(urln)
            counters["WEB"] += 1
            idx = counters["WEB"]

            # Titre lisible (fallback)
            title = _pick_title(meta, source, is_web=True)
            if title.startswith("[Titre indisponible]") and source:
                slug = _slug_from_url(source)
                if slug:
                    title = slug

            site = meta.get("site_name") or _display_domain(source) or "source_web_inconnue"
            extrait = _shorten(text)
            url_line = f"url: {source}" if source else "url: [URL indisponible]"
            selected_web_blocks.append(
                f"[WEB{idx}] {title}\n"
                f"site: {site}\n"
                f"{url_line}\n"
                f"extrait: {extrait}"
            )

        # Debug
        try:
            debug_labels = []
            for i, (m, src, _) in enumerate(candidate_metas, start=1):
                titre = m.get("titre") or m.get("title") or "[Titre indisponible]"
                domaine = _display_domain(src) if src else "n/a"
                debug_labels.append(f"WEB{i}::{domaine}::{titre[:40]}")
            print("[🟧 DEBUG] novelty scores:", list(map(float, nov)))
            print("[🟧 DEBUG] sim(query, web):", list(map(lambda x: round(float(x), 3), sims)))
            print("[🟧 DEBUG] candidates:", debug_labels)
        except Exception:
            pass
    else:
        # aucun candidat web
        pass

    # 5) Assemblage et fallback “aucun web pertinent”
    if selected_web_blocks:
        blocks.extend(selected_web_blocks)
    else:
        blocks.append("[WEB_PERTINENCE] Aucun lien web pertinent pour cette recherche.")

    return separator.join(blocks)




# --- 🟨 Retrieve chunks ---
def retrieve_relevant_chunks(
    query: str,
    top_k_docx: int = DOCX_TOPK,
    top_k_web: int = WEB_TOPK,
    separator: str = "\n\n"
) -> str:
    """
    Récupère et formatte les passages les plus pertinents à partir d'une requête utilisateur.

    Cette fonction interroge deux collections ChromaDB :
    - d'abord la collection "base_docx" (prioritaire),
    - puis la collection "base_web" (secondaire).

    Les extraits les plus proches de la requête sont sélectionnés par similarité vectorielle,
    puis concaténés et formatés pour être injectés dans le prompt du modèle LLM.

    Args:
        query: Requête utilisateur ou texte à rechercher.
        top_k_docx: Nombre d'extraits à récupérer depuis la base documentaire "docx".
        top_k_web: Nombre d'extraits à récupérer depuis la base documentaire "web".
        separator: Chaîne utilisée pour séparer les extraits dans le résultat final.

    Returns:
        Une chaîne de texte formatée contenant les extraits les plus pertinents,
        chacun précédé de son titre et de sa source.
    """

    if not is_chroma_index_ready():
        raise RuntimeError("Index ChromaDB indisponible : (ré)indexation en cours.")

    client = get_chroma_client()
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        encode_kwargs={"normalize_embeddings": NORMALIZE_EMBEDDINGS},
    )

    # Extraction des Documents (format langchain.Schema.Documents)
    def search_collection(collection_name: str, top_k: int) -> list[Document]:

        try:
            collection = client.get_collection(collection_name)
            print(f"✅ Collection trouvée : {collection_name}")
        except Exception as e:
            msg = missing_collection_message(collection_name)
            print(f"❌ {msg}")
            raise ValueError(msg) from e

        vectorstore = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embedding_model,
        )

        try:
            return vectorstore.similarity_search(query=query, k=top_k)
        except Exception as e:
            emsg = str(e).lower()
            if any(key in emsg for key in ("dimension", "dimensions", "dimensionality", "shape", "embedding")):
                # Si c'est déjà l'InvalidArgumentError de Chroma, on la re-propage telle quelle
                try:
                    from chromadb.errors import InvalidArgumentError as ChromaInvalidArgumentError
                except Exception:
                    ChromaInvalidArgumentError = None
                if ChromaInvalidArgumentError and isinstance(e, ChromaInvalidArgumentError):
                    raise
                # Sinon on wrap en RuntimeError (accepté par le test)
                raise RuntimeError(EMBEDDING_MISMATCH_MESSAGE) from e
            raise

    # Recherche dans base_docx (prioritaire)
    results_docx = search_collection("base_docx", top_k_docx)
    print(f"🟧 Résultats pour 'base_docx' - {len(results_docx)} documents trouvés.")


    # Recherche dans base_web (secondaire)
    # on s'autorise à aller au delaà de la limte, on filtrera après
    results_web = search_collection("base_web", max(1, top_k_web * 3))
    print(f"🟧 Résultats pour 'base_web' - {len(results_web)} documents trouvés.")


    # Appel _format_results_with_ids(...)
    retrieved_chunks = _format_results_with_ids(
        results_docx,
        results_web,
        docx_limit=DOCX_TOPK,
        web_limit=WEB_TOPK,
        separator=separator,
        query=query,
        embedding_model=embedding_model,
        sim_threshold=SIM_THRESHOLD,
        nov_min=NOV_MIN,
        nov_max=NOV_MAX,
    )
    print("❇️ récap chunks injectés :",
          f"🟧 DOCX={retrieved_chunks.count('[DOCX')}, WEB={retrieved_chunks.count('[WEB')}",
          f"🟧 WEB_PERTINENCE={'[WEB_PERTINENCE]' in retrieved_chunks}")

    return retrieved_chunks



