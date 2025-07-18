"""
Module de sérialisation et désérialisation de graphiques Plotly.

Permet d’encoder les objets graphiques en base64 pour stockage ou transmission,
et de les décoder pour affichage ultérieur dans l'application.
"""




import base64
import pickle

def serialize_figs(figs):
    """
    Sérialise une liste de figures Plotly en chaînes base64.

    Utilise pickle pour convertir chaque figure en bytes,
    puis encode en base64 pour un stockage ou transfert sécurisé.

    Args:
        figs (list): Liste d'objets Plotly (go.Figure ou px.Figure).

    Returns:
        list: Liste de chaînes encodées en base64.
    """
    return [base64.b64encode(pickle.dumps(fig)).decode("utf-8") for fig in figs]

def deserialize_figs(serialized_figs):
    """
     Désérialise une liste de chaînes base64 en objets Plotly.

     Utilise base64 pour décoder les chaînes, puis pickle pour reconstruire les objets.

     Args:
         serialized_figs (list): Liste de chaînes encodées en base64.

     Returns:
         list: Liste d’objets Plotly reconstruits.
     """

    if not serialized_figs:
        return []
    return [pickle.loads(base64.b64decode(fig_str)) for fig_str in serialized_figs]

