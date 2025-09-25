# src/func/anonymizer.py
"""Outils d’anonymisation pour documents patient (JSON).

Masque les champs sensibles (identité, coordonnées, adresses, situationFamiliale)
tout en préservant la structure du document et la lisibilité des sorties.
Maintient un mapping bijectif {anonymisé -> original} avec suffixes anti-collision.
Gère les tokens neutres (« Non renseigné ») et fournit des helpers de parcours avec logs.
"""

from __future__ import annotations
import secrets
import datetime as dt
import math
import bisect
import random
import unicodedata
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
    "Daniel","Christian","René","Claude","Gérard","Paul","Marcel","Raymond","Roger","Henri",
    "Laurent", "Olivier", "Nicolas", "Pascal", "Bruno", "Vincent", "Thierry", "Frédéric",
    "Christophe"
]
FIRST_NAMES_F: List[str] = [
    "Marie","Jeanne","Monique","Françoise","Nicole","Catherine","Madeleine","Sylvie","Martine","Anne",
    "Hélène","Danielle","Colette","Jacqueline","Suzanne","Michèle","Yvette","Yvonne","Nathalie","Chantal",
    "Sophie", "Isabelle", "Catherine", "Nathalie", "Valérie", "Sandrine", "Véronique",
    "Caroline", "Hélène"
]
LAST_NAMES: List[str] = [
    "Flaubert","Spinoza","Dubois","Descartes","Eluard","Balzac","Berri","Durand","Leroy","Moreau",
    "Joules","Bringer","Jousset","Garcia","Bouvet","Chauvet","Roux","Duroul","Fournier","Morel",
    "Hugo", "Proust", "Sand", "Camus", "Zola", "Duras", "Saint-Exupery", "Mauriac", "Colette"
]
# 20 noms de voie FR usuels
STREET_NAMES: List[str] = [
    "rue de la Paix","avenue Victor Hugo","boulevard Saint-Michel","rue des Écoles","rue de la République",
    "avenue de Verdun","rue Nationale","rue de la Gare","rue du Moulin","rue du Château",
    "rue Pasteur","rue Jules Ferry","rue des Lilas","rue Victor Hugo","rue de l'Église",
    "avenue de la Liberté","rue de la Mairie","rue des Acacias","rue du Stade","rue des Fleurs",
    "avenue de l'Europe", "allée de L'osier ", "Rue des Grands Varays ", "avenue Pierre Mendès-France ",
    "Route des Docteurs Devillers ", "ZI de la Briquetterie ", "rue Blondel", "Boulevard de l'Europe", "Rue Auguste Delaune "
]
# Couples (CP, Commune) FR plausibles (20)
POSTCODES_COMMUNES: List[Tuple[str, str]] = [
    ("75001","Paris"),("13001","Marseille"),("69001","Lyon"),("31000","Toulouse"),("44000","Nantes"),
    ("33000","Bordeaux"),("59000","Lille"),("67000","Strasbourg"),("34000","Montpellier"),("35000","Rennes"),
    ("21000","Dijon"),("06000","Nice"),("72000","Le Mans"),("49000","Angers"),("86000","Poitiers"),
    ("37000","Tours"),("02000","Laon"),("02100","Saint-Quentin"),("80000","Amiens"),("51100","Reims"),
    ("01230", "Saint-Rambert-en-Bugey"), ("01310", "Polliat"), ("01540", "Vonnas",), ("02000", "Laon"),
    ("02120", "Guise"), ("02140", "Vervins"), ("02240", "Ribemont"), ("02300", "Chauny"), ("02430", "Gauchy")
]

NON_INFORMATIF = {"", "non renseigné", "null"}

# jeux de valeurs reconnues (après normalisation)
_MALE_TOKENS = {
    "m", "h", "homme", "m.", "mr", "monsieur", "masculin", "male", "mister"
}
_FEMALE_TOKENS = {
    "f", "femme", "mme", "madame", "mlle", "melle", "mademoiselle",
    "feminin", "feminin.", "féminin", "female"
}

# ---
# --------- Fonctions annexes -------------
def _normalize_token(s: str) -> str:
    """minuscule, accents retirés, espaces/ponctuation enlevés aux extrémités"""
    s = s.strip()
    # NFKD pour séparer lettres/accents, puis suppression des accents
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().strip(" .,-_/\\")
    return s


