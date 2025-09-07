"""
Liste des sites de référence autorisés pour l'extraction documentaire.

Ce module contient une variable `trusted_sites` définissant les sources web
considérées comme fiables pour l’extraction et l’indexation de recommandations
dans le cadre de l’application OBY-IA.

Chaque site est représenté par :
- un nom (ex. : "HAS"),
- une URL de base (`base_url`),
- une ou plusieurs pages de départ (`start_pages`) à crawler.

Cette liste est utilisée par les modules de scraping et d’indexation.
"""

trusted_sites = [
    {
        "name": "INCa",
        "base_url": "https://e-cancer.fr",
        "start_pages": [
            "https://e-cancer.fr/toute-l-information-sur-les-cancers/prevenir-les-risques-de-cancers/comment-prevenir-au-mieux-les-risques-de-cancers"
        ]
    },
    {
        "name": "Biomnis",
        "base_url": "https://eurofins-biomnis.com",
        "start_pages": [
            "https://eurofins-biomnis.com/specialites/"
        ]
    },
    {
    "name": "MedG",
    "base_url": "https://medg.fr",
    "start_pages": [
        #"https://www.medg.fr/arthrose/",
        "https://www.medg.fr/cataracte/",
        "https://www.medg.fr/chute-chez-la-personne-agee/",
        "https://www.medg.fr/degenerescence-maculaire-liee-a-lage/",
        "https://www.medg.fr/demence-a-corps-de-lewy/",
        "https://www.medg.fr/demence-vasculaire/",
        "https://www.medg.fr/denutrition-chez-la-personne-agee/",
        "https://www.medg.fr/maladie-dalzheimer/",
        "https://www.medg.fr/maladie-de-parkinson/",
        "https://www.medg.fr/menopause/",
        "https://www.medg.fr/osteoporose/",
        "https://www.medg.fr/syndrome-post-chute/",
        "https://www.medg.fr/items-r2c/ecni-68-troubles-psychiques-du-sujet-age/",
        "https://www.medg.fr/items-r2c/ecni-79-alteration-de-la-fonction-visuelle/",
        "https://www.medg.fr/items-r2c/ecni-106-confusion-demences/",
        "https://www.medg.fr/items-r2c/ecni-250-troubles-nutritionnels-chez-le-sujet-age/",
        "https://www.medg.fr/items-r2c/ecni-119-vieillissement-normal-aspects-biologiques-fonctionnels-et-relationnels-donnees-epidemiologiques-et-sociologiques-prevention-du-vieillissement-pathologique/",
        "https://www.medg.fr/items-r2c/ecni-120-menopause-et-andropause/",
        "https://www.medg.fr/items-r2c/ecni-124-osteopathies-fragilisantes/",
        "https://www.medg.fr/items-r2c/ecni-126-la-personne-agee-malade-particularites-semiologiques-psychologiques-et-therapeutiques/",
        "https://www.medg.fr/ecni-127-deficit-neurosensoriel-chez-le-sujet-age/",
        "https://www.medg.fr/items-r2c/ecni-128-troubles-de-la-marche-et-de-lequilibre/",
        "https://www.medg.fr/items-r2c/ecni-129-troubles-cognitifs-du-sujet-age/",
        "https://www.medg.fr/items-r2c/ecni-130-autonomie-et-dependance-chez-le-sujet-age/"
    ]
}
]
# trusted_sites = [
#     {
#         "name": "HAS",
#         "base_url": "https://www.has-sante.fr",
#         "start_pages": [
#             "https://www.has-sante.fr/jcms/c_2028194/fr/prendre-en-charge-une-personne-agee-polypathologique-en-soins-primaires"
#         ]
#     },
#     {
#         "name": "Personnes âgées",
#         "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
#         "start_pages": [
#             "https://www.pour-les-personnes-agees.gouv.fr",
#             "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/perte-d-autonomie-evaluation-et-droits/comment-fonctionne-la-grille-aggir"
#         ]
#     },
#     {
#         "name": "MSD Manuals",
#         "base_url": "https://www.msdmanuals.com",
#         "start_pages": [
#             "https://www.msdmanuals.com/fr/accueil/la-santé-des-personnes-âgées/dispenser-des-soins-aux-adultes-âgés/continuité-des-soins-pour-les-adultes-âgés"
#         ]
#     },
#     {
#         "name": "SFGG",
#         "base_url": "https://sfgg.org",
#         "start_pages": [
#             "https://sfgg.org/recommandations/",
#             "https://sfgg.org/?s=Démarche+clinique+du+sujet+âgé&scope=contents"
#             ]
#         },
#     {
#         "name": "SFCARDIO",
#         "base_url": "https://www.sfcardio.fr",
#         "start_pages": [
#             "https://www.sfcardio.fr/nos-publications/recommandations-esc",
#         ]
#     },
#     {
#         "name": "NEUROVASCULAIRE",
#         "base_url": "https://www.societe-francaise-neurovasculaire.fr",
#         "start_pages": [
#             "https://www.societe-francaise-neurovasculaire.fr/recommandations-eso",
#         ]
#     },
#
#     {
#         "name": "SPLF",
#         "base_url": "https://splf.fr",
#         "start_pages": [
#             "https://splf.fr/les-recommandations-splf/"
#         ]
#     },
#     {
#         "name": "SFNDT",
#         "base_url": "https://sfndt.org",
#         "start_pages": [
#             "https://sfndt.org/professionnels/recommandations-pour-la-pratique-clinique"
#         ]
#     },
#     {
#         "name": "SFMG",
#         "base_url": "https://sfmg.fr",
#         "start_pages": [
#             "https://sfmg.fr"
#         ]
#     },
#     {
#         "name": "INCa",
#         "base_url": "https://e-cancer.fr",
#         "start_pages": [
#             "https://e-cancer.fr/toute-l-information-sur-les-cancers/prevenir-les-risques-de-cancers/comment-prevenir-au-mieux-les-risques-de-cancers"
#         ]
#     },
#     {
#         "name": "SPILF",
#         "base_url": "https://infectiologie.com",
#         "start_pages": [
#             "https://infectiologie.com/fr/recommandations.html"
#         ]
#     },
#     {
#         "name": "Cerba",
#         "base_url": "https://lab-cerba.com",
#         "start_pages": [
#             "https://lab-cerba.com/fr/nos-expertises"
#         ]
#     },
#     {
#         "name": "Biomnis",
#         "base_url": "https://eurofins-biomnis.com",
#         "start_pages": [
#             "https://eurofins-biomnis.com/specialites/"
#         ]
#     },
#
#     {
#     "name": "MedG",
#     "base_url": "https://medg.fr",
#     "start_pages": [
#         "https://www.medg.fr/arthrose/",
#         "https://www.medg.fr/cataracte/",
#         "https://www.medg.fr/chute-chez-la-personne-agee/",
#         "https://www.medg.fr/degenerescence-maculaire-liee-a-lage/",
#         "https://www.medg.fr/demence-a-corps-de-lewy/",
#         "https://www.medg.fr/demence-vasculaire/",
#         "https://www.medg.fr/denutrition-chez-la-personne-agee/",
#         "https://www.medg.fr/maladie-dalzheimer/",
#         "https://www.medg.fr/maladie-de-parkinson/",
#         "https://www.medg.fr/menopause/",
#         "https://www.medg.fr/osteoporose/",
#         "https://www.medg.fr/syndrome-post-chute/",
#         "https://www.medg.fr/items-r2c/ecni-68-troubles-psychiques-du-sujet-age/",
#         "https://www.medg.fr/items-r2c/ecni-79-alteration-de-la-fonction-visuelle/",
#         "https://www.medg.fr/items-r2c/ecni-106-confusion-demences/",
#         "https://www.medg.fr/items-r2c/ecni-250-troubles-nutritionnels-chez-le-sujet-age/",
#         "https://www.medg.fr/items-r2c/ecni-119-vieillissement-normal-aspects-biologiques-fonctionnels-et-relationnels-donnees-epidemiologiques-et-sociologiques-prevention-du-vieillissement-pathologique/",
#         "https://www.medg.fr/items-r2c/ecni-120-menopause-et-andropause/",
#         "https://www.medg.fr/items-r2c/ecni-124-osteopathies-fragilisantes/",
#         "https://www.medg.fr/items-r2c/ecni-126-la-personne-agee-malade-particularites-semiologiques-psychologiques-et-therapeutiques/",
#         "https://www.medg.fr/ecni-127-deficit-neurosensoriel-chez-le-sujet-age/",
#         "https://www.medg.fr/items-r2c/ecni-128-troubles-de-la-marche-et-de-lequilibre/",
#         "https://www.medg.fr/items-r2c/ecni-129-troubles-cognitifs-du-sujet-age/",
#         "https://www.medg.fr/items-r2c/ecni-130-autonomie-et-dependance-chez-le-sujet-age/"
#     ]
# }
# ]

