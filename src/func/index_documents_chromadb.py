"""
Module d'indexation des documents de santé dans une base vectorielle ChromaDB.

Ce module prend en entrée des fichiers JSON représentant soit des documents issus de fichiers DOCX,
soit des pages web structurées, puis les segmente et les insère dans une collection ChromaDB.
"""



from uuid import uuid4
from datetime import datetime
import os, json
from chromadb import Client
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from src.utils.chroma_client import get_chroma_client

def index_documents(source_dir: str, source_type: str, client: Client):
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

    print("lancement fonction -> index_documents()... ")

    if source_type not in ("docx", "web"):
        raise ValueError("source_type doit être 'docx' ou 'web'.")

    collection_name = "base_docx" if source_type == "docx" else "base_web"

    # 🔹 Initialisation collection
    # client = get_chroma_client()
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)

    print(f"🔍 Indexation des documents depuis : {source_dir} (type: {source_type})")

    total_files, indexed_chunks = 0, 0

    for file in os.listdir(source_dir):
        if not file.endswith(".json"):
            continue
        print(f"📄 Traitement du fichier JSON : {file}")

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
                    print(f"⚠️ Texte vide pour le fichier {file}")
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
                    print(f"⚠️ Aucune section trouvée dans le fichier {file}")
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

