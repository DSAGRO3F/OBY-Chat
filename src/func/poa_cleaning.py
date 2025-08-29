"""
Module de nettoyage des documents POA (Plan d’Objectifs et d’Actions).

Fonctions :
- clean_patient_document(data: dict, trace: bool = False) -> dict | (dict, list[str])

Comportement :
1) supprime les champs vides / non informatifs ("", "non renseigné", "null")
2) supprime les champs sensibles explicitement demandés (usager + contacts)
3) émonde les conteneurs (dict/list) devenus vides
4) (optionnel) trace chaque suppression si trace=True

Entrée : dict (JSON patient)
Sortie :
- si trace=False : dict nettoyé
- si trace=True  : (dict nettoyé, liste des suppressions)
"""

from typing import Dict, Any, List, Tuple, Union

NON_INFORMATIF = {"", "non renseigné", "null"}


def _is_empty_scalar(v: Any) -> bool:
    """
    Vérifie si une valeur est considérée comme un scalaire vide.

    Sont considérés comme vides : None, les chaînes vides et les
    collections vides. Cette fonction est utilisée pour simplifier
    le nettoyage récursif des documents patients.

    Args:
        v (Any): La valeur à vérifier.

    Returns:
        bool: True si la valeur est vide, False sinon.
    """

    return isinstance(v, str) and v.strip().lower() in NON_INFORMATIF


def _pop_in(d: Dict[str, Any], key: str, changes: List[str] | None = None, path: str = "") -> None:
    """
    Supprime une clé dans un dictionnaire imbriqué et enregistre le changement.

    Si la clé existe, elle est supprimée. L’opération peut être tracée en
    ajoutant le chemin de suppression à la liste des changements.

    Args:
        d (Dict[str, Any]): Le dictionnaire à modifier.
        key (str): La clé à supprimer.
        changes (List[str] | None, optionnel): Liste des chemins supprimés pour traçabilité.
        path (str, optionnel): Chemin courant dans la structure. Par défaut "".

    Returns:
        None
    """

    if isinstance(d, dict) and key in d:
        d.pop(key, None)
        if changes is not None:
            changes.append(f"Removed key: {path}.{key}" if path else f"Removed key: {key}")


def _get(d: Dict[str, Any], *path):
    """
    Récupère une valeur dans un dictionnaire imbriqué en suivant un chemin de clés.

    La fonction parcourt le dictionnaire étape par étape avec les clés données.
    Retourne None si une clé intermédiaire n’existe pas.

    Args:
        d (Dict[str, Any]): Le dictionnaire à parcourir.
        *path: Séquence de clés représentant le chemin d’accès.

    Returns:
        Any: La valeur trouvée, ou None si inexistante.
    """

    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def _ensure_dict(d: Dict[str, Any], *path) -> Dict[str, Any]:
    """
    Garantit qu’un chemin imbriqué existe dans un dictionnaire sous forme de dictionnaire.

    Si le chemin n’existe pas, les dictionnaires intermédiaires nécessaires
    sont créés. Retourne le dictionnaire final au bout du chemin.

    Args:
        d (Dict[str, Any]): Le dictionnaire à compléter.
        *path: Séquence de clés représentant le chemin à garantir.

    Returns:
        Dict[str, Any]: Le dictionnaire correspondant au chemin demandé.
    """

    cur = _get(d, *path)
    return cur if isinstance(cur, dict) else {}