def _detect_from_fields(sexe_raw: Optional[str], civilite_raw: Optional[str]) -> Optional[str]:
    """
    Détermine 'M'/'F' en priorisant le champ 'sexe' s'il est exploitable,
    sinon en se rabattant sur 'civilite'. Retourne None si indéterminé.
    """
    # 1) tenter depuis 'sexe'
    if sexe_raw:
        t = _normalize_token(str(sexe_raw))
        if t in _MALE_TOKENS:   return "M"
        if t in _FEMALE_TOKENS: return "F"

        # cas très fréquents "m"/"f" même sans appartenance stricte
        if t == "m": return "M"
        if t == "f": return "F"

    # 2) sinon tenter depuis 'civilité'
    if civilite_raw:
        t = _normalize_token(str(civilite_raw))
        if t in _MALE_TOKENS:   return "M"
        if t in _FEMALE_TOKENS: return "F"
        if t == "m":  return "M"
        if t == "f":  return "F"

    # 3) sinon indéterminé (laisser le reste du pipeline gérer un prénom neutre/initiales)
    return None


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

    """
    return isinstance(s, str) and _normalize_token(s) in NON_INFORMATIF


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
        pick(["Alice", "Bob", "Charlie"])
        'Bob'
    """
    choice = secrets.choice(options)
    if debug:
        print(f"[DEBUG] Picked value: {choice}")
    return choice

# ------


# I.a -------- Construction date de naissance fictive pour l'usager et les contacts de l'usager -----------
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


# -------- I.a Date naissance usager -----------
def _anonymize_usager_dob_full(doc: dict, path: list[str], mapping: dict[str, str], debug: bool = False) -> None:
    original = _get_at_path(doc, path, debug=debug)
    if debug:
        print(f"[DEBUG] DOB original at {path}: {original!r}")

    age = _sample_age()
    dob = _sample_dob_from_age(age)
    anon_value = dob.isoformat()

    if debug:
        print(f"[DEBUG] DOB full -> {anon_value!r} (âge simulé ≈ {age})")

    _replace_and_map(
        doc=doc,
        path=path,
        original_value=original,
        anonymized_value=anon_value,
        mapping_anon_to_orig=mapping,
        debug=debug,
    )


# -------- I.b Date naissance pour un contact de l'usager  -----------
def _anonymize_contact_dob_full(
    doc: Dict[str, Any],
    path: List[str],
    mapping: Dict[str, str],
    debug: bool = False
) -> None:
    original = _get_at_path(doc, path, debug=debug)
    if debug:
        print(f"[DEBUG] Contact DOB original at {path}: {original!r}")

    age = _sample_age()
    dob = _sample_dob_from_age(age).isoformat()
    if debug:
        print(f"[DEBUG] Contact DOB full -> {dob!r} (âge simulé ≈ {age})")

    _replace_and_map(
        doc=doc,
        path=path,
        original_value=original,
        anonymized_value=dob,
        mapping_anon_to_orig=mapping,
        debug=debug,
    )


