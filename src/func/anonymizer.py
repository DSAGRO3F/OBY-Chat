# src/func/anonymize_usager_persona.py
"""
Anonymisation de l'usager via persona française (session-aléatoire).

Ce module fournit :
- Des pools de valeurs françaises (prénoms, noms, voies, codes postaux/communes).
- La création d'une persona cohérente pour l'usager (prénom selon le genre, nom, adresse, CP/commune).
- Des utilitaires pour lire/écrire dans un dictionnaire JSON par chemins imbriqués.
- Une anonymisation ciblée des champs usager que vous avez listés.
- La construction d'un mapping {valeur_anonymisée: valeur_originale} pour la désanonymisation.

Entrée : dict JSON (document patient).
Sortie : Tuple[Any, Dict[str, str]] -> (document anonymisé, mapping).
"""

from __future__ import annotations
import secrets
import datetime as dt
import math
import bisect
import random
from typing import Any, Dict, List, Tuple, Sequence, TypeVar, Optional
T = TypeVar("T")




"""Section: POOLS FR (≥ 20 valeurs chacun)
Contient des listes de prénoms français (masculins & féminins),
de noms de famille, de noms de voies, et des couples (code postal, commune).
Ces pools servent de base à la génération aléatoire sécurisée (session-based).
"""

# --------- POOLS FR (≥ 20 valeurs chacun) ---------
FIRST_NAMES_M: List[str] = [
    "Jean","Pierre","Michel","Alain","Bernard","André","Jacques","Louis","Philippe","François",
    "Daniel","Christian","René","Claude","Gérard","Paul","Marcel","Raymond","Roger","Henri"
]
FIRST_NAMES_F: List[str] = [
    "Marie","Jeanne","Monique","Françoise","Nicole","Catherine","Madeleine","Sylvie","Martine","Anne",
    "Hélène","Danielle","Colette","Jacqueline","Suzanne","Michèle","Yvette","Yvonne","Nathalie","Chantal"
]
LAST_NAMES: List[str] = [
    "Martin","Bernard","Dubois","Thomas","Robert","Richard","Petit","Durand","Leroy","Moreau",
    "Laurent","Simon","Michel","Garcia","David","Bertrand","Roux","Vincent","Fournier","Morel"
]
# 20 noms de voie FR usuels
STREET_NAMES: List[str] = [
    "rue de la Paix","avenue Victor Hugo","boulevard Saint-Michel","rue des Écoles","rue de la République",
    "avenue de Verdun","rue Nationale","rue de la Gare","rue du Moulin","rue du Château",
    "rue Pasteur","rue Jules Ferry","rue des Lilas","rue Victor Hugo","rue de l'Église",
    "avenue de la Liberté","rue de la Mairie","rue des Acacias","rue du Stade","rue des Fleurs"
]
# Couples (CP, Commune) FR plausibles (20)
POSTCODES_COMMUNES: List[Tuple[str, str]] = [
    ("75001","Paris"),("13001","Marseille"),("69001","Lyon"),("31000","Toulouse"),("44000","Nantes"),
    ("33000","Bordeaux"),("59000","Lille"),("67000","Strasbourg"),("34000","Montpellier"),("35000","Rennes"),
    ("21000","Dijon"),("06000","Nice"),("72000","Le Mans"),("49000","Angers"),("86000","Poitiers"),
    ("37000","Tours"),("02000","Laon"),("02100","Saint-Quentin"),("80000","Amiens"),("51100","Reims")
]

NON_INFORMATIF = {"", "non renseigné", "null"}


def _normalize_case(s: str) -> str:
    """
    Normalise la casse d’une chaîne de caractères.

    Convertit la valeur en minuscules et supprime les espaces superflus
    en début et fin de chaîne. Cela permet de comparer les chaînes de
    manière insensible à la casse.

    Args:
        value (str): La chaîne de caractères à normaliser.

    Returns:
        str: La chaîne transformée en minuscules et sans espaces inutiles.

    Exemple:
        >>> _normalize_case("Bonjour ")
        'bonjour'    """
    return s.strip().casefold()