def _clean_rec(value: Any, changes: List[str] | None = None, path: str = "") -> Any:
    """
    Nettoie récursivement les valeurs vides dans une structure.

    Supprime les None, chaînes vides et conteneurs vides
    (listes, dictionnaires) dans une structure imbriquée.
    Les suppressions peuvent être enregistrées pour audit.

    Args:
        value (Any): La valeur à nettoyer (dict, list ou scalaire).
        changes (List[str] | None, optionnel): Liste des chemins supprimés.
        path (str, optionnel): Chemin courant utilisé pour la traçabilité.

    Returns:
        Any: La valeur nettoyée, ou None si vide.
    """

    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            cur_path = f"{path}.{k}" if path else k
            if isinstance(v, str):
                if _is_empty_scalar(v):
                    if changes is not None:
                        changes.append(f"Removed empty value at: {cur_path}")
                    continue
                out[k] = v
            elif isinstance(v, (dict, list)):
                cleaned = _clean_rec(v, changes, cur_path)
                if cleaned not in (None, {}, [], ""):
                    out[k] = cleaned
                else:
                    if changes is not None:
                        changes.append(f"Removed empty container at: {cur_path}")
            else:
                if v is not None:
                    out[k] = v
                else:
                    if changes is not None:
                        changes.append(f"Removed null at: {cur_path}")
        return out

    if isinstance(value, list):
        cleaned_list = []
        for idx, item in enumerate(value):
            cur_path = f"{path}[{idx}]"
            if isinstance(item, str):
                if _is_empty_scalar(item):
                    if changes is not None:
                        changes.append(f"Removed empty value at: {cur_path}")
                    continue
                cleaned_list.append(item)
            elif isinstance(item, (dict, list)):
                cleaned = _clean_rec(item, changes, cur_path)
                if cleaned not in (None, {}, [], ""):
                    cleaned_list.append(cleaned)
                else:
                    if changes is not None:
                        changes.append(f"Removed empty container at: {cur_path}")
            else:
                if item is not None:
                    cleaned_list.append(item)
                else:
                    if changes is not None:
                        changes.append(f"Removed null at: {cur_path}")
        return cleaned_list

    # scalaires
    if isinstance(value, str) and _is_empty_scalar(value):
        if changes is not None:
            changes.append(f"Removed empty scalar at: {path or '<root>'}")
        return None
    return value


def _remove_usager_sensitive_fields(data: Dict[str, Any], changes: List[str] | None = None) -> None:
    """
    Supprime les champs sensibles dans la section 'usager' d’un document patient.

    Les champs supprimés concernent les informations identifiantes
    (adresse, téléphone, identifiants, etc.). Les suppressions peuvent
    être enregistrées pour traçabilité.

    Args:
        data (Dict[str, Any]): Le document patient sous forme de dictionnaire.
        changes (List[str] | None, optionnel): Liste des champs supprimés.

    Returns:
        None
    """

    # 1) usager.Informations d'état civil.personnePhysique.communeNaissance : libelleCommune, codePostal, inseeCommune
    base_path = "usager.Informations d'état civil.personnePhysique"
    pp = _ensure_dict(data, "usager", "Informations d'état civil", "personnePhysique")

    cn = pp.get("communeNaissance")
    if isinstance(cn, dict):
        for k in ("libelleCommune", "codePostal", "inseeCommune"):
            _pop_in(cn, k, changes, f"{base_path}.communeNaissance")

    # 2) usager.Informations d'état civil.personnePhysique.paysNaissance : libellePays, inseePays
    pn = pp.get("paysNaissance")
    if isinstance(pn, dict):
        for k in ("libellePays", "inseePays"):
            _pop_in(pn, k, changes, f"{base_path}.paysNaissance")

    # 3) usager.contactInfosPersonnels : domicile, mobile, mail
    cip = _ensure_dict(data, "usager", "contactInfosPersonnels")
    for k in ("domicile", "mobile", "mail"):
        _pop_in(cip, k, changes, "usager.contactInfosPersonnels")

    # 4) usager.mouvement : service, secteur
    mou = _ensure_dict(data, "usager", "mouvement")
    for k in ("service", "secteur"):
        _pop_in(mou, k, changes, "usager.mouvement")


