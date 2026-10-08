import datetime
import json
import os
import re
from pathlib import Path
from zoneinfo import ZoneInfo
import discord
from discord import app_commands

HEURE_FRANCE = ZoneInfo("Europe/Paris")

# --- Webhook & Logs ---
WEBHOOK_LOGS_URL = os.environ.get("WEBHOOK_LOGS_URL", "https://discord.com/api/webhooks/TES_IDENTIFIANTS_ICI")

# --- IDs Salons & Catégories ---
ID_SALON_LOGS = 1541572348396703805
ID_ROLE_BOT_MENTION = 1540841034672513206
ID_CATEGORIE_FICHE = 1539031656076410976
ID_SALON_COMMANDE_FICHE = 1542856179435307076
ID_SALON_ALERTE_ACTIVITES = 1542837467709833286
ID_ROLE_PING_ALERTE_ACTIVITE = 1539031656076410976

# Mis à jour avec le rôle pour la signature Cordialement
ID_ROLE_SECRETARY = 1435681997057163364

# --- Fichiers & Données ---
DOSSIER_DATA = Path("data")
DOSSIER_DATA.mkdir(exist_ok=True)
FICHIER_SALONS_FICHE = DOSSIER_DATA / "salons_fiche_perso.json"
FICHIER_COMPTEUR_ACTIVITES = DOSSIER_DATA / "compteur_activites.json"
FICHIER_COFFRE = DOSSIER_DATA / "coffre_armes.json"

SALONS_FICHE_PERSO_INITIAUX = [
    1540828787451633674, 1540829679425028166, 1540829737113624576,
    1540829770609197107, 1540830458483314748, 1540830281848848505,
    1540830423746085037, 1541556456942473316, 1541907647677337640,
]

SALONS_FIXES_CATEGORIE = {
    1541578207340535858, 1540833171589963848, 1542856179435307076,
    1542837467709833286, 1542837521807966279,
}

# --- Rôles ---
ROLES_ACTIVITE = {1539031656076410976}
ROLES_STAFF = {
    1539031656076410974, 1539031656076410973, 1539031656139071533,
    1539031656076410978, 1539031656076410977, 1539031656176951319,
}
ROLES_SUPP = {1539031656176951321, 1539031656176951320, 1539031656176951319}
ROLES_PRESENCE = {1539031656176951321, 1539031656176951320, 1539031656176951317, 1539031656176951319}
ROLES_MODIFIER_PRESENCE = {1539031656176951321, 1539031656176951320, 1539031656176951319}

ROLES_FICHE_PERSO = [
    1540842755939635261, 1539031656076410974, 1539031656076410973,
    1539031656139071533, 1539031656076410979, 1539031656076410978,
    1539031656076410977, 1539045111105720352,
]

# Liste complète des grades mis à jour
LISTE_ROLES_GRADES = [
    1435681997057163364,  # 🌟・Maréchal
    1435686815330996224,  # ⭐⭐⭐⭐⭐️・Général d'armée
    1435686937548820652,  # ⭐⭐⭐️⭐・Général de corps d'armée
    1435686942665609256,  # ⭐⭐️⭐・Général de Division
    1435686948034314321,  # ⭐⭐️・Général de Brigade
    1435686954133094502,  # 🟢・Colonel
    1435686958541049867,  # 🟢・Lieutenant-Colonel
    1435686962882412554,  # 🟢・Commandant
    1435686967152214036,  # 🟢・Capitaine
    1435686971333804193,  # 🟢・Lieutenant
    1435686975003693086,  # 🟢・Sous-Lieutenant
    1435686978522710066,  # 🟢・Aspirant
    1435686983770046545,  # 🟡・Major
    1435686988035653702,  # 🟡・Adjudant-Chef
    1435686992095740044,  # 🟡・Adjudant
    1435686996281659525,  # 🟡・Sergent-Chef BM2
    1435687000509513800,  # 🟡・Sergent
    1435687004774858762,  # 🔘・Caporal-Chef 1ʳᵉ Classe
    1435687009774469273,  # 🔘・Caporal-Chef
    1435687014157521047,  # 🔘・Caporal
    1435687017441919026,  # 🔘・Soldat 1ʳᵉ classe
    1435687023305298002,  # 🔘・Soldat
]

def charger_salons_fiche() -> set[int]:
    salons = set(SALONS_FICHE_PERSO_INITIAUX)
    if FICHIER_SALONS_FICHE.exists():
        try:
            with open(FICHIER_SALONS_FICHE, "r", encoding="utf-8") as f:
                salons.update(json.load(f))
        except Exception as e:
            print(f"Erreur lecture salons fiches : {e}")
    return salons

salons_fiche_perso: set[int] = charger_salons_fiche()

def sauvegarder_salons_fiche():
    try:
        with open(FICHIER_SALONS_FICHE, "w", encoding="utf-8") as f:
            json.dump(sorted(salons_fiche_perso), f)
    except Exception as e:
        print(f"Erreur sauvegarde salons fiches : {e}")

def normaliser_nom_salon_fiche(nom: str) -> str:
    nom_nettoye = nom.lower().strip()
    nom_nettoye = re.sub(r"[^\w\s-]", "", nom_nettoye)
    return re.sub(r"[-\s]+", "-", nom_nettoye)

def utilisateur_a_role(membre: discord.Member, roles_autorises) -> bool:
    if membre.guild_permissions.administrator:
        return True
    return any(role.id in roles_autorises for role in membre.roles)

def verifier_roles(roles_autorises):
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        return utilisateur_a_role(interaction.user, roles_autorises)
    return app_commands.check(predicate)

async def envoyer_log(bot, title, description, color):
    channel_logs = bot.get_channel(ID_SALON_LOGS)
    if not channel_logs:
        try:
            channel_logs = await bot.fetch_channel(ID_SALON_LOGS)
        except Exception as e:
            print(f"Salon de logs introuvable : {e}")
            return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    try:
        await channel_logs.send(embed=embed)
    except Exception as e:
        print(f"Erreur d'envoi du log : {e}")
