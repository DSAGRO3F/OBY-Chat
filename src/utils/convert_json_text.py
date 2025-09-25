# src/utils/convert_json_text.py
"""
Convertit un dossier patient au format JSON en texte libre lisible par un LLM.
Parcourt dynamiquement chaque bloc (usager, contacts, aggir, social, sante, dispositifs, poa*)
et toutes leurs sous-branches, avec un repli récursif générique pour ne rien perdre si le schéma évolue.
Normalise le texte (Unicode NFKC, “smart title” français pour MAJUSCULES), ainsi que dates, booléens et nombres.
Gère AGGIR en ne lisant que la clé 'Resultat' (sans espace) et en aplatissant variables/sous-variables/adverbes.
Supporte 0..n contacts et variabilité des champs (synonymes, listes/chaînes).

Retourne une chaîne structurée par sections.
"""

# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List
from datetime import datetime
import unicodedata
import re


Json = Dict[str, Any]

# =========================
# Helpers casse/diacritiques
# =========================

ACRONYM_RE = re.compile(r"^[A-Z0-9]{2,}$")  # conserve les sigles >= 2
SMALL_WORDS = {"de", "du", "des", "d", "la", "le", "les", "aux", "au", "et", "ou"}

def _strip_diacritics(s: str) -> str:
    """
    Enlève les diacritiques (pour comparaisons éventuelles).
    Ne pas utiliser pour l'affichage final.
    """
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def _smart_title_fr(s: str) -> str:
    """
    Met en 'Title Case' à la française :
      - Si le mot est un ACRONYME (IPA/CHU/HAS/ADMR…), on le garde en MAJ.
      - Petits mots (de/du/des/d'/la/le/les/aux/au/et/ou) en minuscules sauf
        s'ils sont en début de chaîne.
      - Gère d', l' → d’Alzon, l’Hôpital (guillemets typographiques ’).
    """
    if not s:
        return s
    tokens = re.split(r"(\s+)", s)  # on garde les espaces
    out: List[str] = []
    start = True
    for tok in tokens:
        if tok.isspace():
            out.append(tok)
            continue

        raw = tok
        # Conserver les acronymes
        if ACRONYM_RE.match(raw):
            out.append(raw)
        else:
            # gérer l’/d’ en français (d', l', D', L', d’, l’, …)
            m = re.match(r"^([dlDL])['’](.+)$", raw)
            if m:
                art, rest = m.group(1), m.group(2)
                rest_t = rest[:1].upper() + rest[1:].lower() if rest else rest
                out.append(f"{art.lower()}’{rest_t}")
                start = False
                continue

            low = raw.lower()
            if (low in SMALL_WORDS) and (not start):
                out.append(low)
            else:
                out.append(low[:1].upper() + low[1:])
        start = False
    return "".join(out)

def _looks_shouting(s: str) -> bool:
    """
    ALL CAPS: au moins 80% des lettres alpha sont majuscules.
    """
    letters = [ch for ch in s if ch.isalpha()]
    if len(letters) < 3:
        return False
    upp = sum(ch.isupper() for ch in letters)
    return (upp / len(letters)) >= 0.8

# =========================
# Helpers de normalisation
# =========================

def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def _norm_text(s: Any, *, case_mode: str = "auto", fold_spaces: bool = True) -> str:
    """
    Normalise un texte :
      - Unicode NFKC (cohérence accents/ligatures)
      - trim + collapse des espaces
      - Casse :
          case_mode='keep'  → ne touche pas à la casse
          case_mode='lower' → minuscules
          case_mode='upper' → MAJ
          case_mode='title' → Smart title FR
          case_mode='auto'  → si ALL CAPS → smart title, sinon conserve
    """
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFKC", s.strip())
    if fold_spaces:
        s = " ".join(s.split())

    if case_mode == "keep":
        return s
    if case_mode == "lower":
        return s.lower()
    if case_mode == "upper":
        return s.upper()
    if case_mode == "title":
        return _smart_title_fr(s)
    if case_mode == "auto":
        return _smart_title_fr(s) if _looks_shouting(s) else s
    return s

