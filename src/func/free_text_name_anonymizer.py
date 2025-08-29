# src/func/free_text_name_anonymizer.py

"""
Module : free_text_name_anonymizer
---------------------------------

Ce module gère l’anonymisation et la désanonymisation des mentions libres
du nom et prénom du patient dans un POA (Plan d’Objectifs et d’Actions).

Contrairement à l’anonymisation structurée (sections « usager » et « contacts »),
les informations saisies manuellement par les évaluateurs peuvent contenir
le nom ou le prénom du patient dans des champs texte libres
(ex. « Mme Anne Dupont, son épouse est présente »).

Fonctionnalités principales :
    - Normalisation des chaînes (suppression des accents, casse insensible,
      gestion des espaces Unicode).
    - Construction de variantes (nom, prénom, « Prénom Nom », « Nom Prénom »,
      civilités + nom, civilités + prénom + nom).
    - Parcours récursif des structures de type dict/list pour détecter
      les chaînes contenant le nom/prénom du patient.
    - Remplacement par l’alias choisi lors de l’anonymisation structurée.
    - Mise à jour du mapping {alias -> original} pour permettre la
      désanonymisation correcte de la réponse du LLM.

Utilisation typique dans le pipeline :
    >>> from src.func.anonymizer import anonymize_patient_document
    >>> from src.func.free_text_name_anonymizer import anonymize_name_mentions_in_free_text
    >>>
    >>> # 1. Anonymisation structurée (usager + contacts)
    >>> anonymized_doc, mapping = anonymize_patient_document(cleaned_doc, debug=False)
    >>>
    >>> # 2. Anonymisation complémentaire dans le texte libre
    >>> anonymized_doc, mapping = anonymize_name_mentions_in_free_text(anonymized_doc, mapping, debug=False)
    >>>
    >>> # 3. Conversion JSON → texte et envoi au LLM
    >>> anonymized_text = convert_json_to_text(anonymized_doc)
    >>> response = llm_model.invoke(anonymized_text)
    >>>
    >>> # 4. Désanonymisation de la réponse du LLM
    >>> deanonymized_text, reverse_mapping = deanonymize_fields(response, mapping)

Remarques :
    - Les sections « usager » et « contacts » sont explicitement exclues
      de la passe texte libre (elles sont déjà traitées par anonymization structurée).
    - Le module produit un document anonymisé et un mapping enrichi.
    - La comparaison est insensible à la casse et aux accents, et tolère
      les espaces insécables ou multiples.

"""

from __future__ import annotations
import re, unicodedata
from typing import Any, Dict, Iterable, List, Tuple, Optional, Union



_WS_RE = re.compile(r"\s+", flags=re.UNICODE)


def _strip_accents_casefold(s: str) -> str:
    """
    Normalise une chaîne en supprimant les accents et en ignorant la casse.

    La chaîne est décomposée (NFD), les diacritiques sont retirés, tous les
    types d’espaces Unicode sont comprimés en un seul espace, puis `casefold()`
    est appliqué pour des comparaisons robustes (mieux que `lower()`).

    Args:
        s (str): La chaîne d’entrée.

    Returns:
        str: La chaîne normalisée (sans accents, casse normalisée, espaces compressés).
    """

    if not isinstance(s, str):
        return ""
    s_norm = unicodedata.normalize("NFD", s)
    s_noacc = "".join(c for c in s_norm if unicodedata.category(c) != "Mn")
    s_noacc = _WS_RE.sub(" ", s_noacc)  # <- remplace tout whitespace par ' '
    return s_noacc.casefold().strip()


def _debug_dump(s: str) -> str:
    """
    Retourne une représentation des points de code Unicode d’une chaîne.

    Utile pour diagnostiquer des problèmes d’encodage ou d’espaces invisibles
    (ex. espaces insécables). Chaque caractère est affiché avec sa valeur
    hexadécimale (ex. ' '(0x00a0) pour NBSP).

    Args:
        s (str): La chaîne à inspecter.

    Returns:
        str: Une chaîne listant les caractères et leurs points de code.
    """

    return " ".join(f"{ch}({ord(ch):#06x})" for ch in s)