def _is_non_informatif(s: Any) -> bool:
    """
   Vérifie si une valeur est considérée comme non informative.

    Une valeur est jugée non informative si elle correspond à l’un des
    mots-clés prédéfinis (par exemple : "non renseigné", "inconnu", "null").
    La comparaison est insensible à la casse.

    Args:
        value (str): La chaîne de caractères à vérifier.

    Returns:
        bool: True si la valeur est non informative, False sinon.

    Exemple:
        >>> _is_non_informatif("Non renseigné")
        True
    """
    return isinstance(s, str) and _normalize_case(s) in NON_INFORMATIF


"""Section: PERSONA USAGER
Fonctions permettant de sélectionner des valeurs aléatoires sécurisées
et de construire une persona cohérente (prénom, nom, adresse, CP/commune)
pour l'usager, avec un aléa non déterministe entre exécutions.
"""


def pick(options: Sequence[T], debug: bool = False) -> T:
    """
    Sélectionne un élément aléatoire dans une séquence donnée.

    Cette fonction choisit un élément au hasard parmi ceux de la séquence
    passée en argument, en utilisant un générateur aléatoire
    cryptographiquement sûr (`secrets.choice`).

    Args:
        options (Sequence[T]): La séquence d’éléments parmi lesquels choisir.
        debug (bool, optionnel): Si True, affiche en console la valeur choisie
            pour faciliter le débogage. Par défaut False.

    Returns:
        T: L’élément choisi aléatoirement dans la séquence.

    Exemple:
        >>> pick(["Alice", "Bob", "Charlie"])
        'Bob'
    """
    choice = secrets.choice(options)
    if debug:
        print(f"[DEBUG] Picked value: {choice}")
    return choice


# I.a =======Construction date de naissance fictive pour l'usager et les contacts de l'usager==============#


_sysrand = random.SystemRandom()

def _gaussian_age_weights(mu: int = 83, sigma: float = 6.5, lo: int = 60, hi: int = 100) -> tuple[list[int], list[float]]:
    """
    Calcule les poids d’une loi normale tronquée pour des âges entiers.

    Génère une distribution discrète d’âges (entiers) comprise entre `lo` et `hi`,
    centrée sur `mu` avec un écart-type `sigma`. Retourne également la CDF
    (somme cumulée) pour faire un échantillonnage inverse.

    Args:
        mu (int): Moyenne ciblée de l’âge (par défaut 83).
        sigma (float): Écart-type (par défaut 6.5).
        lo (int): Âge minimum (inclus).
        hi (int): Âge maximum (inclus).

    Returns:
        tuple[list[int], list[float]]: (liste des âges, CDF correspondante).
    """
    ages = list(range(lo, hi + 1))
    w = [math.exp(-0.5 * ((a - mu) / sigma) ** 2) for a in ages]
    s = sum(w)
    w = [x / s for x in w]
    cdf = []
    acc = 0.0
    for x in w:
        acc += x
        cdf.append(acc)
    cdf[-1] = 1.0
    return ages, cdf

_AGES, _CDF = _gaussian_age_weights()


def _sample_age() -> int:
    """
    Retourne un âge généré aléatoirement à des fins d’anonymisation.

    L’âge est tiré dans une plage réaliste pour les patients du jeu de données.
    Cette fonction est principalement utilisée lors de l’anonymisation ou du
    remplacement d’informations sensibles de date de naissance par un âge
    approximatif.

    Returns:
        int: Un entier pseudo-aléatoire représentant un âge.
    """


    u = _sysrand.random()
    i = bisect.bisect_left(_CDF, u)
    return _AGES[min(max(i, 0), len(_AGES) - 1)]

def _sample_dob_from_age(age: int, today: dt.date | None = None) -> dt.date:
    """
        Génère une date de naissance pseudo-aléatoire à partir d’un âge donné.

        La fonction calcule une année de naissance approximative à partir de l’âge
        fourni puis attribue aléatoirement un mois et un jour. Elle est utilisée
        pour l’anonymisation lorsqu’on ne conserve que l’âge et qu’une date de
        naissance synthétique mais réaliste est nécessaire.

        Args:
            age (int): L’âge de la personne.

        Returns:
            str: Une date de naissance synthétique au format ISO (YYYY-MM-DD).
        """

    if today is None:
        today = dt.date.today()
    year = today.year - age
    month = _sysrand.randint(1, 12)
    day = _sysrand.randint(1, 28)
    return dt.date(year, month, day)



