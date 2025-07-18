import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]  # 1 niveau au-dessus de scripts/

EXCLUDE_DIRS = {'.git', '__pycache__', '.venv', '.idea'}


def generate_tree(directory: str, prefix: str = '') -> list[str]:
    tree: list[str] = []
    entries = sorted(os.listdir(directory))
    for index, entry in enumerate(entries):
        if entry in EXCLUDE_DIRS:
            continue
        path = os.path.join(directory, entry)
        connector = '└── ' if index == len(entries) - 1 else '├── '
        tree.append(prefix + connector + entry)
        if os.path.isdir(path):
            extension = '    ' if index == len(entries) - 1 else '│   '
            tree.extend(generate_tree(path, prefix + extension))
    return tree


if __name__ == "__main__":
    # project_root = os.path.dirname(os.path.abspath(__file__))  # racine = dossier courant
    project_root = ROOT_DIR
    tree_lines = generate_tree(str(project_root))

    print('\n'.join(tree_lines))  # affichage console

    # Sauvegarde facultative
    with open("arborescence_oby_chat.txt", "w") as f:
        f.write('\n'.join(tree_lines))