def _remove_contacts_sensitive_fields(data: Dict[str, Any], changes: List[str] | None = None) -> None:
    """
    Supprime les champs sensibles dans la section 'contacts' d’un document patient.

    L’anonymisation ne s’applique qu’aux contacts de type
    'Cercle d'aide et de soin' ou 'Entourage'. Certains champs
    exclus restent conservés selon les règles définies.

    Args:
        data (Dict[str, Any]): Le document patient sous forme de dictionnaire.
        changes (List[str] | None, optionnel): Liste des champs supprimés.

    Returns:
        None
    """

    contacts = data.get("contacts")
    if not isinstance(contacts, list):
        return

    for i, c in enumerate(contacts):
        if not isinstance(c, dict):
            continue

        # 1) contact.adresse : ligne, codePostal, libelleCommune
        adr = c.get("adresse")
        if isinstance(adr, dict):
            _pop_in(adr, "ligne", changes, f"contacts[{i}].adresse")
            _pop_in(adr, "codePostal", changes, f"contacts[{i}].adresse")
            _pop_in(adr, "libelleCommune", changes, f"contacts[{i}].adresse")

        # 2) contact.contactInfosPersonnels : domicile, mobile, mail
        cip = c.get("contactInfosPersonnels")
        if isinstance(cip, dict):
            _pop_in(cip, "domicile", changes, f"contacts[{i}].contactInfosPersonnels")
            _pop_in(cip, "mobile", changes, f"contacts[{i}].contactInfosPersonnels")
            _pop_in(cip, "mail", changes, f"contacts[{i}].contactInfosPersonnels")

        # 3) contact.numRpps
        _pop_in(c, "numRpps", changes, f"contacts[{i}]")


def _prune_empty_containers(d: Any, changes: List[str] | None = None, path: str = "") -> Any:
    """
    Supprime récursivement les conteneurs vides (dictionnaires ou listes).

    Parcourt la structure et supprime les conteneurs devenus vides
    après nettoyage. Les suppressions peuvent être enregistrées pour traçabilité.

    Args:
        d (Any): La structure à nettoyer (dict, list, scalaire).
        changes (List[str] | None, optionnel): Liste des chemins supprimés.
        path (str, optionnel): Chemin courant utilisé pour la traçabilité.

    Returns:
        Any: La structure nettoyée, ou None si elle est vide.
    """

    if isinstance(d, dict):
        pruned = {}
        for k, v in d.items():
            cur_path = f"{path}.{k}" if path else k
            pruned_v = _prune_empty_containers(v, changes, cur_path)
            if pruned_v not in (None, {}, [], ""):
                pruned[k] = pruned_v
            else:
                if changes is not None:
                    changes.append(f"Removed empty container at: {cur_path}")
        return pruned

    if isinstance(d, list):
        pruned_list = []
        for idx, v in enumerate(d):
            cur_path = f"{path}[{idx}]"
            pruned_v = _prune_empty_containers(v, changes, cur_path)
            if pruned_v not in (None, {}, [], ""):
                pruned_list.append(pruned_v)
            else:
                if changes is not None:
                    changes.append(f"Removed empty container at: {cur_path}")
        return pruned_list

    return d


def clean_patient_document(
    data: Dict[str, Any],
    trace: bool = False,
) -> Union[Dict[str, Any], Tuple[Dict[str, Any], List[str]]]:
    """
    Nettoie un document patient en supprimant les champs sensibles et vides.

    La fonction :
      - anonymise les sections 'usager' et 'contacts',
      - supprime les conteneurs vides,
      - garantit une structure cohérente.

    Si `trace` est activé, la fonction retourne aussi la liste
    des changements effectués.

    Args:
        data (Dict[str, Any]): Le document patient sous forme de dictionnaire.
        trace (bool, optionnel): Si True, renvoie également la liste des changements.

    Returns:
        Union[Dict[str, Any], Tuple[Dict[str, Any], List[str]]]:
            - Le document nettoyé si trace=False.
            - Un tuple (document_nettoyé, changements) si trace=True.
    """

    changes: List[str] | None = [] if trace else None

    # 1) nettoyage générique (vides / "non renseigné" / "null")
    cleaned = _clean_rec(data, changes, "")

    # 2) retrait ciblé des champs sensibles
    if isinstance(cleaned, dict):
        _remove_usager_sensitive_fields(cleaned, changes)
        _remove_contacts_sensitive_fields(cleaned, changes)

    # 3) élagage des conteneurs désormais vides
    cleaned = _prune_empty_containers(cleaned, changes, "")

    if trace:
        return cleaned, changes  # type: ignore[return-value]
    return cleaned