def _anonymize_usager_dob_full(doc: dict, path: list[str], mapping: dict[str, str], debug: bool = False) -> None:
    """
        Anonymise la date de naissance complète de la section 'usager'
        dans un document patient.

        Cette fonction remplace la date de naissance originale par une
        date synthétique générée à partir d’un âge pseudo-aléatoire.
        Le dictionnaire de correspondance entre valeurs originales et
        anonymisées est mis à jour pour permettre une désanonymisation
        ultérieure.

        Args:
            usager (Dict[str, Any]): Le dictionnaire contenant les informations du patient.
            mapping (Dict[str, str]): Le dictionnaire stockant les correspondances d’anonymisation.
            debug (bool, optionnel): Si True, affiche des messages de débogage. Par défaut False.

        Returns:
            Dict[str, Any]: Le dictionnaire 'usager' mis à jour avec la date de naissance anonymisée.
    """

    original = _get_at_path(doc, path, debug=debug)
    if debug:
        print(f"[DEBUG] DOB original at {path}: {original!r}")

    age = _sample_age()
    dob = _sample_dob_from_age(age)
    anon_value = dob.isoformat()

    if debug:
        print(f"[DEBUG] DOB full -> {anon_value!r} (âge simulé ≈ {age})")

    _replace_and_map(doc, path, anon_value, mapping, debug=debug)



# I.b =======Construction date de naissance fictive pour un contact de l'usager=========



def _anonymize_contact_dob_full(
    doc: Dict[str, Any],
    path: List[str],
    mapping: Dict[str, str],
    debug: bool = False
) -> None:
    """
    Remplace la date de naissance du contact par une date fictive.

    Utilise la distribution d’âges (gaussienne tronquée 60–100, μ≈83, σ≈6.5),
    puis construit une date ISO (YYYY-MM-DD) avec jour 1–28 et mois 1–12.

    Args:
        doc (Dict[str, Any]): Document JSON complet (modifié sur place).
        path (List[str]): Chemin du champ date de naissance du contact.
        mapping (Dict[str, str]): Mapping {valeur_anon: valeur_originale}.
        debug (bool, optionnel): Active les traces de débogage.
    """
    original = _get_at_path(doc, path, debug=debug)
    if debug:
        print(f"[DEBUG] Contact DOB original at {path}: {original!r}")

    age = _sample_age()
    dob = _sample_dob_from_age(age).isoformat()
    if debug:
        print(f"[DEBUG] Contact DOB full -> {dob!r} (âge simulé ≈ {age})")

    _replace_and_map(doc, path, dob, mapping, debug=debug)



# II.a =======Construction d'un persona fictif pour l'usager==============#


def build_usager_persona(gender: str | None = None, debug: bool = False) -> Dict[str, Any]:
    """
    Construit une identité fictive (« persona ») pour l’usager.

    Génère des informations cohérentes pour les champs à anonymiser
    (nom, prénom, adresse, code postal, commune). Le choix des prénoms
    tient compte du sexe si celui-ci est précisé.

    Args:
        gender (str | None, optionnel): Sexe détecté de l’usager
            ("Masculin" ou "Féminin"). Si None, le sexe est choisi au hasard.
        debug (bool, optionnel): Si True, affiche les valeurs choisies.
            Par défaut False.

    Returns:
        Dict[str, Any]: Dictionnaire contenant les champs anonymisés
        (nom, prénom, adresse, etc.).
    """

    try:
        if gender:
            gender = _normalize_case(gender)
    except Exception as e:
        if debug:
            print(f"❌ Le sexe de l'usager n'est pas renseigné -> A renseigner ! : {e}")
            gender = None

    if gender == "masculin":
        first = pick(FIRST_NAMES_M, debug=debug)
    elif gender == "féminin":
        first = pick(FIRST_NAMES_F, debug=debug)
    else:
        first = pick(FIRST_NAMES_M + FIRST_NAMES_F, debug=debug)
    last = pick(LAST_NAMES, debug=debug)

    # Adresse simple: numéro 1..199 + nom de voie
    number = secrets.randbelow(199) + 1
    street = pick(STREET_NAMES, debug=debug)
    addr_line = f"{number} {street}"

    cp, commune = pick(POSTCODES_COMMUNES, debug=debug)

    # Commentaire d'accès générique (pas d'infos sensibles)
    commentaire = "Accès : interphone"

    # Identifiant client neutre (facultatif)
    client_id = f"CLT-{secrets.token_hex(4).upper()}"

    persona = {
        "first_name": first,
        "last_name": last,
        "address_line": addr_line,   # pour usager.adresse.ligne[0]
        "postcode": cp,
        "commune": commune,
        "commentaire": commentaire,
        "client_id": client_id,
    }
    if debug:
        print(f"[DEBUG] build_usager_persona(gender={gender}) -> {persona}")
    return persona