# -------- II.a Construction d'un persona fictif pour l'usager -----------
def build_usager_persona(
    gender: str | None = None,
    sexe: str | None = None,
    civilite: str | None = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Construit une identité fictive (« persona ») pour l’usager.
    Le choix du prénom tient compte du genre détecté via _detect_from_fields(sexe, civilite).
    """

    # 1) Détection robuste du genre
    detected = _detect_from_fields(sexe_raw=sexe, civilite_raw=civilite)

    # Si rien trouvé et qu'on t'a passé un "gender" legacy (ex: "Masculin"/"Féminin"),
    # on réutilise _detect_from_fields en lui donnant 'gender' comme 'sexe'.
    if detected is None and gender:
        detected = _detect_from_fields(sexe_raw=gender, civilite_raw=None)

    # 2) Choix du prénom en fonction du genre détecté
    if detected == "M":
        first = pick(FIRST_NAMES_M, debug=debug)
    elif detected == "F":
        first = pick(FIRST_NAMES_F, debug=debug)
    else:
        # genre inconnu : on pioche dans la liste mixte
        first = pick(FIRST_NAMES_M + FIRST_NAMES_F, debug=debug)

    # 3) Nom + adresse
    last = pick(LAST_NAMES, debug=debug)

    number = secrets.randbelow(199) + 1
    street = pick(STREET_NAMES, debug=debug)
    addr_line = f"{number} {street}"

    cp, commune = pick(POSTCODES_COMMUNES, debug=debug)
    commentaire = "Accès : interphone"
    client_id = f"CLT-{secrets.token_hex(4).upper()}"

    persona = {
        "first_name": first,
        "last_name": last,
        "address_line": addr_line,
        "postcode": cp,
        "commune": commune,
        "commentaire": commentaire,
        "client_id": client_id,
        "domicile": "domicile_1",
        "mobile": "mobile_1",
        "mail": "mail_1"
    }
    if debug:
        print(f"[DEBUG] build_usager_persona(gender={gender}, sexe={sexe}, civilite={civilite}) -> {persona}")
    return persona


"""Section: OUTILS D’ANONYMISATION & MAPPING
Utilitaires pour accéder/modifier des valeurs dans un dict JSON par chemins,
et pour effectuer les remplacements en maintenant un mapping.
"""



# -------- II.b Construction d'un persona fictif pour les contacts de l'usager -----------
# Données de contacts qu'in décide de ne pas anonymiser (pas de données sensibles)
CONTACTS_STATIC_KEEP = {
    "typeContact",
    "titre",
    "role",
    "natureLien",
    "personneConfiance",
    "responsableLegal",
}


# ---------- Détection du genre du contact ------------
def detect_genre_contact(contact: dict) -> Optional[str]:
    """
    Retourne 'M', 'F' ou None si indéterminé.
    Cherche dans contact['personnePhysique'] (et tolère l'absence de 'sexe' côté contacts).
    """
    pp = (contact or {}).get("personnePhysique", {})

    # côté contacts, 'sexe' est souvent absent ; on se repose donc surtout sur 'civilite'
    sexe     = pp.get("sexe") or pp.get("Sexe")
    civilite = pp.get("civilite") or pp.get("Civilite")

    return _detect_from_fields(sexe, civilite)


# ------------- Construction d'un persona pour un contact de l'usager ------------
from typing import Optional, Dict, Any

def build_contact_persona(
    gender: Optional[str] = None,
    sexe: Optional[str] = None,
    civilite: Optional[str] = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Construit une persona française pour un contact.

    Génère un prénom (selon le genre si connu), un nom, une civilité cohérente,
    et une date de naissance fictive raisonnable.

    Args:
        gender: Valeur historique ("Masculin"/"Féminin") — utilisée seulement si `sexe`/`civilite` absents.
        sexe:   Champ 'sexe' du contact s'il existe (p.ex. "M", "F", "masculin", "féminin", etc.).
        civilite: Champ 'civilite' du contact s'il existe (p.ex. "M", "M.", "Monsieur", "Mme", "Madame").
        debug:  Active des impressions de debug.

    Returns:
        Dict[str, Any]: { "civilite", "first_name", "last_name", "dob" }
    """
    # 1) Détection robuste via même logique que pour l’usager
    detected = _detect_from_fields(sexe_raw=sexe, civilite_raw=civilite)
    if detected is None and gender:
        detected = _detect_from_fields(sexe_raw=gender, civilite_raw=None)

    # 2) Choix du prénom en fonction du genre détecté
    if detected == "M":
        first = pick(FIRST_NAMES_M, debug=debug)
    elif detected == "F":
        first = pick(FIRST_NAMES_F, debug=debug)
    else:
        first = pick(FIRST_NAMES_M + FIRST_NAMES_F, debug=debug)

    # 3) Civilité cohérente
    #    - Si on avait une civilité source (paramètre), on génère une civilité anonymisée cohérente
    #      avec le genre détecté (ou neutre si inconnu).
    #    - Sinon, on choisit une civilité par défaut cohérente.
    if detected == "M":
        civilite_out = "M."
    elif detected == "F":
        civilite_out = "Mme"
    else:
        # genre inconnu -> civilité neutre parmi M./Mme
        civilite_out = pick(["M.", "Mme"], debug=debug)

    # 4) Nom + date de naissance
    last = pick(LAST_NAMES, debug=debug)

    age = _sample_age()
    dob = _sample_dob_from_age(age).isoformat()

    persona = {
        "civilite": civilite_out,
        "first_name": first,
        "last_name": last,
        "dob": dob,
    }
    if debug:
        print(f"[DEBUG] build_contact_persona(gender={gender}, sexe={sexe}, civilite={civilite}) -> {persona}")
    return persona


# ------------ Construire les chemins des données à anonymiser dans un dictionnaire pour un contact -------------
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

        # champs conservés : mais on NE les remplace PAS lors de l’anonymisation.
        "typeContact": ["contacts", f"[{index}]", "typeContact"],
        "titre": ["contacts", f"[{index}]", "titre"],
        "role": ["contacts", f"[{index}]", "role"],
        "natureLien": ["contacts", f"[{index}]", "natureLien"],
        "personneConfiance": ["contacts", f"[{index}]", "personneConfiance"],
        "responsableLegal": ["contacts", f"[{index}]", "responsableLegal"],
    }



# ------------ Construction des dictionnaires ----------------#
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
        data = {}
        _ensure_path_dict(data, ["usager", "adresse"])
        {}
        data
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
        data = {"usager": {"nom": "Durand"}}
        _get_at_path(data, ["usager", "nom"])
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
        data = {}
        _set_at_path(data, ["usager", "nom"], "Martin")
        data
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



# -------------- Construction du mapping; correspondance entre valeurs originelles et valeurs fictives -----------#
def _replace_and_map(
    doc: dict,
    path: list,
    original_value,
    anonymized_value,
    mapping_anon_to_orig: dict,
    debug: bool = False,
):
    """
    Remplace la valeur à `path` par la version anonymisée et met à jour le mapping {anon -> orig}.
    Garde la bijectivité : jamais deux originaux pour le même anonymisé (ajoute un suffixe si collision).
    """
    if original_value is None:
        return

    orig = str(original_value)
    anon = str(anonymized_value)

    # collision ? on suffixe jusqu'à unicité (et on remplace la valeur par la version suffixée)
    if anon in mapping_anon_to_orig and mapping_anon_to_orig[anon] != orig:
        base = anon
        i = 2
        while anon in mapping_anon_to_orig and mapping_anon_to_orig[anon] != orig:
            anon = f"{base}#{i}"
            i += 1
        if debug:
            print(f"[DEBUG] Collision détectée : '{base}' déjà utilisé. Nouvelle valeur : '{anon}'")

    # écrire la valeur suffixée (le cas échéant) dans le document
    _set_at_path(doc, path, anon, debug=debug)

    # enregistrer la correspondance
    mapping_anon_to_orig[anon] = orig

    if debug:
        print(f"[DEBUG] Map: '{anon}' -> '{orig}'")


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

    # infos personnelles (domicile, mobile, mail)
    "contactInfosPersonnels_domicile": ["usager", "contactInfosPersonnels", "domicile"],
    "contactInfosPersonnels_mobile": ["usager", "contactInfosPersonnels", "mobile"],
    "contactInfosPersonnels_mail": ["usager", "contactInfosPersonnels", "mail"],

    # adresse
    "adresse_ligne0": ["usager","adresse","ligne","[0]"],   # list index 0
    "adresse_codePostal": ["usager","adresse","codePostal"],
    "adresse_libelleCommune": ["usager","adresse","libelleCommune"],
    "adresse_commentaire": ["usager","adresse","commentaire"],
}