def _iter_string_fields(obj: Any, path: List[str] | None = None) -> Iterable[Tuple[List[str], str]]:
    """
     Itère récursivement sur tous les champs texte d’une structure Python.

     Parcourt dictionnaires et listes imbriqués, et produit des couples
     (chemin, valeur) pour chaque champ de type `str`. Le chemin est une
     liste de clés/indices (ex. ["social", "blocs", "[0]", "reponse"]).

     Args:
         obj (Any): Structure Python (dict, list, scalaires).
         path (List[str] | None, optionnel): Chemin courant lors de la récursion.

     Yields:
         Iterable[Tuple[List[str], str]]: Couples (path, value) pour chaque chaîne trouvée.
     """

    if path is None:
        path = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_string_fields(v, path + [str(k)])
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _iter_string_fields(v, path + [f"[{i}]"])
    else:
        if isinstance(obj, str):
            yield path, obj



def _get_parent_and_key(root: Any, path: List[str]) -> Tuple[Any, Optional[str]]:
    """
    Retourne le conteneur parent et la clé/position finale pour un chemin donné.

    Permet de réassigner une nouvelle valeur à l’emplacement ciblé. Gère
    les dictionnaires et les listes (indices représentés sous la forme "[i]").

    Args:
        root (Any): Racine de la structure.
        path (List[str]): Chemin vers la valeur cible.

    Returns:
        Tuple[Any, Optional[str]]: (parent, clé_ou_indice_token) ou (None, None) si introuvable.
    """

    if not path:
        return None, None
    parent = root
    for token in path[:-1]:
        if isinstance(parent, dict) and token in parent:
            parent = parent[token]
        elif isinstance(parent, list) and token.startswith("[") and token.endswith("]"):
            try:
                idx = int(token[1:-1])
            except Exception:
                return None, None
            if 0 <= idx < len(parent):
                parent = parent[idx]
            else:
                return None, None
        else:
            return None, None
    return parent, path[-1]



def _should_skip_path(path: List[str]) -> bool:
    """
    Indique si un chemin doit être ignoré (sections déjà traitées).

    Retourne True pour les chemins appartenant aux sections 'usager'
    ou 'contacts', afin d’éviter un retraitement des champs déjà
    anonymisés de manière structurée.

    Args:
        path (List[str]): Chemin du champ courant.

    Returns:
        bool: True si le chemin doit être ignoré, False sinon.
    """

    return len(path) >= 1 and path[0] in {"usager", "contacts"}



def _build_variants(first_name: str, last_name: str) -> List[str]:
    """
    Construit des variantes textuelles du nom de l’usager à détecter.

    Génère les formes usuelles pour maximiser la détection en texte libre :
      - nom seul (ex. "Dupont"),
      - prénom seul (ex. "Anne"),
      - "Prénom Nom" et "Nom Prénom",
      - civilités + nom (ex. "M. Dupont", "Madame Dupont"),
      - civilités + prénom + nom (ex. "Mme Anne Dupont").

    Args:
        first_name (str): Prénom original de l’usager.
        last_name (str): Nom original de l’usager.

    Returns:
        List[str]: Liste dédupliquée de variantes à rechercher/remplacer.
    """

    f = (first_name or "").strip()
    l = (last_name or "").strip()

    variants = []

    if l:
        # Nom seul, combinaisons simples
        variants += [l, f"{l} {f}".strip(), f"{f} {l}".strip()]
        # Civilités + Nom
        variants += [f"M. {l}", f"M {l}", f"Monsieur {l}", f"Mons {l}", f"Mme {l}", f"Madame {l}"]
        # Civilités + Prénom + Nom
        if f:
            variants += [f"M. {f} {l}", f"M {f} {l}", f"Monsieur {f} {l}", f"Mons {f} {l}", f"Mme {f} {l}", f"Madame {f} {l}"]

    if f:
        variants.append(f)

    # Dédoublonnage
    out, seen = [], set()
    for v in variants:
        if v and v not in seen:
            out.append(v)
            seen.add(v)

    return out


def _compile_variants_regex(variants: list[str]) -> tuple[re.Pattern, dict[str, str]]:
    """
    Compile un motif regex robuste couvrant toutes les variantes.

    Les variantes sont d’abord normalisées (sans accents, casse insensible,
    espaces Unicode compressés). Le motif résultant tolère des espaces multiples
    (`\\s+`) entre les tokens et utilise des bords de mots (`\\b`).

    Args:
        variants (List[str]): Variantes brutes (non normalisées).

    Returns:
        Tuple[re.Pattern, Dict[str, str]]:
            - Motif regex compilé pour rechercher les variantes dans du texte normalisé.
            - Dictionnaire {forme_normalisée: forme_originale} pour retrouver la variante source.
    """

    canon_map: dict[str, str] = {}
    pieces: list[str] = []

    for v in variants:
        nv = _strip_accents_casefold(v)
        if not nv:
            continue
        # split sur espace (déjà normalisé en simple ' ') puis recolle avec \s+
        tokens = nv.split(" ")
        part = r"\s+".join(re.escape(tok) for tok in tokens if tok)
        pieces.append(part)
        canon_map.setdefault(nv, v)

    if not pieces:
        return re.compile(r"(?!x)x"), {}

    # \b aux extrémités + IGNORECASE+UNICODE
    pat = r"\b(?:%s)\b" % "|".join(sorted(pieces, key=len, reverse=True))
    return re.compile(pat, flags=re.IGNORECASE | re.UNICODE), canon_map