"""Section: OUTILS D’ANONYMISATION & MAPPING
Utilitaires pour accéder/modifier des valeurs dans un dict JSON par chemins,
et pour effectuer les remplacements en maintenant un mapping.
"""



# II.b =======Construction d'un persona fictif pour les contacts de l'usager==============#


# Données de contacts qu'in décide de ne pas anonymiser (pas de données sensibles)
CONTACTS_STATIC_KEEP = {
    "typeContact",
    "titre",
    "role",
    "natureLien",
    "personneConfiance",
    "responsableLegal",
}


# Détection du genre du contact
def detect_genre_contact(contact: Dict[str, Any]) -> Optional[str]:
    """
    Détecte le genre d’un contact à partir de sa civilité.

    Essaie d’interpréter `contact['personnePhysique']['civilite']`
    (ex. « M. », « Monsieur », « Mme », « Madame ») pour retourner
    « Masculin » ou « Féminin ». Si indéterminé, renvoie None.

    Args:
        contact (Dict[str, Any]): Dictionnaire du contact.

    Returns:
        Optional[str]: « Masculin », « Féminin » ou None.
    """
    try:
        civ = contact.get("personnePhysique", {}).get("civilite")
        if isinstance(civ, str):
            s = civ.strip().casefold()
            # on tolère « m. », « monsieur », etc.
            if s.startswith("m") and not s.startswith("mme"):
                return "Masculin"
            if s.startswith("mme") or s.startswith("madame"):
                return "Féminin"
    except Exception:
        pass
    return None


# Construction d'un persona pour un contact de l'usager
def build_contact_persona(gender: Optional[str] = None, debug: bool = False) -> Dict[str, Any]:
    """
    Construit une persona française pour un contact.

    Génère un prénom (selon le genre si connu), un nom, et une date
    de naissance fictive cohérente avec la distribution d’âges
    (gaussienne tronquée 60–100, moyenne ~83).

    Args:
        gender (Optional[str]): « Masculin », « Féminin » ou None.
        debug (bool, optionnel): Si True, affiche les valeurs choisies.

    Returns:
        Dict[str, Any]: Dictionnaire de persona pour le contact.
    """
    if gender == "Masculin":
        first = pick(FIRST_NAMES_M, debug=debug)
        civilite = "M."
    elif gender == "Féminin":
        first = pick(FIRST_NAMES_F, debug=debug)
        civilite = "Mme"
    else:
        first = pick(FIRST_NAMES_M + FIRST_NAMES_F, debug=debug)
        # civilité neutre par défaut ; tu peux la laisser originale si tu préfères ne pas la anonymiser
        civilite = pick(["M.", "Mme"], debug=debug)

    last = pick(LAST_NAMES, debug=debug)

    age = _sample_age()
    dob = _sample_dob_from_age(age).isoformat()

    persona = {
        "civilite": civilite,
        "first_name": first,
        "last_name": last,
        "dob": dob,
    }
    if debug:
        print(f"[DEBUG] build_contact_persona(gender={gender}) -> {persona}")
    return persona


# Construire les chemins des données à anonymiser dans un dictionnaire pour un contact
def _contact_paths(index: int) -> Dict[str, List[str]]:
    """
    Construit les chemins (paths) à anonymiser pour un contact donné.

    Les listes étant indexées, on génère les chemins pour l’index `index`.

    Args:
        index (int): Index du contact dans `doc['contacts']`.

    Returns:
        Dict[str, List[str]]: Dictionnaire {clé_logique: path_list}.
    """
    return {
        # champs à anonymiser
        "civilite": ["contacts", f"[{index}]", "personnePhysique", "civilite"],
        "nomUtilise": ["contacts", f"[{index}]", "personnePhysique", "nomUtilise"],
        "prenomUtilise": ["contacts", f"[{index}]", "personnePhysique", "prenomUtilise"],
        "dateNaissance": ["contacts", f"[{index}]", "personnePhysique", "dateNaissance"],

        # champs conservés : présents ici uniquement si tu veux (par ex. pour lecture),
        # mais on NE les remplace PAS lors de l’anonymisation.
        "typeContact": ["contacts", f"[{index}]", "typeContact"],
        "titre": ["contacts", f"[{index}]", "titre"],
        "role": ["contacts", f"[{index}]", "role"],
        "natureLien": ["contacts", f"[{index}]", "natureLien"],
        "personneConfiance": ["contacts", f"[{index}]", "personneConfiance"],
        "responsableLegal": ["contacts", f"[{index}]", "responsableLegal"],
    }



