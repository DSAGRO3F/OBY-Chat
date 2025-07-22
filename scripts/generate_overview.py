"""

Script de génération automatique du fichier 'overview.md' à partir de 'tools.md'.

Ce script parcourt le fichier Markdown `tools.md`, repère les blocs de description
associés à chaque module Python (définis entre balises `<!--- ... --->` juste avant chaque bloc `::: module.nom`),
et génère une documentation synthétique et lisible dans le fichier `overview.md`.

La documentation générée présente pour chaque module :
- Son nom (ex. : `data.get_constants`)
- Un encadré de description extraite depuis `tools.md`

Ce script est destiné à automatiser la création de la documentation générale du projet
et s'intègre dans le système de documentation statique utilisé par MkDocs.

Lancement :
    $ python scripts/generate_overview.py

Dépendances :
- Le fichier `config/config.py` doit contenir les variables :
    TOOLS_MD_PATH : chemin vers le fichier source `tools.md`
    OVERVIEW_MD_PATH : chemin de sortie vers le fichier généré `overview.md`
"""



# scripts/generate_overview.py

from pathlib import Path
import re
from config.config import TOOLS_MD_PATH, OVERVIEW_MD_PATH


def extract_module_descriptions(tools_md_path: Path) -> list[tuple[str, str]]:
    """
    Extrait les noms de modules et leurs descriptions depuis tools.md.

    Args:
        tools_md_path (Path): Chemin vers le fichier tools.md

    Returns:
        list of tuples: [(nom_du_module, description associée), ...]
    """
    content = tools_md_path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"<!---\s*(.*?)\s*--->\s*\n+::: ([\w\.]+)", re.DOTALL
    )

    results = []
    for match in pattern.finditer(content):
        description, module_name = match.groups()
        results.append((module_name.strip(), description.strip()))
    return results


def generate_overview_md(module_infos: list[tuple[str, str]], output_path: Path) -> None:
    """
    Génère le fichier overview.md structuré à partir des descriptions de modules.

    Args:
        module_infos (list): Liste de tuples (module_name, description)
        output_path (Path): Chemin du fichier output overview.md
    """
    lines = [
        "# 🧭 Vue d'ensemble des modules du projet OBY-Chat\n",
        "_Cette page fournit une description concise des principaux modules Python du projet._\n",
        "---\n\n"
    ]

    for module, desc in module_infos:
        lines.append(f"## 📄 Module : `{module}`\n")
        lines.append(f"> **Rôle :**\n> {desc.replace(chr(10), '\n> ')}\n")
        lines.append("---\n\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[✅] overview.md généré avec succès → {output_path}")


if __name__ == "__main__":
    modules = extract_module_descriptions(TOOLS_MD_PATH)
    generate_overview_md(modules, OVERVIEW_MD_PATH)
