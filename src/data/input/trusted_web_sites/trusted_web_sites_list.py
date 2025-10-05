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
    # {
    #   "name": "HAS – Personne âgée : Fragilité (repérage & ambulatoire)",
    #   "base_url": "https://www.has-sante.fr",
    #   "start_pages": [
    #     "https://www.has-sante.fr/jcms/c_1602972/fr/fiche-points-cles-et-solutions-comment-reperer-la-fragilite-en-soins-ambulatoire",
    #     "https://www.has-sante.fr/jcms/c_1602973/fr/note-methodologique-et-de-synthese-documentaire-reperer-la-fragilite-en-soins-ambulatoires",
        # "https://www.has-sante.fr/jcms/c_1718248/fr/comment-prendre-en-charge-les-personnes-agees-fragiles-en-ambulatoire",
        # "https://www.has-sante.fr/jcms/c_1718876/fr/fiche-points-cles-et-solutions-prendre-en-charge-les-personnes-agees-fragiles-en-ambulatoire",
        # "https://www.has-sante.fr/jcms/c_1718882/fr/note-methodologique-et-de-synthese-documentaire-prendre-en-charge-les-personnes-agees-fragiles-en-ambulatoire"
    #     ],
    #     "max_pages": 50
    # },
    # {
    #     "name": "HAS – Personne âgée : Repérage de la perte d’autonomie (volet domicile)",
    #     "base_url": "https://www.has-sante.fr",
    #     "start_pages": [
    #         "https://www.has-sante.fr/jcms/c_2835100/fr/reperage-des-risques-de-perte-d-autonomie-ou-de-son-aggravation-pour-les-personnes-agees-volet-domicile",
    #         "https://www.has-sante.fr/jcms/c_2835142/fr/l-outil-de-reperage-des-risques-de-perte-d-autonomie-ou-de-son-aggravation",
    #         "https://www.has-sante.fr/jcms/c_2835108/fr/anesm-rbpp-reperage-des-risques-personnes-agees-a5-bat-pdf-interactif",
    #         "https://www.has-sante.fr/jcms/c_2911284/fr/fiche-outil-reperage-perte-autonomie"
    #     ],
    #     "max_pages": 50
    # },
    # {
    #     "name": "HAS – Personne âgée : Prévention des chutes & capacités motrices",
    #     "base_url": "https://www.has-sante.fr",
    #     "start_pages": [
    #         "https://www.has-sante.fr/jcms/p_3506172/fr/synthese-aps-personnes-agees-a-risque-de-chute",
    #         "https://www.has-sante.fr/jcms/p_3506171/fr/synthese-maintien-des-capacites-motrices-des-personnes-agees-prescription-d-activite-physique",
    #         "https://www.has-sante.fr/jcms/c_269961/fr/prevention-des-chutes-synthese-des-recommandations-pdf",
    #         "https://www.has-sante.fr/jcms/c_793371/fr/evaluation-et-prise-en-charge-des-personnes-agees-faisant-des-chutes-repetees",
    #         "https://www.has-sante.fr/jcms/p_3222464/fr/pied-de-la-personne-agee-fiche-outil-n3-le-patient-a-risque-de-chutes",
    #         "https://www.has-sante.fr/jcms/c_2876862/fr/consultation-et-prescription-medicale-d-activite-physique-a-des-fins-de-sante"
    #     ],
    #     "max_pages": 50
    # },
    # {
    #     "name": "HAS – Personne âgée : Dénutrition (diagnostic & prise en charge 70+)",
    #     "base_url": "https://www.has-sante.fr",
    #     "start_pages": [
    #         "https://www.has-sante.fr/jcms/p_3297884/fr/diagnostic-de-la-denutrition-chez-la-personne-de-70-ans-et-plus-recommandations",
    #         "https://www.has-sante.fr/jcms/p_3165944/fr/diagnostic-de-la-denutrition-chez-la-personne-de-70-ans-et-plus",
    #         "https://www.has-sante.fr/jcms/p_3297885/fr/diagnostic-de-la-denutrition-chez-l-enfant-l-adulte-et-la-personne-de-70-ans-et-plus-fiche-outil",
    #         "https://www.has-sante.fr/jcms/r_1495743/fr/strategie-de-prise-en-charge-en-cas-de-denutrition-proteino-energetique-chez-la-personne-agee"
    #     ],
    #     "max_pages": 50
    # },
    # {
    #     "name": "HAS – Personne âgée : Médicaments & iatrogénie au domicile",
    #     "base_url": "https://www.has-sante.fr",
    #     "start_pages": [
    #         "https://www.has-sante.fr/jcms/p_3193089/fr/le-risque-medicamenteux-au-domicile",
    #         "https://www.has-sante.fr/jcms/p_3193115/fr/guide-le-risque-medicamenteux-au-domicile-mise-a-jour-juillet-2020",
    #         "https://www.has-sante.fr/jcms/c_1771468/fr/comment-ameliorer-la-qualite-et-la-securite-des-prescriptions-de-medicaments-chez-la-personne-agee",
    #         "https://www.has-sante.fr/jcms/c_1771482/fr/ameliorer-la-qualite-et-la-securite-des-prescriptions-de-medicaments-chez-la-personne-agee-fiche-points-cles",
    #         "https://www.has-sante.fr/jcms/c_946211/fr/outils-de-securisation-et-d-auto-evaluation-de-l-administration-des-medicaments",
    #         "https://www.has-sante.fr/jcms/c_2618396/fr/interruptions-de-tache-lors-de-l-administration-des-medicaments"
    #     ],
    #     "max_pages": 50
    # },
    # {
    #     "name": "HAS – Personne âgée : Fin de vie à domicile (soins palliatifs)",
    #     "base_url": "https://www.has-sante.fr",
    #     "start_pages": [
    #         "https://www.has-sante.fr/jcms/c_2833702/fr/accompagner-la-fin-de-vie-des-personnes-agees-a-domicile",
    #         "https://www.has-sante.fr/jcms/c_2833706/fr/web-synthese-findevie-domicile",
    #         "https://www.has-sante.fr/jcms/c_2833707/fr/web-rbpp-findevie-domicile",
    #         "https://www.has-sante.fr/jcms/p_3151123/fr/patient-en-fin-de-vie-hospitalise-ou-a-domicile-quels-medicaments-et-comment-les-utiliser",
    #         "https://www.has-sante.fr/jcms/c_2834390/fr/comment-mettre-en-oeuvre-une-sedation-profonde-et-continue-maintenue-jusqu-au-deces-guide-parcours-de-soins",
    #         "https://www.has-sante.fr/jcms/p_3151633/fr/sedation-profonde-jusqu-au-deces-une-decision-collegiale",
    #         "https://www.has-sante.fr/jcms/c_2655084/fr/fiche-points-cles-organisation-des-parcours-comment-favoriser-le-maintien-a-domicile-des-patients-adultes-relevant-de-soins-palliatifs"
    #     ],
    #     "max_pages": 50
    # },
    {
        "name": "Pour les personnes âgées – Prévention des chutes à domicile",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/preserver-son-autonomie-et-sa-sante/comment-prevenir-les-risques-de-chutes-chez-les-personnes-agees",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/preserver-son-autonomie-et-sa-sante/prevenir-les-chutes-des-conseils-en-video",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/preserver-son-autonomie-et-sa-sante/prevenir-les-chutes"
        ],
        "max_pages": 50
    },
    {
        "name": "Pour les personnes âgées – Dénutrition & alimentation (prévenir la perte d’autonomie)",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/preserver-son-autonomie-et-sa-sante/denutrition-des-personnes-agees-la-reperer-et-la-prevenir",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/preserver-son-autonomie-et-sa-sante/denutrition-comment-veiller-a-une-bonne-alimentation",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/preserver-son-autonomie-et-sa-sante/les-consequences-de-la-denutrition-pour-les-personnes-agees"
        ],
        "max_pages": 50
    },
    {
        "name": "Pour les personnes âgées – Aménager le logement & aides techniques",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/amenager-son-logement-et-s-equiper",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/amenager-son-logement-et-s-equiper/des-equipements-pour-faciliter-son-quotidien",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/amenager-son-logement-et-s-equiper/amenager-son-logement",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/amenager-son-logement-et-s-equiper/ou-trouver-des-informations-et-des-conseils-sur-les-aides-techniques",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/amenager-son-logement-et-s-equiper/les-aides-financieres-pour-adapter-son-logement",
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/amenager-son-logement-et-s-equiper/choisir-un-professionnel-pour-amenager-son-logement"
        ],
        "max_pages": 50
    },
    {
        "name": "Pour les personnes âgées – Aides & soins à domicile (services autonomie, SSIAD, SPASAD)",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/beneficier-d-aide-a-domicile/les-services-d-aide-a-domicile",
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/beneficier-de-soins-a-domicile/les-ssiad-services-de-soins-infirmiers-a-domicile",
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/beneficier-de-soins-a-domicile"
        ],
        "max_pages": 50
    },
    {
        "name": "Pour les personnes âgées – Hospitalisation à domicile (HAD)",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/beneficier-de-soins-a-domicile/l-had-hospitalisation-a-domicile"
        ],
        "max_pages": 50
    },
    {
        "name": "Pour les personnes âgées – Organiser la sortie d’hospitalisation / retour à domicile",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/etre-hospitalise/comment-organiser-sa-sortie-d-hospitalisation",
            "https://www.pour-les-personnes-agees.gouv.fr/annuaires-et-services/fiches-pratiques/fiche-pratique-sortie-d-hospitalisation-a-qui-s-adresser-en-cas-de-perte-d-autonomie",
            "https://www.pour-les-personnes-agees.gouv.fr/annuaires-et-services/fiches-pratiques/fiches-pratiques-sortie-d-hospitalisation",
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/etre-hospitalise/etre-hospitalise-ce-qu-il-faut-savoir",
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/etre-hospitalise"
        ],
        "max_pages": 50
    },
    {
        "name": "Pour les personnes âgées – Téléassistance (sécuriser le domicile)",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/beneficier-d-aide-a-domicile/la-teleassistance",
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/aides-financieres/les-aides-financieres-pour-installer-une-teleassistance",
            "https://www.pour-les-personnes-agees.gouv.fr/annuaires-et-services/facile-a-lire-et-a-comprendre/la-teleassistance-comment-ca-marche"
        ],
        "max_pages": 50
    },
    {
        "name": "Pour les personnes âgées – Prévenir la déshydratation & vagues de chaleur",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/preserver-son-autonomie/preserver-son-autonomie-et-sa-sante/deshydratation-conseils-de-prevention-en-prevision-des-fortes-chaleurs",
            "https://www.pour-les-personnes-agees.gouv.fr/actualites/conseils-et-gestes-simples-a-adopter-pour-se-proteger-des-fortes-chaleurs"
        ],
        "max_pages": 50
    },
    {
        "name": "Pour les personnes âgées – Aides financières à domicile (APA & démarches)",
        "base_url": "https://www.pour-les-personnes-agees.gouv.fr",
        "start_pages": [
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/aides-financieres/l-apa-a-domicile",
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/beneficier-d-aide-a-domicile",
            "https://www.pour-les-personnes-agees.gouv.fr/vivre-a-domicile/beneficier-d-aide-a-domicile/j-ai-besoin-d-etre-aide-a-domicile-comment-faire"
        ],
        "max_pages": 50
    },
    # {
    #   "name": "MSD Manuals – Soins à domicile & organisation du maintien",
    #   "base_url": "https://www.msdmanuals.com",
    #   "start_pages": [
    #     "https://www.msdmanuals.com/fr/professional/gériatrie/soins-aux-personnes-âgées/soins-à-domicile",
    #     "https://www.msdmanuals.com/fr/professional/gériatrie/soins-aux-personnes-âgées/soins-de-répit",
    #     "https://www.msdmanuals.com/fr/professional/gériatrie/problèmes-sociaux-chez-les-personnes-âgées/soins-dispensés-par-la-famille-aux-personnes-âgées",
    #     "https://www.msdmanuals.com/fr/professional/gériatrie/problèmes-sociaux-chez-les-personnes-âgées/personnes-âgées-vivant-seules",
    #     "https://www.msdmanuals.com/fr/professional/gériatrie/problèmes-sociaux-chez-les-personnes-âgées/auto-négligence-chez-les-personnes-âgées",
    #     "https://www.msdmanuals.com/fr/professional/gériatrie/prise-en-charge-du-patient-gériatrique/évaluation-gériatrique-standardisée",
    #     "https://www.msdmanuals.com/fr/professional/gériatrie/soins-aux-personnes-âgées/revue-générale-des-soins-gériatriques"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #     "name": "MSD Manuals – Prévention des chutes & blessures à domicile",
    #     "base_url": "https://www.msdmanuals.com",
    #     "start_pages": [
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/chutes-chez-les-personnes-âgées/chutes-chez-les-personnes-âgées",
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/prévention-des-maladies-et-du-handicap-chez-la-personne-âgée/prévention-des-blessures-chez-les-personnes-âgées",
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/prise-en-charge-du-patient-gériatrique/anamnèse-chez-les-personnes-âgées",  # inclut la check-list de sécurité du domicile
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/troubles-de-la-marche-chez-les-personnes-âgées/troubles-de-la-marche-chez-les-personnes-âgées",
    #         "https://www.msdmanuals.com/fr/professional/troubles-cardiovasculaires/symptômes-des-maladies-cardiovasculaires/hypotension-orthostatique"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #     "name": "MSD Manuals – Médicaments & iatrogénie (ambulatoire)",
    #     "base_url": "https://www.msdmanuals.com",
    #     "start_pages": [
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/traitement-pharmacologique-chez-les-personnes-âgées/problèmes-liés-aux-médicaments-chez-les-personnes-âgées",
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/traitement-pharmacologique-chez-les-personnes-âgées/pharmacocinétique-chez-les-personnes-âgées",
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/traitement-pharmacologique-chez-les-personnes-âgées/pharmacodynamie-chez-les-sujets-âgés",
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/traitement-pharmacologique-chez-les-personnes-âgées/catégories-de-médicaments-qui-méritent-une-vigilance-chez-le-patient-âgé",
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/prévention-des-maladies-et-du-handicap-chez-la-personne-âgée/prévention-des-complications-iatrogènes-chez-les-personnes-âgées"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #     "name": "MSD Manuals – Dépistage fonctionnel & nutrition (domicile)",
    #     "base_url": "https://www.msdmanuals.com",
    #     "start_pages": [
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/prise-en-charge-du-patient-gériatrique/anamnèse-chez-les-personnes-âgées",      # inclut repérage nutrition/chutes
    #         "https://www.msdmanuals.com/fr/professional/gériatrie/prise-en-charge-du-patient-gériatrique/revue-générale-de-l-évaluation-des-personnes-âgées",
    #         "https://www.msdmanuals.com/fr/professional/sujets-spéciaux/symptômes-non-spécifiques/perte-de-poids-involontaire",
    #         "https://www.msdmanuals.com/fr/professional/troubles-gastro-intestinaux/troubles-œsophagiens-et-de-la-déglutition/dysphagie"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #     "name": "MSD Manuals – Troubles fréquents impactant le maintien à domicile",
    #     "base_url": "https://www.msdmanuals.com",
    #     "start_pages": [
    #         "https://www.msdmanuals.com/fr/professional/troubles-génito-urinaires/troubles-de-la-miction/incontinence-urinaire-chez-l-adulte",
    #         "https://www.msdmanuals.com/fr/professional/troubles-neurologiques/syndrome-confusionnel-et-démence/confusion",  # prévention/prise en charge du delirium
    #         "https://www.msdmanuals.com/fr/professional/troubles-neurologiques/symptômes-des-troubles-neurologiques/faiblesse-musculaire"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #   "name": "SFGG – Recommandations",
    #   "base_url": "https://sfgg.org",
    #   "start_pages": [
    #     "https://sfgg.org/recommandations/",
    #     "https://sfgg.org/recommandations/anti-grippe-le-vaccin-haute-dose-efluelda/",
    #     "https://sfgg.org/recommandations/canicule-les-bons-reflexes-a-adopter-pour-les-personnes-agees-ehpad-et-domicile/",
    #     "https://sfgg.org/recommandations/confusion-aigue-chez-la-personne-agee/",
    #     "https://sfgg.org/recommandations/degenerescence-maculaire-liee-a-lage/",
    #     "https://sfgg.org/recommandations/denutrition-chez-la-personne-agee/",
    #     "https://sfgg.org/recommandations/depression-chez-la-personne-agee/",
    #     "https://sfgg.org/recommandations/maladie-alzheimer/",
    #     "https://sfgg.org/recommandations/maladie-de-parkinson/",
    #     "https://sfgg.org/recommandations/notre-dossier-le-vieillissement-chez-la-femme/",
    #     "https://sfgg.org/recommandations/parcours-des-personnes-agees-ayant-des-troubles-cognitifs/",
    #     "https://sfgg.org/recommandations/prevention-des-chutes-accidentelles-chez-la-personne-agee/",
    #     "https://sfgg.org/recommandations/prevention-et-prise-en-charge-des-effets-indesirables-pouvant-survenir-apres-une-ponction-lombaire/",
    #     "https://sfgg.org/recommandations/prise-en-charge-des-personnes-agees-atteintes-de-diabete-de-type-2/",
    #     "https://sfgg.org/recommandations/services-daide-et-de-soins-a-domicile-accompagnement-des-personnes-atteintes-de-maladie-neurodegenerative/",
    #     "https://sfgg.org/recommandations/24483-2/",
    #     "https://sfgg.org/recommandations/reperage-plus-precoce-de-la-dmla/"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #   "name": "SFC – Documents professionnels (accès libre)",
    #   "base_url": "https://www.sfcardio.fr",
    #   "start_pages": [
    #     "https://www.sfcardio.fr/nos-publications/documents-professionnels/",
    #     "https://www.sfcardio.fr/publication/echocardiographie-deffort/",
    #     "https://www.sfcardio.fr/publication/echocardiographie-de-perfusion-sous-dobutamine/",
    #     "https://www.sfcardio.fr/publication/echocardiographie-transoesophagienne-anesthesie-generale/",
    #     "https://www.sfcardio.fr/publication/echocardiographie-transoesophagienne-anesthesie-locale/",
    #     "https://www.sfcardio.fr/publication/fermeture-percutanee-de-foramen-ovale-permeable-fop/"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #     "name": "SFC – Documents de consensus (accès libre)",
    #     "base_url": "https://www.sfcardio.fr",
    #     "start_pages": [
    #         "https://www.sfcardio.fr/nos-publications/documents-de-consensus/",
    #         "https://www.sfcardio.fr/publication/cardiac-rehabilitation-recommendations-2023-update/",
    #         "https://www.sfcardio.fr/publication/appareils-de-mesure-de-la-pression-arterielle-sans-brassard-cuffless-et-methode-de-validation/",
    #         "https://www.sfcardio.fr/publication/disponibilite-des-tritherapies-fixes-dantihypertenseurs-pour-contribuer-a-un-meilleur-controle-tensionnel-des-hypertendus-prise-de-position-de-la-societe-francaise-dhypertension-ar/"
    #       ],
    #     "max_pages": 20
    # },
    # {
    #   "name": "SFNV – Recommandations ESO (accès public)",
    #   "base_url": "https://www.societe-francaise-neurovasculaire.fr",
    #   "start_pages": [
    #     "https://www.societe-francaise-neurovasculaire.fr/recommandations-eso",
    #     "https://www.societe-francaise-neurovasculaire.fr/_files/ugd/c1feba_b43a23c398584f2ba444d45b11e481d0.pdf"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #   "name": "SPLF – Recommandations (accès libre)",
    #   "base_url": "https://splf.fr",
    #   "start_pages": [
    #     "https://splf.fr/les-recommandations-splf/",
    #     "https://splf.fr/actualisation-des-recommandations-de-prise-en-charge-des-pneumonies-aigues-communautaires-chez-ladulte/",
    #     "https://docs.splf.fr/divers/docs-gen/recos/actualisation-PAC2025.pdf"
    #     ],
    #     "max_pages": 20
    # },
    # {
    #   "name": "INCa – cancer.fr : types de cancers",
    #   "base_url": "https://www.cancer.fr",
    #   "start_pages": [
    #     "https://www.cancer.fr/personnes-malades/les-cancers/col-de-l-uterus",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/colon",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/tumeurs-du-cerveau",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/endometre",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/estomac",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/foie",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/leucemie-lymphoide-chronique",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/lymphome-hodgkinien",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/lymphome-non-hodgkinien",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/melanome-de-la-peau",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/myelome-multiple",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/aesophage",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/oto-rhino-laryngee-orl",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/ovaire",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/cancers-pediatriques",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/pancreas",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/poumon",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/prostate",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/rectum",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/rein",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/sein",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/testicule",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/thyroide",
    #     "https://www.cancer.fr/personnes-malades/les-cancers/vessie"
    #       ],
    #     "max_pages": 20
    # },
    # {
    #   "name": "SPILF – Recommandations (accès public)",
    #   "base_url": "https://www.infectiologie.com",
    #   "start_pages": [
    #     "https://www.infectiologie.com/fr/recommandations-1.html",
    #     "https://www.infectiologie.com/fr/recommandations-spilf.html",
    #     "https://www.infectiologie.com/UserFiles/File/spilf/recos/duree-traitement-pac-29-nov.pdf",
    #     "https://www.infectiologie.com/UserFiles/File/spilf/recos/reco-perf-continue-2025.pdf",
    #     "https://www.infectiologie.com/UserFiles/File/spilf/recos/saisine-dgs-atb-critique-9-fev-22-v3.pdf"
    #     ],
    #     "max_pages": 20
    # },