# =======Construction des dictionnaires==============#



def _ensure_path_dict(d: Dict[str, Any], path: List[str]) -> Dict[str, Any] | None:
    """
    Crée récursivement les clés manquantes dans un dictionnaire pour un chemin donné.

    Si certaines clés du chemin n’existent pas, elles sont initialisées
    avec des dictionnaires vides jusqu’à atteindre la profondeur souhaitée.

    Args:
        d (Dict[str, Any]): Le dictionnaire racine.
        path (List[str]): Liste des clés représentant le chemin à créer.

    Returns:
        Dict[str, Any]: Le dictionnaire correspondant à la dernière clé du chemin.

    Exemple:
        >>> data = {}
        >>> _ensure_path_dict(data, ["usager", "adresse"])
        {}
        >>> data
        {'usager': {'adresse': {}}}
    """

    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur if isinstance(cur, dict) else None


def _get_at_path(d: Dict[str, Any], path: List[str], debug: bool = False) -> Any:
    """
    Récupère la valeur d’un dictionnaire en suivant un chemin de clés.

    Args:
        d (Dict[str, Any]): Le dictionnaire dans lequel chercher.
        path (List[str]): Liste des clés successives menant à la valeur.

    Returns:
        Any: La valeur trouvée ou None si une clé du chemin n’existe pas.

    Exemple:
        >>> data = {"usager": {"nom": "Durand"}}
        >>> _get_at_path(data, ["usager", "nom"])
        'Durand'
    """

    cur: Any = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        elif isinstance(cur, list):
            try:
                idx = int(p.strip("[]"))
                cur = cur[idx]
            except Exception:
                if debug:
                    print(f"[DEBUG] _get_at_path: invalid list index at segment '{p}' for path={path}")
                return None
        else:
            if debug:
                print(f"[DEBUG] _get_at_path: path not found at segment '{p}' for path={path}")
            return None
    if debug:
        print(f"[DEBUG] _get_at_path({path}) -> {cur!r}")
    return cur


def _set_at_path(d: Dict[str, Any], path: List[str], new_value: Any, debug: bool = False) -> bool:
    """
    Définit une valeur dans un dictionnaire en suivant un chemin de clés.

    Si certaines clés du chemin n’existent pas, elles sont créées.

    Args:
        d (Dict[str, Any]): Le dictionnaire dans lequel écrire.
        path (List[str]): Liste des clés successives menant à la valeur.
        value (Any): La valeur à affecter.

    Exemple:
        >>> data = {}
        >>> _set_at_path(data, ["usager", "nom"], "Martin")
        >>> data
        {'usager': {'nom': 'Martin'}}
    """

    if not path:
        if debug:
            print("[DEBUG] _set_at_path: empty path")
        return False
    cur: Any = d
    for i, p in enumerate(path):
        is_last = (i == len(path) - 1)
        if isinstance(cur, dict):
            if is_last:
                cur[p] = new_value
                if debug:
                    print(f"[DEBUG] _set_at_path: set {path} = {new_value!r}")
                return True
            if p not in cur:
                if debug:
                    print(f"[DEBUG] _set_at_path: missing key '{p}' in path={path}")
                return False
            cur = cur[p]
        elif isinstance(cur, list):
            try:
                idx = int(p.strip("[]"))
            except Exception:
                if debug:
                    print(f"[DEBUG] _set_at_path: invalid list index token '{p}' in path={path}")
                return False
            if idx < 0 or idx >= len(cur):
                if debug:
                    print(f"[DEBUG] _set_at_path: list index out of range [{idx}] in path={path}")
                return False
            if is_last:
                cur[idx] = new_value
                if debug:
                    print(f"[DEBUG] _set_at_path: set {path} = {new_value!r}")
                return True
            cur = cur[idx]
        else:
            if debug:
                print(f"[DEBUG] _set_at_path: non-container encountered at '{p}' for path={path}")
            return False
    return False