# ------------ Détection genre de l'usager pour choix du prénom ----------------#
def detect_genre_usager(usager: dict) -> Optional[str]:
    """
    Retourne 'M', 'F' ou None si indéterminé.
    Cherche d'abord dans usager['Informations d'état civil']['personnePhysique'].
    """
    info = (usager or {}).get("Informations d'état civil", {})
    pp   = (info or {}).get("personnePhysique", {})

    # Les clés que l'on voit dans tes JSON
    sexe      = pp.get("sexe") or pp.get("Sexe")
    civilite  = pp.get("civilite") or pp.get("Civilite")

    return _detect_from_fields(sexe, civilite)


# ------------- Construction dictionnaire des valeurs fictives ---------------#
def _replace_with_original(
    doc: Dict[str, Any],
    path: List[str],
    anon_value: Any,
    mapping: Dict[str, str],
    debug: bool = False,
) -> None:
    orig = _get_at_path(doc, path, debug=debug)
    _replace_and_map(doc=doc, path=path,
                     original_value=orig, anonymized_value=str(anon_value),
                     mapping_anon_to_orig=mapping, debug=debug)


# ================================================#
# ======== Fonction principale USAGERS ===========#
# ================================================#

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

    pp = usager.get("Informations d'état civil", {}).get("personnePhysique", {})
    persona = build_usager_persona(
        sexe=pp.get("sexe") or pp.get("Sexe"),
        civilite=pp.get("civilite") or pp.get("Civilite"),
        debug=True
    )

    # --- État civil ---
    _replace_with_original(doc, USAGER_PATHS["clientId"], persona["client_id"], mapping, debug)
    _replace_with_original(doc, USAGER_PATHS["nomFamille"], persona["last_name"], mapping, debug)
    _replace_with_original(doc, USAGER_PATHS["nomUtilise"], persona["last_name"], mapping, debug)
    _replace_with_original(doc, USAGER_PATHS["prenomsActeNaissance"], persona["first_name"], mapping, debug)
    _replace_with_original(doc, USAGER_PATHS["premierPrenomActeNaissance"], persona["first_name"], mapping, debug)
    _replace_with_original(doc, USAGER_PATHS["prenomUtilise"], persona["first_name"], mapping, debug)

    # --- Situation familiale : neutraliser si informative
    sit = _get_at_path(doc, USAGER_PATHS["situationFamiliale"], debug=debug)
    if sit is None:
        # pas de mapping quand original == None, on écrit directement
        _set_at_path(doc, USAGER_PATHS["situationFamiliale"], "Non renseigné", debug=debug)
    elif isinstance(sit, str) and not _is_non_informatif(sit):
        # valeur informative -> neutraliser avec mapping
        _replace_with_original(doc, USAGER_PATHS["situationFamiliale"], "Non renseigné", mapping, debug)


    # --- Date de naissance
    _anonymize_usager_dob_full(doc, USAGER_PATHS["dateNaissance"], mapping, debug)

    # --- Adresse ---
    _replace_with_original(doc, USAGER_PATHS["adresse_ligne0"], persona["address_line"], mapping, debug)
    _replace_with_original(doc, USAGER_PATHS["adresse_codePostal"], persona["postcode"], mapping, debug)
    _replace_with_original(doc, USAGER_PATHS["adresse_libelleCommune"], persona["commune"], mapping, debug)
    _replace_with_original(doc, USAGER_PATHS["adresse_commentaire"], persona["commentaire"], mapping, debug)

    # --- Infos personnelles
    # domicile
    v = _get_at_path(doc, USAGER_PATHS["contactInfosPersonnels_domicile"], debug=debug)
    if v is None or (isinstance(v, str) and _is_non_informatif(v)):
        _set_at_path(doc, USAGER_PATHS["contactInfosPersonnels_domicile"], "Non renseigné", debug=debug)
    else:
        _replace_with_original(doc, USAGER_PATHS["contactInfosPersonnels_domicile"], persona["domicile"], mapping,
                               debug)

    # mobile
    v = _get_at_path(doc, USAGER_PATHS["contactInfosPersonnels_mobile"], debug=debug)
    if v is None or (isinstance(v, str) and _is_non_informatif(v)):
        _set_at_path(doc, USAGER_PATHS["contactInfosPersonnels_mobile"], "Non renseigné", debug=debug)
    else:
        _replace_with_original(doc, USAGER_PATHS["contactInfosPersonnels_mobile"], persona["mobile"], mapping, debug)

    # mail
    v = _get_at_path(doc, USAGER_PATHS["contactInfosPersonnels_mail"], debug=debug)
    if v is None or (isinstance(v, str) and _is_non_informatif(v)):
        _set_at_path(doc, USAGER_PATHS["contactInfosPersonnels_mail"], "Non renseigné", debug=debug)
    else:
        _replace_with_original(doc, USAGER_PATHS["contactInfosPersonnels_mail"], persona["mail"], mapping, debug)


    if debug:
        preview = list(mapping.items())[:10]
        print(f"[DEBUG] Mapping preview (first 10): {preview}")
        print("[DEBUG] anonymize_usager_fields: done")

    return doc, mapping


