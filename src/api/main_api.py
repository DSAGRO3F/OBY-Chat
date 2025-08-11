# src/api/main_api.py

"""point d’entrée du serveur FastAPI. main_api.py a pour rôle de :
Créer l’objet FastAPI()
Importer et inclure les routes (chat, login, logout…)
Définir la configuration de CORS (permet d’autoriser les appels depuis l’interface OBY)
Ajouter éventuellement des middlewares (authentification, logs, etc.)
"""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import des routeurs définis dans d'autres fichiers
from src.api.routes import chat, login, logout, status, export, poa_patients

# Création de l'application FastAPI
app = FastAPI(
    title="OBY-IA API",
    description="Service d'intelligence artificielle pour OBY, accessible par API",
    version="1.0.0"
)

# Configuration CORS pour permettre à l'interface OBY d'accéder à cette API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod : remplacer par ["https://oby.fr"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des différentes routes (modules séparés)
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(login.router, prefix="/auth", tags=["auth"])
app.include_router(logout.router, prefix="/auth", tags=["auth"])
app.include_router(status.router, prefix="/status", tags=["status"])
app.include_router(export.router, prefix="/chat", tags=["export"])
app.include_router(poa_patients.router, prefix="/admin", tags=["patients"])
app.mount("/static", StaticFiles(directory="outputs"), name="static")