# =======Construction du mapping; correspondance entre valeurs originelles et valeurs fictives==============#



def _replace_and_map(
    doc: Dict[str, Any],
    path: List[str],
    anon_value: Any,
    mapping: Dict[str, str],
    debug: bool = False
) -> None:
    """
    Remplace une valeur dans un dictionnaire et met à jour le mapping anonymisation.

    La valeur originale est enregistrée dans `mapping` pour conserver une trace
    de l’anonymisation effectuée.

    Args:
        d (Dict[str, Any]): Le dictionnaire à modifier.
        path (List[str]): Liste des clés menant à la valeur à remplacer.
        new_value (Any): La valeur anonymisée qui remplace l’ancienne.
        mapping (Dict[str, str]): Dictionnaire de correspondance
            {valeur_anonymisée: valeur_originale}.
        debug (bool, optionnel): Si True, affiche les valeurs remplacées.
            Par défaut False.

    Exemple:
        >>> data = {"usager": {"nom": "Durand"}}
        >>> mapping = {}
        >>> _replace_and_map(data, ["usager", "nom"], "Martin", mapping)
        >>> data
        {'usager': {'nom': 'Martin'}}
        >>> mapping
        {'Martin': 'Durand'}
    """

    original = _get_at_path(doc, path, debug=debug)
    if original is None:
        if debug:
            print(f"[DEBUG] _replace_and_map: path not found, skip -> {path}")
        return

    if isinstance(original, str) and _is_non_informatif(original):
        if debug:
            print(f"[DEBUG] _replace_and_map: non-informative at {path}, replacing without mapping "
                  f"({original!r} -> {anon_value!r})")
        _set_at_path(doc, path, anon_value, debug=debug)
        return

    if isinstance(original, (str, int, float, bool)):
        if debug:
            print(f"[DEBUG] _replace_and_map: mapping {path} -> {original!r} => {anon_value!r}")
        _set_at_path(doc, path, anon_value, debug=debug)
        mapping[str(anon_value)] = str(original)
    else:
        if debug:
            print(f"[DEBUG] _replace_and_map: complex structure at {path}, replacing without mapping")
        _set_at_path(doc, path, anon_value, debug=debug)


"""Section: ANONYMISATION USAGER (champs listés)
Déclare les chemins à anonymiser pour l'usager et expose la fonction
principale `anonymize_usager_fields` qui applique la persona et construit le mapping.
"""

# --------- ANONYMISATION USAGER (champs listés) ---------
USAGER_PATHS = {
    # état civil
    "clientId": ["usager","Informations d'état civil","clientId"],
    "nomFamille": ["usager","Informations d'état civil","personnePhysique","nomFamille"],
    "prenomsActeNaissance": ["usager","Informations d'état civil","personnePhysique","prenomsActeNaissance"],
    "premierPrenomActeNaissance": ["usager","Informations d'état civil","personnePhysique","premierPrenomActeNaissance"],
    "nomUtilise": ["usager","Informations d'état civil","personnePhysique","nomUtilise"],
    "prenomUtilise": ["usager","Informations d'état civil","personnePhysique","prenomUtilise"],
    "dateNaissance": ["usager", "Informations d'état civil", "personnePhysique", "dateNaissance"],
    "situationFamiliale": ["usager","Informations d'état civil","personnePhysique","situationFamiliale"],

    # adresse
    "adresse_ligne0": ["usager","adresse","ligne","[0]"],   # list index 0
    "adresse_codePostal": ["usager","adresse","codePostal"],
    "adresse_libelleCommune": ["usager","adresse","libelleCommune"],
    "adresse_commentaire": ["usager","adresse","commentaire"],
}



# =======Détection genre de l'usager pour choix du prénom==============#



