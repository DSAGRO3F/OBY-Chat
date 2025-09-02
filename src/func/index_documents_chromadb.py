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
from chromadb.utils import embedding_functions
from src.utils.chroma_client import get_chroma_client

from config.config import EMBEDDING_MODEL_NAME


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
            titre = fiche.get("titre", "Titre inconnu")
            type_document = fiche.get("type_document", "document")
            source = fiche.get("source_doc" if source_type == "docx" else "source_url", "Source inconnue")

            if source_type == "docx":
                # ✅ 1 seul chunk : texte complet
                chunk_text = fiche.get("texte_complet", "").strip()
                if not chunk_text:
                    print(f"⚠️ Texte vide pour le fichier {file}, source_type : {source_type}")
                    continue

                chunk_id = f"{file}_{uuid4().hex[:8]}"
                try:
                    collection.add(
                        documents=[chunk_text],
                        ids=[chunk_id],
                        metadatas=[{
                            "titre": titre,
                            "type_document": type_document,
                            "source": source,
                            "section_index": 0,
                            "source_type": source_type,
                            "date_indexation": datetime.now().strftime("%Y-%m-%d"),
                        }]
                    )
                    indexed_chunks += 1
                except Exception as e:
                    print(f"❌ Erreur d’ajout depuis {file} : {e}")


            elif source_type == "web":
                sections = fiche.get("sections", [])
                if not sections:
                    print(f"⚠️ Aucune section trouvée dans le fichier {file}, source_type : {source_type}")
                    continue

                for i, section in enumerate(sections):
                    chunk_text = section.get("texte", "").strip()
                    if not chunk_text:
                        print(f"⚠️ Chunk vide dans section {i} du fichier {file}")
                        continue

                    chunk_id = f"{file}_{uuid4().hex[:8]}"
                    try:
                        collection.add(
                            documents=[chunk_text],
                            ids=[chunk_id],
                            metadatas=[{
                                "titre": titre,
                                "type_document": type_document,
                                "source": source,
                                "section_index": i,
                                "source_type": source_type,
                                "date_indexation": datetime.now().strftime("%Y-%m-%d"),
                            }]
                        )
                        indexed_chunks += 1
                    except Exception as e:
                        print(f"❌ Erreur d'ajout d'une section depuis {file}, section {i} : {e}")


        total_files += 1

    print(f"✅ {indexed_chunks} sections indexées à partir de {total_files} fichiers.")