# ================================================#
# ======== Fonction principale CONTACTS ==========#
# ================================================#

def anonymize_contacts_fields(
    doc: Dict[str, Any],
    mapping: Dict[str, str],
    debug: bool = False,
) -> Dict[str, Any]:
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

        # On récupère les champs utiles pour la détection via _detect_from_fields(...)
        pp = (contact or {}).get("personnePhysique", {})
        persona = build_contact_persona(
            sexe=pp.get("sexe") or pp.get("Sexe"),
            civilite=pp.get("civilite") or pp.get("Civilite"),
            debug=debug,
        )

        # log de contrôle
        if debug:
            g_detected = detect_genre_contact(contact)
            print(f"[DEBUG] Contact[{i}] genre détecté (source doc): {g_detected!r}")
            print(f"[DEBUG] Contact[{i}] persona -> {persona}")

        # Remplacements des champs anonymisés
        # civilité : pour conserver l'originale, commenter ligne ci-dessous
        _replace_with_original(doc, paths["civilite"], persona["civilite"], mapping, debug)

        _replace_with_original(doc, paths["prenomUtilise"], persona["first_name"], mapping, debug)
        _replace_with_original(doc, paths["nomUtilise"], persona["last_name"], mapping, debug)

        # Date de naissance (utilise la fonction dédiée déjà mise à jour)
        _anonymize_contact_dob_full(doc, paths["dateNaissance"], mapping, debug)

        # Champs marqués (*) : ne pas remplacer (on les log pour contrôle)
        if debug:
            kept = {k: _get_at_path(doc, v, debug=False) for k, v in paths.items() if k in CONTACTS_STATIC_KEEP}
            print(f"[DEBUG] Contact[{i}] champs conservés (*) -> {kept}")

    return doc