def detect_genre_usager(usager_dict: Dict[str, Any]) -> str | None:
    """
    Détecte le sexe de l’usager à partir de la structure JSON.

    La fonction tente de lire la clé :
        usager['Informations d'état civil']['personnePhysique']['sexe']
    puis interprète sa valeur de manière robuste et insensible à la casse
    (et aux accents) pour retourner « Masculin » ou « Féminin ».
    Si la valeur est absente ou non conforme, la fonction renvoie None.

    Args:
        usager_dict (Dict[str, Any]): Le sous-dictionnaire représentant la
            section « usager » du document JSON.

    Returns:
        str | None: « Masculin », « Féminin » ou None si indéterminé.

    Exemple:
        >>> usager = {
        ...     "Informations d'état civil": {
        ...         "personnePhysique": {"sexe": "féminin"}
        ...     }
        ... }
        >>> detect_genre_usager(usager)
        'Féminin'
    """

    try:
        sexe = usager_dict["Informations d'état civil"]["personnePhysique"].get("sexe")
        if isinstance(sexe, str):
            s = _normalize_case(sexe)
            if s.startswith("mascul"):
                return "Masculin"
            if s.startswith("fémin") or s.startswith("femin"):
                return "Féminin"
    except Exception:
        pass
    return None



# =======Construction dictionnaire des valeurs fictives==============#



def anonymize_usager_fields(
    doc: Dict[str, Any],
    debug: bool = False
) -> Tuple[Any, Dict[str, str]]:
    """
    Anonymise les champs sensibles de la section « usager » dans les données JSON.

    Construit un persona fictif pour l’usager (nom, prénom, adresse, etc.)
    puis remplace les valeurs originales par celles générées.
    Retourne également le mapping entre les valeurs anonymisées
    et les valeurs originales.

    Args:
        data (Dict[str, Any]): Données JSON de l’usager.
        debug (bool, optionnel): Si True, affiche les remplacements effectués.
            Par défaut False.

    Returns:
        Tuple[Dict[str, Any], Dict[str, str]]:
            - Les données avec les champs anonymisés.
            - Le mapping {valeur_anonymisée: valeur_originale}.
    """

    if debug:
        print("[DEBUG] anonymize_usager_fields: start")

    mapping: Dict[str, str] = {}

    usager = doc.get("usager", {})
    gender = detect_genre_usager(usager)
    if debug:
        print(f"[DEBUG] Detected gender: {gender!r}")

    persona = build_usager_persona(gender, debug=debug)

    # Remplacements (état civil)
    _replace_and_map(doc, USAGER_PATHS["clientId"], persona["client_id"], mapping, debug=debug)
    _replace_and_map(doc, USAGER_PATHS["nomFamille"], persona["last_name"], mapping, debug=debug)
    _replace_and_map(doc, USAGER_PATHS["nomUtilise"], persona["last_name"], mapping, debug=debug)
    _replace_and_map(doc, USAGER_PATHS["prenomsActeNaissance"], persona["first_name"], mapping, debug=debug)
    _replace_and_map(doc, USAGER_PATHS["premierPrenomActeNaissance"], persona["first_name"], mapping, debug=debug)
    _replace_and_map(doc, USAGER_PATHS["prenomUtilise"], persona["first_name"], mapping, debug=debug)

    # Situation familiale : si non-informative, on laisse tel quel; sinon on neutralise (ex. "Marié(e)")
    sit = _get_at_path(doc, USAGER_PATHS["situationFamiliale"], debug=debug)
    if isinstance(sit, str) and not _is_non_informatif(sit):
        _replace_and_map(doc, USAGER_PATHS["situationFamiliale"], "Marié(e)", mapping, debug=debug)

    # ... (remplacements état civil + adresse)
    _anonymize_usager_dob_full(doc, USAGER_PATHS["dateNaissance"], mapping, debug=debug)

    # Adresse (ligne[0], codePostal, libelleCommune, commentaire)
    _replace_and_map(doc, USAGER_PATHS["adresse_ligne0"], persona["address_line"], mapping, debug=debug)
    _replace_and_map(doc, USAGER_PATHS["adresse_codePostal"], persona["postcode"], mapping, debug=debug)
    _replace_and_map(doc, USAGER_PATHS["adresse_libelleCommune"], persona["commune"], mapping, debug=debug)
    _replace_and_map(doc, USAGER_PATHS["adresse_commentaire"], persona["commentaire"], mapping, debug=debug)

    if debug:
        preview = list(mapping.items())[:10]
        print(f"[DEBUG] Mapping preview (first 10): {preview}")
        print("[DEBUG] anonymize_usager_fields: done")

    return doc, mapping



# ================Fonction principale qui appelle plusieurs fonctions pour produire