def _norm_bool(v: Any) -> str:
    if isinstance(v, bool):
        return "Oui" if v else "Non"
    vs = _norm_text(v).lower()
    if vs in {"true", "vrai", "oui"}:
        return "Oui"
    if vs in {"false", "faux", "non"}:
        return "Non"
    return _norm_text(v) or "Non renseigné"

def _norm_date(s: Any) -> str:
    """
    Rend YYYY-MM-DD si possible, sinon valeur normalisée.
    Accepte : YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, DD/MM/YYYY, DD/MM/YYYY HH:MM
    """
    if not s:
        return "Non renseigné"
    raw = _norm_text(s, case_mode="keep")
    fmts = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M")
    for f in fmts:
        try:
            return datetime.strptime(raw, f).date().isoformat()
        except Exception:
            pass
    return raw  # si ce n'est pas une date (ex: "1h36min"), on rend tel quel

def _norm_number(s: Any) -> str:
    """
    Normalisation souple des nombres : '33.3', '8,46', int/float → str.
    """
    if s is None or s == "":
        return "Non renseigné"
    if isinstance(s, (int, float)):
        return _norm_text(s, case_mode="keep")
    raw = _norm_text(s, case_mode="keep").replace(",", ".")
    try:
        float(raw)
        return raw
    except Exception:
        return _norm_text(s)

def _join(values: Iterable[Any], sep: str = ", ") -> str:
    parts = [_norm_text(v) for v in values if _norm_text(v)]
    return sep.join(parts) if parts else "Non renseigné"