# {
#     "name": "Lab Cerba – Catalogue d’examens",
#     "base_url": "https://www.lab-cerba.com",
#     "start_pages": [f"https://www.lab-cerba.com/fr/catalogue?exams_page={i}" for i in range(1, 271)],
#     "max_pages": 2800, # au niveau du site
#     "max_depth": 1,
#     "allow_path_regex": r"^/fr/examen/",
#     "deny_query_regex": r"(^|&)exams_page=",
# },
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
#         ],
#         "max_pages": 20
#     },
#     {
#     "name": "RecoMedicales – Addictologie",
#     "base_url": "https://recomedicales.fr",
#     "start_pages": [
#         "https://recomedicales.fr/recommandations/arret-tabac/",
#         "https://recomedicales.fr/recommandations/sevrage-alcool/",
#         "https://recomedicales.fr/recommandations/substituts-nicotiniques/"
#     ],
#     "max_pages": 20
#
#     },
#     {
#     "name": "RecoMedicales – Allergologie",
#     "base_url": "https://recomedicales.fr",
#     "start_pages": [
#         "https://recomedicales.fr/recommandations/allergies-croisees/",
#         "https://recomedicales.fr/recommandations/asthme/",
#         "https://recomedicales.fr/recommandations/dermatite-atopique/",
#         "https://recomedicales.fr/recommandations/intolerance-lactose/",
#         "https://recomedicales.fr/recommandations/rhinite-allergique/",
#         "https://recomedicales.fr/recommandations/urticaire/"
#         ],
#         "max_pages": 20
#     },
#     {
#     "name": "RecoMedicales – Biologie",
#     "base_url": "https://recomedicales.fr",
#     "start_pages": [
#         "https://recomedicales.fr/recommandations/anomalies-tp-tca/",
#         "https://recomedicales.fr/recommandations/augmentation-gamma-gt/",
#         "https://recomedicales.fr/recommandations/hypereosinophilie/",
#         "https://recomedicales.fr/recommandations/hypercalcemie/",
#         "https://recomedicales.fr/recommandations/hyperferritinemie/",
#         "https://recomedicales.fr/recommandations/hypocalcemie/",
#         "https://recomedicales.fr/recommandations/hyponatremie/",
#         "https://recomedicales.fr/recommandations/cibles-biologiques/"
#           ],
#         "max_pages": 20
#     },
#     {
#     "name": "RecoMedicales – Cardiologie",
#     "base_url": "https://recomedicales.fr",
#     "start_pages": [
#         "https://recomedicales.fr/recommandations/anevrysme-aorte-abdominale/",
#         "https://recomedicales.fr/recommandations/avk/",
#         "https://recomedicales.fr/recommandations/arteriopathie-obliterante-membres-inferieurs/",
#         "https://recomedicales.fr/recommandations/automesure-tensionnelle/",
#         "https://recomedicales.fr/recommandations/electrocardiogramme/",
#         "https://recomedicales.fr/recommandations/embolie-pulmonaire/",
#         "https://recomedicales.fr/recommandations/endocardite/",
#         "https://recomedicales.fr/recommandations/epreuve-effort/",
#         "https://recomedicales.fr/recommandations/fibrillation-atriale/",
#         "https://recomedicales.fr/recommandations/hypercholesterolemie-familiale/",
#         "https://recomedicales.fr/recommandations/hypertension-arterielle/",
#         "https://recomedicales.fr/recommandations/hypertension-arterielle-maligne/",
#         "https://recomedicales.fr/recommandations/hypertension-arterielle-pulmonaire/",
#         "https://recomedicales.fr/recommandations/hypotension-orthostatique/",
#         "https://recomedicales.fr/recommandations/insuffisance-cardiaque-aigue/",
#         "https://recomedicales.fr/recommandations/insuffisance-cardiaque-chronique/",
#         "https://recomedicales.fr/recommandations/pericardite-aigue/",
#         "https://recomedicales.fr/recommandations/statines/",
#         "https://recomedicales.fr/recommandations/syndrome-coronarien-aigu/",
#         "https://recomedicales.fr/recommandations/syndrome-coronarien-chronique/",
#         "https://recomedicales.fr/recommandations/tensiometres-electroniques-valides/",
#         "https://recomedicales.fr/recommandations/thrombose-veineuse-profonde/",
#         "https://recomedicales.fr/recommandations/thrombose-veineuse-superficielle/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Endocrinologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/acromegalie/",
#         "https://recomedicales.fr/recommandations/andropause-deficit-testosterone/",
#         "https://recomedicales.fr/recommandations/apports-calcium/",
#         "https://recomedicales.fr/recommandations/carence-vitamine-b12/",
#         "https://recomedicales.fr/recommandations/denutrition/",
#         "https://recomedicales.fr/recommandations/diabete-type-1/",
#         "https://recomedicales.fr/recommandations/diabete-type-2/",
#         "https://recomedicales.fr/recommandations/diabete-gestationnel/",
#         "https://recomedicales.fr/recommandations/hirsutisme/",
#         "https://recomedicales.fr/recommandations/hypercalcemie/",
#         "https://recomedicales.fr/recommandations/hyperthyroidie/",
#         "https://recomedicales.fr/recommandations/hypocalcemie/",
#         "https://recomedicales.fr/recommandations/hypothyroidie/",
#         "https://recomedicales.fr/recommandations/hypothyroidie-fruste/",
#         "https://recomedicales.fr/recommandations/nodule-thyroidien/",
#         "https://recomedicales.fr/recommandations/obesite-adulte/",
#         "https://recomedicales.fr/recommandations/regime-vegetarien-vegetalien/",
#         "https://recomedicales.fr/recommandations/syndrome-cushing/",
#         "https://recomedicales.fr/recommandations/syndrome-ovaires-polykystiques-sopk/",
#         "https://recomedicales.fr/recommandations/vitamine-d/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Hématologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/amylose-al/",
#         "https://recomedicales.fr/recommandations/anemie/",
#         "https://recomedicales.fr/recommandations/anomalies-tp-tca/",
#         "https://recomedicales.fr/recommandations/asplenie/",
#         "https://recomedicales.fr/recommandations/deficit-g6pd/",
#         "https://recomedicales.fr/recommandations/electrophorese-proteines-seriques/",
#         "https://recomedicales.fr/recommandations/hypereosinophilie/",
#         "https://recomedicales.fr/recommandations/leucemie-aigue-adulte/",
#         "https://recomedicales.fr/recommandations/leucemie-lymphoide-chronique/",
#         "https://recomedicales.fr/recommandations/lymphomes-non-hodgkiniens/",
#         "https://recomedicales.fr/recommandations/lymphopenie/",
#         "https://recomedicales.fr/recommandations/neutropenie/",
#         "https://recomedicales.fr/recommandations/gammapathie-monoclonale-mgus/",
#         "https://recomedicales.fr/recommandations/polyglobulie/",
#         "https://recomedicales.fr/recommandations/splenomegalie/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Hépato-gastro-entérologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/appendicite-aigue/",
#         "https://recomedicales.fr/recommandations/augmentation-gamma-gt/",
#         "https://recomedicales.fr/recommandations/cancer-colorectal/",
#         "https://recomedicales.fr/recommandations/cancer-estomac/",
#         "https://recomedicales.fr/recommandations/cancer-pancreas/",
#         "https://recomedicales.fr/recommandations/carcinome-hepatocellulaire/",
#         "https://recomedicales.fr/recommandations/cholangite-biliaire-primitive/",
#         "https://recomedicales.fr/recommandations/cholangite-sclerosante-primitive/",
#         "https://recomedicales.fr/recommandations/cholecystite-aigue/",
#         "https://recomedicales.fr/recommandations/coloscopie/",
#         "https://recomedicales.fr/recommandations/constipation/",
#         "https://recomedicales.fr/recommandations/diarrhee-chronique/",
#         "https://recomedicales.fr/recommandations/diverticulite-sigmoidienne/",
#         "https://recomedicales.fr/recommandations/dyspepsie/",
#         "https://recomedicales.fr/recommandations/dysphagie/",
#         "https://recomedicales.fr/recommandations/fissure-anale/",
#         "https://recomedicales.fr/recommandations/helicobacter-pylori/",
#         "https://recomedicales.fr/recommandations/hemangiome-hepatique/",
#         "https://recomedicales.fr/recommandations/hemochromatose/",
#         "https://recomedicales.fr/recommandations/hemorroides/",
#         "https://recomedicales.fr/recommandations/hepatite-a/",
#         "https://recomedicales.fr/recommandations/hepatite-autoimmune/",
#         "https://recomedicales.fr/recommandations/hepatite-b/",
#         "https://recomedicales.fr/recommandations/hepatite-c/",
#         "https://recomedicales.fr/recommandations/hernie-parietale/",
#         "https://recomedicales.fr/recommandations/hyperferritinemie/",
#         "https://recomedicales.fr/recommandations/hyperplasie-nodulaire-focale/",
#         "https://recomedicales.fr/recommandations/ictere/",
#         "https://recomedicales.fr/recommandations/incontinence-fecale/",
#         "https://recomedicales.fr/recommandations/infections-claustridium-difficile/",
#         "https://recomedicales.fr/recommandations/intolerance-lactose/",
#         "https://recomedicales.fr/recommandations/kyste-pilonidal/",
#         "https://recomedicales.fr/recommandations/maladie-coeliaque/",
#         "https://recomedicales.fr/recommandations/maladie-wilson/",
#         "https://recomedicales.fr/recommandations/oxyurose/",
#         "https://recomedicales.fr/recommandations/pancreatite-aigue/",
#         "https://recomedicales.fr/recommandations/pancreatite-chronique/",
#         "https://recomedicales.fr/recommandations/reflux-gastro-oesophagien/",
#         "https://recomedicales.fr/recommandations/regime-fodmaps/",
#         "https://recomedicales.fr/recommandations/regime-sans-residus/",
#         "https://recomedicales.fr/recommandations/steatose-hepatique-et-nash/",
#         "https://recomedicales.fr/recommandations/syndrome-intestin-irritable/",
#         "https://recomedicales.fr/recommandations/tenia/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Infectiologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/asplenie/",
#         "https://recomedicales.fr/recommandations/chikungunya/",
#         "https://recomedicales.fr/recommandations/coqueluche/",
#         "https://recomedicales.fr/recommandations/covid-19/",
#         "https://recomedicales.fr/recommandations/erysipele/",
#         "https://recomedicales.fr/recommandations/fievre-nourrisson/",
#         "https://recomedicales.fr/recommandations/fievre-jaune/",
#         "https://recomedicales.fr/recommandations/grippe/",
#         "https://recomedicales.fr/recommandations/hsh/",
#         "https://recomedicales.fr/recommandations/vih-sida/",
#         "https://recomedicales.fr/recommandations/infections-herpes-virus/",
#         "https://recomedicales.fr/recommandations/infection-urinaire-cystite-pyelonephrite/",
#         "https://recomedicales.fr/recommandations/maladie-lyme/",
#         "https://recomedicales.fr/recommandations/maladie-griffes-chat/",
#         "https://recomedicales.fr/recommandations/megalerythme-epidemique-parvovirus/",
#         "https://recomedicales.fr/recommandations/meningite/",
#         "https://recomedicales.fr/recommandations/hygiene-conservation-aliments/",
#         "https://recomedicales.fr/recommandations/mononucleose-infectieuse/",
#         "https://recomedicales.fr/recommandations/morsure/",
#         "https://recomedicales.fr/recommandations/mpox/",
#         "https://recomedicales.fr/recommandations/mycoses-dermatophytes-candidoses/",
#         "https://recomedicales.fr/recommandations/oxyurose/",
#         "https://recomedicales.fr/recommandations/paludisme/",
#         "https://recomedicales.fr/recommandations/panaris/",
#         "https://recomedicales.fr/recommandations/pediculoses/",
#         "https://recomedicales.fr/recommandations/prophylaxie-preexposition-prep/",
#         "https://recomedicales.fr/recommandations/rougeole/",
#         "https://recomedicales.fr/recommandations/strongyloidose-anguillulose/",
#         "https://recomedicales.fr/recommandations/syphilis/",
#         "https://recomedicales.fr/recommandations/tenia/",
#         "https://recomedicales.fr/recommandations/tuberculose/",
#         "https://recomedicales.fr/recommandations/vaccination/",
#         "https://recomedicales.fr/recommandations/voyage/",
#         "https://recomedicales.fr/recommandations/zona/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Médecine du sommeil",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/duree-sommeil-recommandee/",
#         "https://recomedicales.fr/recommandations/narcolepsie/",
#         "https://recomedicales.fr/recommandations/syndrome-apnees-obstructives-sommeil/",
#         "https://recomedicales.fr/recommandations/syndrome-jambes-sans-repos/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Neurologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/accident-vasculaire-cerebral/",
#         "https://recomedicales.fr/recommandations/algie-vasculaire-face/",
#         "https://recomedicales.fr/recommandations/canal-lombaire-etroit/",
#         "https://recomedicales.fr/recommandations/douleur-neuropathique/",
#         "https://recomedicales.fr/recommandations/maladie-alzheimer/",
#         "https://recomedicales.fr/recommandations/maladie-parkinson/",
#         "https://recomedicales.fr/recommandations/meningite/",
#         "https://recomedicales.fr/recommandations/migraine/",
#         "https://recomedicales.fr/recommandations/nevralgie-pudendale/",
#         "https://recomedicales.fr/recommandations/nevralgie-trigeminale-classique/",
#         "https://recomedicales.fr/recommandations/paralysie-faciale-idiopathique/",
#         "https://recomedicales.fr/recommandations/syndrome-jambes-sans-repos/",
#         "https://recomedicales.fr/recommandations/syndrome-canal-carpien/",
#         "https://recomedicales.fr/recommandations/traumatisme-cranien-enfant/",
#         "https://recomedicales.fr/recommandations/tremblement-essentiel/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Néphrologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/hematurie/",
#         "https://recomedicales.fr/recommandations/hypercalcemie/",
#         "https://recomedicales.fr/recommandations/hypocalcemie/",
#         "https://recomedicales.fr/recommandations/hyponatremie/",
#         "https://recomedicales.fr/recommandations/insuffisance-renale-aigue/",
#         "https://recomedicales.fr/recommandations/insuffisance-renale-chronique/",
#         "https://recomedicales.fr/recommandations/polykystose-renale/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Ophtalmologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/bilan-orthoptique/",
#         "https://recomedicales.fr/recommandations/cataracte/",
#         "https://recomedicales.fr/recommandations/chalazion/",
#         "https://recomedicales.fr/recommandations/degenerescence-maculaire-age-dmla/",
#         "https://recomedicales.fr/recommandations/glaucome/",
#         "https://recomedicales.fr/recommandations/orgelet/",
#         "https://recomedicales.fr/recommandations/urgences-ophtalmologiques/",
#         "https://recomedicales.fr/recommandations/zona/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – ORL",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/angine/",
#         "https://recomedicales.fr/recommandations/bouchon-cerumen/",
#         "https://recomedicales.fr/recommandations/cancer-thyroide/",
#         "https://recomedicales.fr/recommandations/coqueluche/",
#         "https://recomedicales.fr/recommandations/dysphonie/",
#         "https://recomedicales.fr/recommandations/laryngite-aigue/",
#         "https://recomedicales.fr/recommandations/maladie-meniere/",
#         "https://recomedicales.fr/recommandations/otite-externe/",
#         "https://recomedicales.fr/recommandations/otite-moyenne-aigue/",
#         "https://recomedicales.fr/recommandations/paralysie-faciale-idiopathique/",
#         "https://recomedicales.fr/recommandations/presbyacousie/",
#         "https://recomedicales.fr/recommandations/rhinite-allergique/",
#         "https://recomedicales.fr/recommandations/sinusite-chronique/",
#         "https://recomedicales.fr/recommandations/sinusite/",
#         "https://recomedicales.fr/recommandations/vertiges-positionnels-vppb/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Orthopédie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/coxarthrose/",
#         "https://recomedicales.fr/recommandations/genu-varum-valgum/",
#         "https://recomedicales.fr/recommandations/entorse-cheville/",
#         "https://recomedicales.fr/recommandations/fracture-extremite-superieure-femur/",
#         "https://recomedicales.fr/recommandations/inegalite-longueur-membres-inferieurs/",
#         "https://recomedicales.fr/recommandations/maladie-osgood-schlatter/",
#         "https://recomedicales.fr/recommandations/maladie-dupuytren/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Pneumologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/arret-tabac/",
#         "https://recomedicales.fr/recommandations/asthme/",
#         "https://recomedicales.fr/recommandations/bronchopneumopathie-chronique-obstructive/",
#         "https://recomedicales.fr/recommandations/cancer-poumon/",
#         "https://recomedicales.fr/recommandations/covid-19/",
#         "https://recomedicales.fr/recommandations/corticoides-inhales/",
#         "https://recomedicales.fr/recommandations/grippe/",
#         "https://recomedicales.fr/recommandations/pneumonie-aigue-communautaire/",
#         "https://recomedicales.fr/recommandations/toux-chronique/",
#         "https://recomedicales.fr/recommandations/tuberculose/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Psychiatrie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/benzodiazepines/",
#         "https://recomedicales.fr/recommandations/boulimie-hyperphagie/",
#         "https://recomedicales.fr/recommandations/depression/",
#         "https://recomedicales.fr/recommandations/parasomnies/",
#         "https://recomedicales.fr/recommandations/remboursement-psychologue-monsoutienpsy/",
#         "https://recomedicales.fr/recommandations/schizophrenie/",
#         "https://recomedicales.fr/recommandations/trouble-anxieux-generalise/",
#         "https://recomedicales.fr/recommandations/trouble-bipolaire/",
#         "https://recomedicales.fr/recommandations/trouble-deficit-attention-tdah/",
#         "https://recomedicales.fr/recommandations/trouble-obsessionnel-compulsif-toc/",
#         "https://recomedicales.fr/recommandations/trouble-oppositionnel-provocation-top/",
#         "https://recomedicales.fr/recommandations/trouble-panique/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Pédiatrie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/allergie-proteines-lait-vache/",
#         "https://recomedicales.fr/recommandations/angine/",
#         "https://recomedicales.fr/recommandations/antalgie-enfant/",
#         "https://recomedicales.fr/recommandations/apports-calcium/",
#         "https://recomedicales.fr/recommandations/bronchiolite/",
#         "https://recomedicales.fr/recommandations/cryptorchidie/",
#         "https://recomedicales.fr/recommandations/genu-varum-valgum/",
#         "https://recomedicales.fr/recommandations/diarrhee-aigue-nourrisson/",
#         "https://recomedicales.fr/recommandations/duree-sommeil-recommandee/",
#         "https://recomedicales.fr/recommandations/enuresie-primaire/",
#         "https://recomedicales.fr/recommandations/erytheme-fessier-nourrisson/",
#         "https://recomedicales.fr/recommandations/examens-suivi-nourrisson/",
#         "https://recomedicales.fr/recommandations/enfant-ecrans/",
#         "https://recomedicales.fr/recommandations/fievre-nourrisson/",
#         "https://recomedicales.fr/recommandations/inegalite-longueur-membres-inferieurs/",
#         "https://recomedicales.fr/recommandations/infection-urinaire-enfant/",
#         "https://recomedicales.fr/recommandations/laryngite-aigue/",
#         "https://recomedicales.fr/recommandations/maladie-kawasaki/",
#         "https://recomedicales.fr/recommandations/megalerythme-epidemique-parvovirus/",
#         "https://recomedicales.fr/recommandations/mononucleose-infectieuse/",
#         "https://recomedicales.fr/recommandations/otite-moyenne-aigue/",
#         "https://recomedicales.fr/recommandations/oxyurose/",
#         "https://recomedicales.fr/recommandations/phimosis/",
#         "https://recomedicales.fr/recommandations/plagiocephalie/",
#         "https://recomedicales.fr/recommandations/remboursement-psychologue-monsoutienpsy/",
#         "https://recomedicales.fr/recommandations/puberte-precoce/",
#         "https://recomedicales.fr/recommandations/rougeole/",
#         "https://recomedicales.fr/recommandations/saturnisme/",
#         "https://recomedicales.fr/recommandations/prevention-carie-fluor/",
#         "https://recomedicales.fr/recommandations/soins-cordon-ombilical/",
#         "https://recomedicales.fr/recommandations/traumatisme-cranien-enfant/",
#         "https://recomedicales.fr/recommandations/trouble-deficit-attention-tdah/",
#         "https://recomedicales.fr/recommandations/vaccination/",
#         "https://recomedicales.fr/recommandations/varicelle/",
#         "https://recomedicales.fr/recommandations/verrues/",
#         "https://recomedicales.fr/recommandations/vitamine-d/",
#         "https://recomedicales.fr/recommandations/vitamine-k/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Rhumatologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/arterite-cellules-geantes-horton/",
#         "https://recomedicales.fr/recommandations/bursite/",
#         "https://recomedicales.fr/recommandations/electrophorese-proteines-seriques/",
#         "https://recomedicales.fr/recommandations/enthesopathie-calcanenne/",
#         "https://recomedicales.fr/recommandations/fibromyalgie/",
#         "https://recomedicales.fr/recommandations/gonarthrose/",
#         "https://recomedicales.fr/recommandations/goutte/",
#         "https://recomedicales.fr/recommandations/lombalgie-commune/",
#         "https://recomedicales.fr/recommandations/nevrome-morton/",
#         "https://recomedicales.fr/recommandations/osteoporose-masculine/",
#         "https://recomedicales.fr/recommandations/osteoporose/",
#         "https://recomedicales.fr/recommandations/phenomene-raynaud/",
#         "https://recomedicales.fr/recommandations/polyarthrite-rhumatoide/",
#         "https://recomedicales.fr/recommandations/rhumatisme-pyrophosphate-chondrocalcinose/",
#         "https://recomedicales.fr/recommandations/scoliose/",
#         "https://recomedicales.fr/recommandations/spondylarthrite-ankylosante/",
#         "https://recomedicales.fr/recommandations/syndrome-canal-carpien/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Social",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/aides-sociales/",
#         "https://recomedicales.fr/recommandations/allocation-personnalisee-autonomie/",
#         "https://recomedicales.fr/recommandations/remboursement-soins-etranger/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Thérapeutique",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/avk/",
#         "https://recomedicales.fr/recommandations/benzodiazepines/",
#         "https://recomedicales.fr/recommandations/contraception/",
#         "https://recomedicales.fr/recommandations/contraception-urgence/",
#         "https://recomedicales.fr/recommandations/corticoides-inhales/",
#         "https://recomedicales.fr/recommandations/corticoides/",
#         "https://recomedicales.fr/recommandations/dermocorticoides/",
#         "https://recomedicales.fr/recommandations/medicaments-ecrasables/",
#         "https://recomedicales.fr/recommandations/methotrexate/",
#         "https://recomedicales.fr/recommandations/medicaments-prise-repas/",
#         "https://recomedicales.fr/recommandations/monographies-medicaments/",
#         "https://recomedicales.fr/recommandations/perfusions-domicile/",
#         "https://recomedicales.fr/recommandations/remboursement-psychologue-monsoutienpsy/",
#         "https://recomedicales.fr/recommandations/prophylaxie-preexposition-prep/",
#         "https://recomedicales.fr/recommandations/regime-sans-residus/",
#         "https://recomedicales.fr/recommandations/statines/",
#         "https://recomedicales.fr/recommandations/vaccination/",
#         "https://recomedicales.fr/recommandations/vitamine-d/",
#         "https://recomedicales.fr/recommandations/vitamine-k/"
#           ],
#         "max_pages": 20
#     },
#     {
#       "name": "RecoMedicales – Urologie",
#       "base_url": "https://recomedicales.fr",
#       "start_pages": [
#         "https://recomedicales.fr/recommandations/andropause-deficit-testosterone/",
#         "https://recomedicales.fr/recommandations/cancer-prostate/",
#         "https://recomedicales.fr/recommandations/cancer-vessie/",
#         "https://recomedicales.fr/recommandations/cancer-rein/",
#         "https://recomedicales.fr/recommandations/cancer-testicule/",
#         "https://recomedicales.fr/recommandations/contraception/",
#         "https://recomedicales.fr/recommandations/cryptorchidie/",
#         "https://recomedicales.fr/recommandations/dysfonction-erectile/",
#         "https://recomedicales.fr/recommandations/ejaculation-prematuree/",
#         "https://recomedicales.fr/recommandations/enuresie-primaire/",
#         "https://recomedicales.fr/recommandations/hematurie/",
#         "https://recomedicales.fr/recommandations/hypertrophie-benigne-prostate/",
#         "https://recomedicales.fr/recommandations/incontinence-urinaire-femme/",
#         "https://recomedicales.fr/recommandations/infections-herpes-virus/",
#         "https://recomedicales.fr/recommandations/infection-genitale-uretrite-orchiepididymite/",
#         "https://recomedicales.fr/recommandations/infection-urinaire-cystite-pyelonephrite/",
#         "https://recomedicales.fr/recommandations/infection-urinaire-enfant/",
#         "https://recomedicales.fr/recommandations/infertilite-couple/",
#         "https://recomedicales.fr/recommandations/phimosis/"
#           ],
#         "max_pages": 20
#     },
#     {
#         "name": "SFNDT – Recommandations pour la pratique clinique",
#         "base_url": "https://www.sfndt.org",
#         "start_pages": [
#             "https://www.sfndt.org/professionnels/recommandations-pour-la-pratique-clinique",
#             "https://www.sfndt.org/professionnels/recommandations-pour-la-pratique-clinique?page=2",
#             "https://www.sfndt.org/professionnels/recommandations-pour-la-pratique-clinique?page=3",
#             "https://www.sfndt.org/professionnels/recommandations-pour-la-pratique-clinique?page=4",
#         ],
#         "max_pages": 50
#     },

]