def anonymize_contacts_fields(
    doc: Dict[str, Any],
    mapping: Dict[str, str],
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Anonymise les champs des contacts (0..N) et alimente le mapping.

    Pour chaque contact, la fonction :
      1) Détecte le genre via la civilité (si possible).
      2) Construit une persona (civilité, prénom, nom, DOB fictive).
      3) Remplace uniquement les champs **non marqués (*)** :
         - personnePhysique.prenomUtilise
         - personnePhysique.nomUtilise
         - personnePhysique.civilite (optionnel)
         - personnePhysique.dateNaissance
      4) Laisse intacts les champs marqués `(*)` :
         - typeContact, titre, role, natureLien, personneConfiance, responsableLegal

    Args:
        doc (Dict[str, Any]): Document JSON du patient (modifié sur place).
        mapping (Dict[str, str]): Mapping global {valeur_anon: valeur_originale}.
        debug (bool, optionnel): Active les messages de débogage.

    Returns:
        Dict[str, Any]: Le document JSON modifié (pour chaînage éventuel).
    """
    contacts = doc.get("contacts")
    if not isinstance(contacts, list) or not contacts:
        if debug:
            print("[DEBUG] Aucun contact à anonymiser.")
        return doc

    for i, contact in enumerate(contacts):
        if not isinstance(contact, dict):
            if debug:
                print(f"[DEBUG] Contact index {i} non dict, on ignore.")
            continue

        paths = _contact_paths(i)

        # Détection du genre du contact
        g = detect_genre_contact(contact)
        if debug:
            print(f"[DEBUG] Contact[{i}] genre détecté: {g!r}")

        persona = build_contact_persona(g, debug=debug)

        # Remplacements des champs anonymisés
        # civilité : si tu souhaites conserver l'originale, commente la ligne ci-dessous
        _replace_and_map(doc, paths["civilite"], persona["civilite"], mapping, debug=debug)

        _replace_and_map(doc, paths["prenomUtilise"], persona["first_name"], mapping, debug=debug)
        _replace_and_map(doc, paths["nomUtilise"], persona["last_name"], mapping, debug=debug)

        _anonymize_contact_dob_full(doc, paths["dateNaissance"], mapping, debug=debug)

        # Champs marqués (*) : ne pas remplacer
        if debug:
            kept = {k: _get_at_path(doc, v, debug=False) for k, v in paths.items() if k in CONTACTS_STATIC_KEEP}
            print(f"[DEBUG] Contact[{i}] champs conservés (*) -> {kept}")

    return doc


# =============Fonction principale=====================

def anonymize_patient_document(doc: Dict[str, Any], debug: bool = False) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Anonymise l’usager puis (le cas échéant) les contacts et retourne (doc, mapping).
    """
    doc_anon, mapping = anonymize_usager_fields(doc, debug=debug)   # usager + DOB
    doc_anon = anonymize_contacts_fields(doc_anon, mapping, debug=debug)  # contacts
    return doc_anon, mapping



# =============Fonction inverse de désanonymisation==============

import re
from typing import Dict


def deanonymize_fields(
        text: str,
        mapping_anon_to_orig: Dict[str, str],
        debug: bool = False
) -> Tuple[str, Dict[str, str]]:
    """
    Remplace dans 'text' toutes les valeurs anonymisées par leurs valeurs originales
    en utilisant le mapping {anonymisé -> original}.

    Args:
        text (str): Le texte potentiellement contenant des valeurs anonymisées.
        mapping_anon_to_orig (Dict[str, str]): Dictionnaire des correspondances.
        debug (bool, optionnel): Affiche les substitutions effectuées si True.

    Returns:
        Tuple[str, Dict[str, str]]:
            - Texte désanonymisé (chaîne de caractères).
            - Reverse mapping {original -> anonymisé} pour usage ultérieur.
    """
    if not mapping_anon_to_orig:
        return text, {}

    # Trie les clés anonymisées par longueur décroissante (évite collisions partielles)
    keys = sorted(mapping_anon_to_orig.keys(), key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(k) for k in keys))

    def _sub(m):
        k = m.group(0)
        original = mapping_anon_to_orig.get(k, k)
        if debug:
            print(f"[DEBUG] Remplacement '{k}' -> '{original}'")
        return original

    deanonymized_text = pattern.sub(_sub, text)

    # Construction du reverse mapping {original -> anonymisé}
    reverse_mapping = {v: k for k, v in mapping_anon_to_orig.items()}

    return deanonymized_text, reverse_mapping





