# ===================================================== #
# =============Fonction principale===================== #
# ===================================================== #

def anonymize_patient_document(doc: Dict[str, Any], debug: bool = False) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Anonymise l’usager puis (le cas échéant) les contacts et retourne (doc, mapping).
    """
    doc_anon, mapping = anonymize_usager_fields(doc, debug=debug)   # usager + DOB
    doc_anon = anonymize_contacts_fields(doc_anon, mapping, debug=debug)  # contacts
    return doc_anon, mapping


# ======================================================================= #
# =============Fonction inverse de désanonymisation ===================== #
# ======================================================================= #

import re
from typing import Dict


_WORDLIKE_RE = re.compile(r"^[\wÀ-ÖØ-öø-ÿ]+(?:[ '\-][\wÀ-ÖØ-öø-ÿ]+)*$", re.UNICODE)

def deanonymize_fields(
        text: str,
        mapping_anon_to_orig: Dict[str, str],
        debug: bool = False
) -> Tuple[str, Dict[str, str]]:
    """
    Remplace dans 'text' toutes les valeurs anonymisées par leurs valeurs originales
    en utilisant le mapping {anonymisé -> original}.
    Retourne aussi {original -> anonymisé}.
    """
    if not mapping_anon_to_orig:
        return text, {}

    # 1) Trie par longueur décroissante (évite collisions partielles)
    keys = sorted(mapping_anon_to_orig.keys(), key=len, reverse=True)

    # 2) Sépare tokens "type mot" vs autres
    wordlike_keys = [k for k in keys if _WORDLIKE_RE.match(k)]
    other_keys    = [k for k in keys if k not in wordlike_keys]

    # 3) Passe 1 : tokens "autres" (dates, codes, ponctuation) - pas de bornes
    if other_keys:
        pattern_other = re.compile("|".join(re.escape(k) for k in other_keys))
        def _sub_other(m):
            k = m.group(0)
            original = mapping_anon_to_orig.get(k, k)
            if debug:
                print(f"[DEBUG] Remplacement '{k}' -> '{original}'")
            return original
        text = pattern_other.sub(_sub_other, text)

    # 4) Passe 2 : tokens "mot-like" avec bornes non-alphanumériques
    if wordlike_keys:
        pattern_word = re.compile(
            r"(?<!\w)(" + "|".join(re.escape(k) for k in wordlike_keys) + r")(?!\w)",
            flags=re.UNICODE
        )
        def _sub_word(m):
            k = m.group(1)
            original = mapping_anon_to_orig.get(k, k)
            if debug:
                print(f"[DEBUG] Remplacement '{k}' -> '{original}'")
            return original
        text = pattern_word.sub(_sub_word, text)

    # 5) reverse mapping (utile pour ré-anonymiser un extrait après coup)
    reverse_mapping = {v: k for k, v in mapping_anon_to_orig.items()}

    return text, reverse_mapping



