def _replacement_for_variant(original_variant: str, orig_first: str, orig_last: str, alias_first: str, alias_last: str) -> str:
    """
    Détermine la chaîne de remplacement (alias) adaptée à une variante rencontrée.

    Respecte la structure de la variante originale :
      - "Prénom Nom"  -> "alias_first alias_last"
      - "Nom Prénom"  -> "alias_last alias_first"
      - civilité + Nom -> même civilité + alias_last
      - nom seul       -> alias_last
      - prénom seul    -> alias_first
      - par défaut     -> "alias_first alias_last"

    Args:
        original_variant (str): Variante détectée dans le texte.
        orig_first (str): Prénom original.
        orig_last (str): Nom original.
        alias_first (str): Prénom alias.
        alias_last (str): Nom alias.

    Returns:
        str: La chaîne de remplacement correspondante.
    """

    ov = original_variant.strip()
    # Formes “Prénom Nom” / “Nom Prénom”
    if " " in ov:
        parts = ov.split()
        if len(parts) == 2:
            a, b = parts[0], parts[1]
            if (_strip_accents_casefold(a) == _strip_accents_casefold(orig_first) and
                _strip_accents_casefold(b) == _strip_accents_casefold(orig_last)):
                return f"{alias_first} {alias_last}"
            if (_strip_accents_casefold(a) == _strip_accents_casefold(orig_last) and
                _strip_accents_casefold(b) == _strip_accents_casefold(orig_first)):
                return f"{alias_last} {alias_first}"
    # Civilités + Nom
    civ_map = {"m.": "M.", "m ": "M.", "monsieur": "Monsieur", "mons": "Monsieur", "mme": "Mme", "madame": "Madame"}
    ov_norm = _strip_accents_casefold(ov)
    for civ_norm, civ_print in civ_map.items():
        if ov_norm.startswith(civ_norm + " "):
            return f"{civ_print} {alias_last}"
    # Nom seul / Prénom seul
    if _strip_accents_casefold(ov) == _strip_accents_casefold(orig_last):
        return alias_last
    if _strip_accents_casefold(ov) == _strip_accents_casefold(orig_first):
        return alias_first
    # Par défaut
    return f"{alias_first} {alias_last}"


