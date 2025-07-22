"""
Module de récupération des extraits pertinents depuis une base ChromaDB.
Ce module interroge une collection vectorielle Chroma (via LangChain)
et retourne les passages les plus similaires à une requête, pour enrichir un prompt.
"""

def retrieve_relevant_chunks(
    query: str,
    top_k_docx: int = 5,
    top_k_web: int = 3,
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

    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings

    from langchain.schema import Document
    from src.func.index_documents_chromadb import get_chroma_client
    from config.config import CHROMA_GLOBAL_DIR

    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    client = get_chroma_client()

    def search_collection(collection_name: str, top_k: int) -> list[Document]:
        try:
            collection = client.get_collection(collection_name)
            print(f"✅ Collection trouvée : {collection_name}")
        except Exception:
            print(f"❌ Collection introuvable : {collection_name}")
            raise ValueError(f"Collection '{collection_name}' introuvable.")

        vectorstore = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=CHROMA_GLOBAL_DIR,
        )
        return vectorstore.similarity_search(query=query, k=top_k)

    # Recherche dans base_docx (prioritaire)
    results_docx = search_collection("base_docx", top_k_docx)
    print(f"🔍 Résultats pour 'base_docx' - {len(results_docx)} documents trouvés.")

    # Recherche dans base_web (secondaire)
    results_web = search_collection("base_web", top_k_web)
    print(f"🔍 Résultats pour 'base_web' - {len(results_web)} documents trouvés.")

    # Formatage pour injection dans le prompt
    def format_results(results: list[Document]) -> list[str]:
        formatted = []
        for doc in results:
            meta = doc.metadata
            titre = meta.get("titre", "Titre inconnu")
            source = meta.get("source", meta.get("source_url", "Source inconnue"))
            text = doc.page_content.strip()
            formatted.append(f"- Titre : {titre} (source : {source})\n{text}")
        return formatted

    all_formatted = format_results(results_docx) + format_results(results_web)
    return separator.join(all_formatted)