def _pick(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Retourne la première clé présente dans d parmi keys (utile pour synonymes).
    """
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    return default

def _addr_line(adresse: Dict[str, Any]) -> str:
    if not isinstance(adresse, dict):
        return "Non renseigné"
    ligne = adresse.get("ligne")
    if isinstance(ligne, list):
        return _join([x for x in ligne if x], " ")
    if isinstance(ligne, str):
        return _norm_text(ligne)
    return "Non renseigné"

# =========================
# Rendu générique (fallback)
# =========================

def _flatten_unknown(value: Any, prefix: str = "") -> List[str]:
    """
    Dump récursif générique pour ne rien perdre si le schéma évolue :
      - dict → descend dans les clés
      - list → énumère les éléments
      - atomique → affiche la valeur
    """
    lines: List[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            key = _norm_text(k)
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_flatten_unknown(v, prefix=prefix + "  "))
            else:
                vv = _norm_text(v) or "Non renseigné"
                lines.append(f"{prefix}{key}: {vv}")
    elif isinstance(value, list):
        for i, item in enumerate(value, 1):
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}- élément {i}:")
                lines.extend(_flatten_unknown(item, prefix=prefix + "  "))
            else:
                vv = _norm_text(item) or "Non renseigné"
                lines.append(f"{prefix}- {vv}")
    else:
        vv = _norm_text(value) or "Non renseigné"
        lines.append(f"{prefix}{vv}")
    return lines

# =========================
# Sections dédiées
# =========================

def _section_usager(data: Json) -> List[str]:
    """Formate la section « usager » du dossier patient en lignes de texte.
    Extrait l’état civil, l’adresse et les coordonnées personnelles depuis
    `usager`, en gérant les variantes de schéma (ex. adresse.ligne en liste
    ou en chaîne) et en normalisant la casse/diacritiques.

    Args:
        data (Json): Dossier patient complet sous forme de dict JSON.

    Returns:
        List[str]: Lignes de texte prêtes à être concaténées pour la sortie.
    """
    lines: List[str] = ["### Présentation de la personne accompagnée"]
    usager = data.get("usager", {}) or {}
    etat_civil = (
        usager.get("Informations d'état civil", {}).get("personnePhysique", {}) or {}
    )
    adresse = usager.get("adresse", {}) or {}
    contact = usager.get("contactInfosPersonnels", {}) or {}

    lines += [
        f"- Nom : {_norm_text(_pick(etat_civil, 'nomFamille', 'nomUtilise', default='Non renseigné'), case_mode='auto')}",
        f"- Prénom : {_norm_text(_pick(etat_civil, 'prenomUtilise', 'prenom', default='Non renseigné'), case_mode='auto')}",
        f"- Sexe : {_norm_text(etat_civil.get('sexe') or 'Non renseigné', case_mode='auto')}",
        f"- Date de naissance : {_norm_date(etat_civil.get('dateNaissance'))}",
        f"- Situation familiale : {_norm_text(etat_civil.get('situationFamiliale') or 'Non renseigné', case_mode='auto')}",
        f"- Adresse : {_addr_line(adresse)}, {_norm_text(adresse.get('codePostal') or '', case_mode='keep')} {_norm_text(adresse.get('libelleCommune') or '', case_mode='auto')}".rstrip(),
        f"- Tel. domicile : {_norm_text(contact.get('domicile') or '', case_mode='keep') or 'Non renseigné'}",
        f"- Tel. mobile : {_norm_text(contact.get('mobile') or '', case_mode='keep') or 'Non renseigné'}",
        f"- Courriel : {_norm_text(_pick(contact, 'mailMSSANTE', 'mailPro', 'mail', default='Non renseigné'), case_mode='keep')}",
    ]
    return lines

def _section_contacts(data: Json) -> List[str]:
    """
    Formate la section « contacts » (0..n) en lignes de texte.
    Lit dynamiquement les contacts au niveau racine, gère l’absence éventuelle
    de contacts, normalise les champs (noms, téléphones, emails) et affiche
    un repli générique récursif pour toute sous-branche non standard.

    Args:
        data (Json): Dossier patient complet sous forme de dict JSON.

    Returns:
        List[str]: Lignes de texte prêtes à être concaténées pour la sortie.
    """

    lines: List[str] = ["", "### Contacts identifiés"]
    contacts = _as_list(data.get("contacts"))
    if not contacts:
        lines.append("- Aucun contact renseigné")
        return lines

    for i, c in enumerate(contacts, 1):
        if not isinstance(c, dict):
            lines.append(f"- Contact {i} : {_norm_text(c, case_mode='auto')}")
            continue
        pp = c.get("personnePhysique", {}) or {}
        ci = c.get("contactInfosPersonnels", {}) or {}
        adr = c.get("adresse", {}) or {}

        nom = _join([
            _norm_text(pp.get("prenomUtilise"), case_mode="auto"),
            _norm_text(pp.get("nomUtilise"), case_mode="auto"),
        ], " ")
        role = _join([
            _norm_text(c.get("role"), case_mode="auto"),
            _norm_text(c.get("natureLien"), case_mode="auto"),
            _norm_text(c.get("typeStructure"), case_mode="auto"),
        ])
        mail_any = _pick(ci, "mailMSSANTE", "mailPro", "mail", default="Non renseigné")
        tel = _join([
            _norm_text(ci.get("mobile"), case_mode="keep"),
            _norm_text(ci.get("domicile"), case_mode="keep"),
        ])

        lines += [
            f"- Contact {i} : {nom or 'Non renseigné'} ({role})",
            f"  - Téléphone : {tel}",
            f"  - Email : {_norm_text(mail_any, case_mode='keep')}",
            f"  - Adresse : {_addr_line(adr)}, {_norm_text(adr.get('codePostal') or '', case_mode='keep')} {_norm_text(adr.get('libelleCommune') or '', case_mode='auto')}".rstrip()
        ]

        # Dump générique des éventuelles sous-branches non standard
        known_keys = {"personnePhysique", "contactInfosPersonnels", "adresse", "role", "natureLien", "typeStructure", "structure", "finessET"}
        extras = {k: v for k, v in c.items() if k not in known_keys and v not in (None, "", [], {})}
        if extras:
            lines.append("  - Détails supplémentaires :")
            lines.extend(["    " + l for l in _flatten_unknown(extras)])
    return lines

def _section_aggir(data: Json) -> List[str]:
    """
    Formate la section « AGGIR » en lignes de texte prêtes à l’affichage.
    Extrait GIR, date de modification et Temps d’aide/24h, puis aplatit
    AggirVariable/SousVariable en ne lisant que la clé « Resultat » (sans espace)
    et en restituant les adverbes S/T/C/H, avec normalisation des champs.

    Args:
        data (Json): Dossier patient complet sous forme de dict JSON.

    Returns:
        List[str]: Lignes de texte pour la section AGGIR.
    """

    aggir = data.get("aggir")
    if not aggir:
        return []

    def _adverbes_str(lst: Any) -> str:
        if not lst:
            return "Adverbes S/T/C/H : – / – / – / –"
        ordered = {"S": "–", "T": "–", "C": "–", "H": "–"}
        for a in _as_list(lst):
            q = _norm_text(a.get("Question"), case_mode="keep")
            r = _norm_text(a.get("Reponse"), case_mode="keep")
            if q in ordered and r:
                ordered[q] = r
        return f"Adverbes S/T/C/H : {ordered['S']} / {ordered['T']} / {ordered['C']} / {ordered['H']}"

    lines: List[str] = ["", "### AGGIR"]
    lines.append(f"- GIR : {_norm_text(aggir.get('GIR') or 'Non renseigné', case_mode='keep')}")
    lines.append(f"- Date de modification : {_norm_text(aggir.get('dateModification') or 'Non renseigné', case_mode='keep')}")
    lines.append(f"- Temps d'aide/24h : {_norm_text(aggir.get('TempsAide24H') or 'Non renseigné', case_mode='keep')}")

    for v in _as_list(aggir.get("AggirVariable")):
        nom = _norm_text(v.get("Nom") or "(Variable)", case_mode="auto")
        res = _norm_text(v.get("Resultat") or "Non renseigné", case_mode="keep")   # <- clé sans espace uniquement
        com = _norm_text(v.get("Commentaires") or "", case_mode="auto")
        lines.append(f"\n- {nom} — Résultat : {res}")
        if com:
            lines.append(f"  Commentaires : {com}")
        lines.append(f"  {_adverbes_str(v.get('AggirAdverbes'))}")

        for sv in _as_list(v.get("AggirSousVariable")):
            snom = _norm_text(sv.get("Nom") or "(Sous-variable)", case_mode="auto")
            sres = _norm_text(sv.get("Resultat") or "Non renseigné", case_mode="keep")
            scom = _norm_text(sv.get("Commentaires") or "", case_mode="auto")
            lines.append(f"  * {snom} — Résultat : {sres}")
            if scom:
                lines.append(f"    Commentaires : {scom}")
            lines.append(f"    {_adverbes_str(sv.get('AggirAdverbes'))}")

    return lines

def _section_blocs(data: Json, section_key: str, title: str) -> List[str]:
    """
    Formate une section à blocs (ex. « social », « sante ») en lignes de texte.
    Parcourt dynamiquement `blocs[]`, restitue les paires question/réponse,
    les tests (nom, résultat, date) et les mesures éventuelles, puis applique
    un repli récursif générique pour toute sous-branche non prévue.

    Args:
        data (Json): Dossier patient complet sous forme de dict JSON.
        section_key (str): Clé top-level de la section à traiter (p. ex. "social", "sante").
        title (str): Titre d’affichage pour la section.

    Returns:
        List[str]: Lignes de texte prêtes à être concaténées pour la sortie.
    """

    sec = data.get(section_key) or {}
    blocs = _as_list(sec.get("blocs"))
    if not blocs:
        return []

    lines: List[str] = ["", f"### {title}"]
    for b in blocs:
        if not isinstance(b, dict):
            lines.append(f"- Bloc : {_norm_text(b, case_mode='auto')}")
            continue

        bnom = _norm_text(b.get("nom") or "Sans nom", case_mode="auto")
        lines.append(f"\n- Bloc : {bnom}")

        # Q/R
        for qr in _as_list(b.get("questionReponse")):
            if isinstance(qr, dict):
                q = _norm_text(qr.get("question") or "?", case_mode="auto")
                r = _norm_text(qr.get("reponse") or "Non renseigné", case_mode="auto")
                lines.append(f"  • {q} : {r}")
            else:
                lines.append(f"  • {_norm_text(qr, case_mode='auto')}")

        # Tests
        for t in _as_list(b.get("test")):
            if isinstance(t, dict):
                nom = _norm_text(t.get("nom") or "?", case_mode="auto")
                res = _norm_text(_pick(t, "resultat", "résultat", default="Non renseigné"), case_mode="keep")
                dte = _norm_date(t.get("dateTest")) if t.get("dateTest") else None
                base = f"  • Test — {nom} : {res}"
                lines.append(base if not dte else f"{base} (le {dte})")
            else:
                lines.append(f"  • Test — {_norm_text(t, case_mode='auto')}")

        # Constantes/mesures éventuelles (synonymes)
        for m in _as_list(b.get("mesureConstante")):
            if isinstance(m, dict):
                typ = _norm_text(m.get("type") or "?", case_mode="auto")
                val = _norm_text(_pick(m, "valeur", "value", default="Non renseigné"), case_mode="keep")
                unit = _norm_text(m.get("unite") or "", case_mode="keep")
                stat = _norm_text(_pick(m, "statut", "status", default=""), case_mode="auto")
                ds = _norm_date(m.get("dateSaisie")) if m.get("dateSaisie") else None
                line = f"  • Mesure — {typ} : {val}{(' ' + unit) if unit else ''}"
                if stat and stat != "Non renseigné":
                    line += f" ({stat})"
                if ds:
                    line += f" le {ds}"
                lines.append(line)
            else:
                lines.append(f"  • Mesure — {_norm_text(m, case_mode='auto')}")

        # Dump générique des sous-branches inconnues du bloc
        known = {"nom", "questionReponse", "test", "mesureConstante", "comorbidites"}
        extras = {k: v for k, v in b.items() if k not in known and v not in (None, "", [], {})}
        if extras:
            lines.append("  • Détails du bloc :")
            lines.extend(["    " + l for l in _flatten_unknown(extras)])

        # Cas spécifique : Comorbidités (si présent dans ce bloc)
        for c in _as_list(b.get("comorbidites")):
            if isinstance(c, dict):
                pairs = [f"{_norm_text(k, case_mode='auto')}: {_norm_text(v, case_mode='auto')}"
                         for k, v in c.items() if v not in (None, "", [], {})]
                if pairs:
                    lines.append("  • Comorbidité — " + " | ".join(pairs))

    return lines

def _section_dispositifs_materiels(data: Json) -> List[str]:
    """
    Formate les sections « dispositifs » et « matériels » en lignes de texte.
    Parcourt dynamiquement les listes hétérogènes (schémas variables selon les
    dossiers), extrait toutes les paires clé:valeur non vides et normalise le
    rendu pour une lecture cohérente par un LLM.

    Args:
        data (Json): Dossier patient complet sous forme de dict JSON.

    Returns:
        List[str]: Lignes de texte pour les sections Dispositifs et Matériels.
    """
    lines: List[str] = []
    items = [("Dispositifs", _as_list(data.get("dispositifs"))),
             ("Matériels", _as_list(data.get("materiels")))]
    for title, arr in items:
        if not arr:
            continue
        lines.append("")
        lines.append(f"### {title}")
        for it in arr:
            if isinstance(it, dict):
                pairs = [f"{_norm_text(k, case_mode='auto')}: {_norm_text(v, case_mode='auto')}"
                         for k, v in it.items() if v not in (None, "", [], {})]
                if pairs:
                    lines.append("- " + " | ".join(pairs))
            else:
                lines.append(f"- {_norm_text(it, case_mode='auto')}")
    return lines

def _section_poa_problemes(data: Json, key: str, title: str) -> List[str]:
    """
    Formate une section POA à « problèmes » (poaSocial/poaSante) en texte.
    Parcourt dynamiquement `problemes[]`, restitue nom de bloc, statut,
    problème posé, objectifs et préoccupations, puis détaille chaque action
    de `planActions[]` en listant toutes les paires clé=valeur pertinentes.

    Args:
        data (Json): Dossier patient complet sous forme de dict JSON.
        key (str): Clé top-level de la section à traiter (ex. "poaSocial", "poaSante").
        title (str): Titre d’affichage pour la section.

    Returns:
        List[str]: Lignes de texte prêtes à être concaténées pour la sortie.
    """

    sec = data.get(key) or {}
    probs = _as_list(sec.get("problemes"))
    if not probs:
        return []
    lines: List[str] = ["", f"### {title}"]
    for p in probs:
        if not isinstance(p, dict):
            lines.append(f"- {_norm_text(p, case_mode='auto')}")
            continue
        lines += [
            f"\n- Bloc : {_norm_text(p.get('nomBloc') or 'Sans nom', case_mode='auto')} (Statut: {_norm_text(p.get('statut') or '?', case_mode='auto')})",
            f"  • Problème : {_norm_text(p.get('problemePose') or 'Non renseigné', case_mode='auto')}",
            f"  • Objectifs : {_norm_text(p.get('objectifs') or 'Non renseigné', case_mode='auto')}",
            f"  • Préoccupation patient/professionnel : {_join([_norm_text(p.get('preoccupationPatient'), case_mode='auto'), _norm_text(p.get('preoccupationProfessionel'), case_mode='auto')], ' / ')}"
        ]
        for a in _as_list(p.get("planActions")):
            if isinstance(a, dict):
                # Affiche toutes les clés disponibles
                pairs = [f"{_norm_text(k, case_mode='auto')}={_norm_text(v, case_mode='auto')}"
                         for k, v in a.items() if v not in (None, "", [], {})]
                if pairs:
                    lines.append("  • Action : " + "; ".join(pairs))
            else:
                lines.append(f"  • Action : {_norm_text(a, case_mode='auto')}")
    return lines

def _section_poa_autonomie(data: Json) -> List[str]:
    """
    Formate la section « poaAutonomie » en lignes de texte.
    Parcourt dynamiquement `actions[]` et restitue les champs connus
    (type d’action, personnes en charge, jours, date de début, durée,
    moments, types d’aide, actions, détails), avec normalisation souple.

    Args:
        data (Json): Dossier patient complet sous forme de dict JSON.

    Returns:
        List[str]: Lignes de texte prêtes à être concaténées pour la sortie.
    """

    pa = data.get("poaAutonomie") or {}
    acts = _as_list(pa.get("actions"))
    if not acts:
        return []
    lines: List[str] = ["", "### poaAutonomie"]
    for a in acts:
        if not isinstance(a, dict):
            lines.append(f"- {_norm_text(a, case_mode='auto')}")
            continue
        # Champs connus
        lines += [
            f"\n- Type d'action : {_norm_text(a.get('typeAction') or 'Non renseigné', case_mode='auto')}",
            f"  • Personnes en charge : {_join([_norm_text(x, case_mode='auto') for x in a.get('personneChargeAction', [])])}",
            f"  • Jours d'intervention : {_join([_norm_text(x, case_mode='auto') for x in a.get('joursIntervention', [])])}",
            f"  • Début : {_norm_date(a.get('dateDebutAction'))}",
        ]
        # dureeAction : bool OU str
        dur = a.get("dureeAction")
        dur_str = _norm_bool(dur) if isinstance(dur, (bool, type(None))) else _norm_text(dur, case_mode="auto")
        lines += [
            f"  • Durée action : {dur_str or 'Non renseigné'}",
            f"  • Durée passage : {_norm_text(a.get('dureePassage') or 'Non renseigné', case_mode='keep')}",
            f"  • Moments : {_join([_norm_text(x, case_mode='auto') for x in a.get('momentJournee', [])])}",
            f"  • Type d'aide : {_join([_norm_text(x, case_mode='auto') for x in a.get('typeAide', [])])}",
            f"  • Actions : {_join([_norm_text(x, case_mode='auto') for x in a.get('actions', [])])}",
        ]
        # Champs libres
        for k in ("detailAction", "critereEvaluation", "resultatActions"):
            if k in a and a[k] not in (None, "", [], {}):
                lines.append(f"  • {_norm_text(k, case_mode='auto')} : {_norm_text(a[k], case_mode='auto')}")

        # Dump générique des éventuelles clés non listées
        known = {
            "typeAction", "personneChargeAction", "joursIntervention", "dateDebutAction",
            "dureeAction", "dureePassage", "momentJournee", "typeAide", "actions",
            "detailAction", "critereEvaluation", "resultatActions"
        }
        extras = {k: v for k, v in a.items() if k not in known and v not in (None, "", [], {})}
        if extras:
            lines.append("  • Détails de l'action :")
            lines.extend(["    " + l for l in _flatten_unknown(extras)])
    return lines

# =========================
# Point d'entrée principal
# =========================

def convert_json_to_text(data: Json) -> str:
    """
    Convertit un dossier patient au format JSON en texte libre lisible par un LLM.
    Parcourt dynamiquement chaque bloc (usager, contacts, aggir, social, sante, dispositifs, poa*)
    et toutes leurs sous-branches, avec un repli récursif générique pour ne rien perdre si le schéma évolue.
    Normalise le texte (Unicode NFKC, “smart title” français pour MAJUSCULES), ainsi que dates, booléens et nombres.
    Gère AGGIR en ne lisant que la clé 'Resultat' (sans espace) et en aplatissant variables/sous-variables/adverbes.
    Supporte 0..n contacts et variabilité des champs (synonymes, listes/chaînes).
    Retourne une chaîne structurée par sections.
    """
    lines: List[str] = []

    # 1) USAGER
    lines += _section_usager(data)

    # 2) CONTACTS
    lines += _section_contacts(data)

    # 3) AGGIR
    lines += _section_aggir(data)

    # 4) SOCIAL / 5) SANTE
    lines += _section_blocs(data, "social", "Social")
    lines += _section_blocs(data, "sante", "Santé")

    # 6) DISPOSITIFS / MATERIELS
    lines += _section_dispositifs_materiels(data)

    # 7) POA Social / 8) POA Santé / 9) POA Autonomie
    lines += _section_poa_problemes(data, "poaSocial", "poaSocial")
    lines += _section_poa_problemes(data, "poaSante", "poaSante")
    lines += _section_poa_autonomie(data)

    # 10) Dump générique final pour les clés top-level non couvertes
    known_top = {
        "usager", "contacts", "aggir", "social", "sante", "dispositifs",
        "materiels", "poaSocial", "poaSante", "poaAutonomie"
    }
    extras_top = {k: v for k, v in data.items() if k not in known_top and v not in (None, "", [], {})}
    if extras_top:
        lines.append("")
        lines.append("### Informations supplémentaires")
        lines.extend(_flatten_unknown(extras_top))

    return "\n".join(lines)




