# Fonctionnement du pipeline "src/func/run_full_indexing_pipeline.py" (07/07/2025)

## 1. Déclencheur initial : ajout d’un fichier .docx

Le pipeline de traitement est conçu pour détecter automatiquement les nouveaux fichiers .docx dans data/fiches_documentaires_docx/.

## 2. Lancement du pipeline global

Le fichier central est :

src/func/run_full_indexing_pipeline.py
Ce script :
- détecte les fichiers .docx ajoutés ou modifiés depuis la dernière indexation ;
- lance le pipeline de conversion + vectorisation uniquement sur ceux-là.
Il repose sur :

- detect_changes_and_get_modified_files()
- Il lit le journal indexed_files.json pour savoir quels fichiers ont déjà été traités (via leur hash).

### 2.1. Rôle de la fonction: src/func/indexed_health_related_files.py, notamment la fonction :
- 1. detect_changes_and_get_modified_files()
    - Objectif de cette fonction

        - Elle compare l’état actuel du répertoire contenant les fichiers .docx avec l’état enregistré dans indexed_files.json (via des hashs de fichiers).
    - Elle détecte donc :

        - un fichier .docx existant modifié (hash changé) ;
        - un nouveau fichier .docx jamais indexé auparavant (car il n’existe pas dans le journal).


### 2.2. Voici comment est détecté un nouveau fichier :

    - Étape 1 : liste des fichiers actuels
        - docx_files = glob.glob(os.path.join(docx_dir, "*.docx"))
    - Étape 2 : calcul du hash de chaque fichier actuel
        for file_path in docx_files:
            file_hash = compute_file_hash(file_path)
    - Étape 3 : comparaison avec le journal
        if file_path not in indexed_files or indexed_files[file_path] != file_hash:
            modified_files.append(file_path)

Ici, si file_path n’est pas présent du tout dans le indexed_files.json, alors le fichier est considéré comme "nouveau" et ajouté à la liste modified_files.

### 2.3. Conclusion

Le pipeline détecte bien les nouveaux fichiers .docx de manière implicite, car ils n’ont pas encore de hash enregistré dans indexed_files.json.

Il n’y a pas besoin d’un test explicite « si fichier nouveau », car l’absence de clé file_path dans le dictionnaire indexed_files est suffisante pour le déclencher.

## 3. Conversion du .docx en .json structuré

Fichier impliqué :

- src/func/convert_fiches_docx_to_json.py
- Fonctions principales :
    - convert_fiches_docx_to_json() : extrait les sections du document de manière semi-structurée ;
    - save_fiches_to_json() : sauvegarde les fiches dans data/to_json_fiches_documentaires/.


## 4. Indexation des contenus .json dans ChromaDB

Fichier :

- src/func/index_documents_chromadb.py
  - Fonction :
    - index_documents()
    - Elle transforme chaque fichier .json en documents à vecteurs (Document).
    - Elle injecte ces documents dans la collection base_docx de ChromaDB, dans le répertoire centralisé CHROMA_GLOBAL_DIR.


## 5. Utilisation par le chatbot (OBY-IA)

Une fois indexés :

Les contenus sont accessibles via retrieve_relevant_chunks().
    - Si l’intention utilisateur est de type generate_ppa ou generate_recommendations, alors :
        - la recherche sémantique dans la base ChromaDB est effectuée ;
        - les extraits pertinents sont insérés dans le prompt rag_llm_prompt_template_medical_plan() pour enrichir la génération de plan d’accompagnement (avec références de sources, si le prompt est bien paramétré).
    - Fichier journal mis à jour

Après indexation :
- data/indexation/indexed_files.json
- Ce fichier est mis à jour avec le hash du nouveau fichier .docx pour éviter de le retraiter inutilement à la prochaine exécution.




