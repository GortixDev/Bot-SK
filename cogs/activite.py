import datetime
import json
import discord
from discord import app_commands
from discord.ext import commands
from config import (
    HEURE_FRANCE, FICHIER_COMPTEUR_ACTIVITES, ID_SALON_ALERTE_ACTIVITES,
    ID_ROLE_PING_ALERTE_ACTIVITE, ROLES_ACTIVITE, ROLES_STAFF,
    salons_fiche_perso, verifier_roles
)

LIMITES_ACTIVITES = {
    "ATM": (6, "joueur"),
    "GOFAST": (6, "joueur"),
    "CAMBU": (6, "joueur"),
    "CONTENEUR": (4, "joueur"),
    "SUPPERETTE": (2, "groupe"),
    "AMMUNATION": (2, "groupe"),
}

CATEGORIES_ACTIVITE = [
    "ATM", "ATM RATE", "CAMBU", "CAMBU RATE", "GOFAST", "GOFAST RATE",
    "CONTENEUR", "CONTENEUR RATE", "SUPPERETTE", "SUPPERETTE RATE",
    "AMMUNATION", "AMMUNATION RATE", "DISQUEUSE", "DISQUEUSE RATE",
    "VENTE DE DROGUE", "VENTE DE DROGUE RATE",
]

def obtenir_jour() -> str:
    return datetime.datetime.now(HEURE_FRANCE).strftime("%Y-%m-%d")

def charger_compteur_activites() -> dict:
    if not FICHIER_COMPTEUR_ACTIVITES.exists():
        return {}
    try:
        with open(FICHIER_COMPTEUR_ACTIVITES, "r", encoding="utf-8") as f:
            donnees_brutes = json.load(f)
    except Exception as e:
        print(f"Erreur lecture compteurs : {e}")
        return {}

    donnees = {}
    for jour, contenu in donnees_brutes.items():
        donnees[jour] = {
            "joueur": {int(salon_id): cat for salon_id, cat in contenu.get("joueur", {}).items()},
            "groupe": contenu.get("groupe", {}),
        }
    return donnees

compteur_activites = charger_compteur_activites()

def sauvegarder_compteur_activites():
    try:
        with open(FICHIER_COMPTEUR_ACTIVITES, "w", encoding="utf-8") as f:
            json.dump(compteur_activites, f)
    except Exception as e:
        print(f"Erreur sauvegarde compteurs : {e}")

def nettoyer_anciens_jours():
    jour_actuel = obtenir_jour()
    if any(j != jour_actuel for j in compteur_activites.keys()):
        for j in list(compteur_activites.keys()):
            if j != jour_actuel:
                del compteur_activites[j]
        sauvegarder_compteur_activites()

def activite_est_bloquee(channel_id: int, categorie_base: str) -> bool:
    if channel_id not in salons_fiche_perso or categorie_base not in LIMITES_ACTIVITES:
        return False
    nettoyer_anciens_jours()
    limite, portee = LIMITES_ACTIVITES[categorie_base]
    jour = obtenir_jour()
    donnees_jour = compteur_activites.get(jour, {"joueur": {}, "groupe": {}})

    compte = donnees_jour.get("joueur", {}).get(channel_id, {}).get(categorie_base, 0) if portee == "joueur" else donnees_jour.get("groupe", {}).get(categorie_base, 0)
    return compte >= limite

class ActiviteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def envoyer_alerte(self, interaction, categorie, compte, limite, portee):
        salon_alerte = self.bot.get_channel(ID_SALON_ALERTE_ACTIVITES) or await self.bot.fetch_channel(ID_SALON_ALERTE_ACTIVITES)
        texte_portee = "par jour et par joueur" if portee == "joueur" else "par jour et par groupe"
        texte_blocage = "dans ce salon" if portee == "joueur" else "pour tout le monde"

        embed = discord.Embed(
            title="⚠️ Limite d'activité atteinte",
            description=(
                f"**Catégorie :** {categorie}\n"
                f"**Limite :** {limite} {texte_portee}\n"
                f"**Nombre atteint aujourd'hui :** {compte}\n"
                f"**Salon :** {interaction.channel.mention}\n"
                f"**Déclenché par :** {interaction.user.mention}\n\n"
                f"🔒 La commande `/activite` pour **{categorie}** est désormais bloquée {texte_blocage} jusqu'à demain 00h00."
            ),
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        await salon_alerte.send(
            content=f"<@&{ID_ROLE_PING_ALERTE_ACTIVITE}>",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

    async def verifier_limite(self, interaction: discord.Interaction, categorie_base: str):
        if interaction.channel_id not in salons_fiche_perso or categorie_base not in LIMITES_ACTIVITES:
            return
        nettoyer_anciens_jours()
        limite, portee = LIMITES_ACTIVITES[categorie_base]
        jour = obtenir_jour()
        donnees_jour = compteur_activites.setdefault(jour, {"joueur": {}, "groupe": {}})

        if portee == "joueur":
            salon_data = donnees_jour["joueur"].setdefault(interaction.channel_id, {})
            salon_data[categorie_base] = salon_data.get(categorie_base, 0) + 1
            compte = salon_data[categorie_base]
        else:
            donnees_jour["groupe"][categorie_base] = donnees_jour["groupe"].get(categorie_base, 0) + 1
            compte = donnees_jour["groupe"][categorie_base]

        sauvegarder_compteur_activites()
        if compte >= limite:
            await self.envoyer_alerte(interaction, categorie_base, compte, limite, portee)

    @app_commands.command(name="activite", description="Enregistre une activité")
    @app_commands.choices(type_activite=[app_commands.Choice(name=c, value=c) for c in CATEGORIES_ACTIVITE])
    @verifier_roles(ROLES_ACTIVITE)
    async def activite(self, interaction: discord.Interaction, type_activite: app_commands.Choice[str], montant_ou_poids: str | None = None):
        valeur = type_activite.value
        est_rate = valeur.endswith("RATE")
        categorie_base = valeur.replace(" RATE", "").strip()

        if activite_est_bloquee(interaction.channel_id, categorie_base):
            limite, portee = LIMITES_ACTIVITES[categorie_base]
            await interaction.response.send_message(
                f"❌ La limite quotidienne pour **{categorie_base}** ({limite} {'par joueur' if portee == 'joueur' else 'par groupe'}) est atteinte.",
                ephemeral=True,
            )
            return

        if not est_rate and not montant_ou_poids:
            await interaction.response.send_message("❌ Merci de préciser le montant ou le poids.", ephemeral=True)
            return

        desc = f"**{valeur}**\n\n**Par :** {interaction.user.mention}" if est_rate else f"**{valeur}** {montant_ou_poids}\n\n**Par :** {interaction.user.mention}"
        embed = discord.Embed(title="📌 Activité Enregistrée", description=desc, color=discord.Color.dark_gray())
        await interaction.response.send_message(embed=embed)
        await self.verifier_limite(interaction, categorie_base)

    @app_commands.command(name="reactiveractivite", description="Réactive manuellement une activité bloquée")
    @app_commands.choices(type_activite=[app_commands.Choice(name=c, value=c) for c in LIMITES_ACTIVITES.keys()])
    @verifier_roles(ROLES_STAFF)
    async def reactiveractivite(self, interaction: discord.Interaction, type_activite: app_commands.Choice[str], salon: discord.TextChannel | None = None):
        cat_base = type_activite.value
        limite, portee = LIMITES_ACTIVITES[cat_base]
        nettoyer_anciens_jours()
        jour = obtenir_jour()
        donnees_jour = compteur_activites.setdefault(jour, {"joueur": {}, "groupe": {}})

        if portee == "joueur":
            salon_cible = salon or interaction.channel
            if salon_cible.id not in salons_fiche_perso:
                await interaction.response.send_message("❌ Salon non suivi.", ephemeral=True)
                return
            donnees_jour["joueur"].get(salon_cible.id, {}).pop(cat_base, None)
            texte_cible = f"dans {salon_cible.mention}"
        else:
            donnees_jour["groupe"].pop(cat_base, None)
            texte_cible = "pour tout le monde"

        sauvegarder_compteur_activites()
        await interaction.response.send_message(f"✅ `/activite` réactivée pour **{cat_base}** {texte_cible}.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ActiviteCog(bot))