def _extract_names_from_doc_and_mapping(doc_anon: Dict[str, Any], mapping_anon_to_orig: Dict[str, str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extrait (orig_first, orig_last, alias_first, alias_last) depuis le doc et le mapping.

    Récupère l’alias (prenomUtilise, nomUtilise) dans le document anonymisé
    et retrouve les valeurs originales en inversant le mapping {anonymisé -> original}.
    Retourne None si une information nécessaire est manquante.

    Args:
        doc_anon (Dict[str, Any]): Document anonymisé (section usager incluse).
        mapping_anon_to_orig (Dict[str, str]): Mapping {anonymisé -> original}.

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
            (orig_first, orig_last, alias_first, alias_last).
    """

    try:
        pp = doc_anon["usager"]["Informations d'état civil"]["personnePhysique"]
        alias_first = pp.get("prenomUtilise")
        alias_last  = pp.get("nomUtilise")
    except Exception:
        return None, None, None, None
    orig_first = mapping_anon_to_orig.get(str(alias_first)) if alias_first else None
    orig_last  = mapping_anon_to_orig.get(str(alias_last))  if alias_last  else None
    return orig_first, orig_last, alias_first, alias_last


def anonymize_name_mentions_in_free_text(
    data_or_tuple: Union[Dict[str, Any], Tuple[Dict[str, Any], List[str]]],
    mapping_anon_to_orig: Dict[str, str],
    *,
    debug: bool = False
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Remplace, hors sections 'usager' et 'contacts', les mentions libres du nom/prénom
    du patient par l’alias (persona) et renvoie (document_modifié, mapping_enrichi).

    La fonction :
      1) Récupère le couple (prénom/nom) alias dans le document anonymisé,
         et les originaux en inversant le mapping {anonymisé -> original}.
      2) Construit des variantes texte (Nom, Prénom, "Prénom Nom", "Nom Prénom",
         civilités + Nom) pour maximiser la détection.
      3) Parcourt récursivement toutes les chaînes du document (dict/list),
         en **ignorant** explicitement les sections 'usager' et 'contacts'.
      4) Remplace les occurrences par l’alias approprié et **enrichit** le mapping
         avec des paires {anonymisé -> original} utiles à la désanonymisation LLM.

    Remarques :
      - L’entrée peut être un dict ou un tuple (dict, changes) retourné par
        `clean_patient_document(trace=True)` ; dans ce cas seul le dict est modifié.
      - La comparaison est insensible à la casse et aux accents.
      - Le mapping est mis à jour **in-place** et aussi renvoyé pour chaînage.

    Args:
        data_or_tuple: Document patient (dict) ou (dict, changes).
        mapping_anon_to_orig: Mapping existant {anonymisé -> original} à enrichir.
        debug: Active les messages de débogage.

    Returns:
        Tuple[Dict[str, Any], Dict[str, str]]:
            - Le document modifié (dict anonymisé côté texte libre).
            - Le mapping {anonymisé -> original} enrichi.

    Exemple:
        >>> doc_anon, mapping = anonymize_patient_document(cleaned_doc)
        >>> doc_anon, mapping = anonymize_name_mentions_in_free_text(doc_anon, mapping)
        >>> # puis en sortie LLM :
        >>> text_final, reverse = deanonymize_fields(llm_text, mapping)
    """
    # Support Union[dict, (dict, changes)]
    doc = data_or_tuple[0] if isinstance(data_or_tuple, tuple) else data_or_tuple
    if not isinstance(doc, dict):
        if debug:
            print("[DEBUG] Entrée non dict; aucun traitement.")
        return doc, mapping_anon_to_orig

    # 1) Récupérer (originaux, alias) depuis doc + mapping
    orig_first, orig_last, alias_first, alias_last = _extract_names_from_doc_and_mapping(doc, mapping_anon_to_orig)
    if not (orig_first and orig_last and alias_first and alias_last):
        if debug:
            print("[DEBUG] Impossible de déterminer les noms orig/alias; passe texte libre annulée.")
        return doc, mapping_anon_to_orig

    # 2) Construire variantes + motif
    variants = _build_variants(orig_first, orig_last)
    pattern, canon_map = _compile_variants_regex(variants)
    if not canon_map:
        if debug:
            print("[DEBUG] Aucune variante canonique; rien à remplacer.")
        return doc, mapping_anon_to_orig

    # 3) Parcours des champs texte hors usager/contacts
    for path, value in _iter_string_fields(doc):
        if not value or _should_skip_path(path):
            continue

        # Dans la boucle pour ce path précis :
        if debug and path[-1] == "reponse":
            print("[DEBUG] RAW :", repr(value))
            print("[DEBUG] NORM:", _strip_accents_casefold(value))
            print("[DEBUG] CP  :", _debug_dump(value[:40]))

        text_norm = _strip_accents_casefold(value)
        if not pattern.search(text_norm):
            continue

        # 4) Remplacements + enrichissement mapping
        new_value = value

        for v in sorted(canon_map.values(), key=len, reverse=True):
            # On compile un motif insensible à la casse, avec bords de mot
            rx = re.compile(rf"\b{re.escape(v)}\b", flags=re.IGNORECASE | re.UNICODE)

            def _fn(m: re.Match) -> str:
                seen = m.group(0)  # forme exacte rencontrée dans le texte ("Deloin", "DELOIN", "deloin"...)
                repl = _replacement_for_variant(
                    v, orig_first, orig_last, alias_first, alias_last
                )
                # mapping dans le bon sens pour la désanonymisation ultérieure
                mapping_anon_to_orig[str(repl)] = str(seen)
                if debug:
                    print(f"[DEBUG] Remplacement libre: '{seen}' -> '{repl}'")
                return repl

            new_value, n = rx.subn(_fn, new_value)


        parent, last = _get_parent_and_key(doc, path)
        if parent is None:
            continue
        if isinstance(parent, dict):
            parent[last] = new_value
        elif isinstance(parent, list) and last and last.startswith("[") and last.endswith("]"):
            parent[int(last[1:-1])] = new_value

        if debug and new_value != value:
            print(f"[DEBUG] Remplacement texte libre @ {'.'.join(path)}")
            print(f"        AVANT: {value!r}")
            print(f"        APRES: {new_value!r}")

    return doc, mapping_anon_to_orig