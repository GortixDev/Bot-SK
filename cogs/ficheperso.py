import datetime
import re
import discord
from discord import app_commands
from discord.ext import commands
from config import (
    ID_SALON_COMMANDE_FICHE, ID_CATEGORIE_FICHE, ROLES_FICHE_PERSO,
    ROLES_STAFF, HEURE_FRANCE, LISTE_ROLES_GRADES,
    salons_fiche_perso, sauvegarder_salons_fiche, verifier_roles
)

ROLES_AUTOMATIQUES_FICHE = [1539031656139071530, 1539031656076410976, 1539395768476246057]

def normaliser_nom_salon_fiche(texte: str) -> str:
    table_separateurs = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-", "－": "-", "·": "-", "•": "-", "|": "-", "/": "-", "\\": "-"})
    texte = texte.strip().translate(table_separateurs).lower().replace(" ", "-")
    texte = re.sub(r"[\r\n\t]+", "-", texte)
    return re.sub(r"-{2,}", "-", texte).strip("-")[:100].strip("-")

class FichePersoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ficheperso", description="Crée un salon de fiche perso avec les rôles automatiques")
    @verifier_roles(ROLES_STAFF)
    async def ficheperso(self, interaction: discord.Interaction, membre: discord.Member, rename: str | None = None):
        if interaction.channel_id != ID_SALON_COMMANDE_FICHE:
            await interaction.response.send_message(f"❌ À utiliser dans <#{ID_SALON_COMMANDE_FICHE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        categorie_cible = guild.get_channel(ID_CATEGORIE_FICHE) if guild else None

        if not isinstance(categorie_cible, discord.CategoryChannel):
            await interaction.followup.send("❌ Catégorie invalide.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            membre: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        for role_id in ROLES_FICHE_PERSO:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True, manage_channels=True)

        nom_salon = normaliser_nom_salon_fiche(rename) if rename else f"🔫・{normaliser_nom_salon_fiche(membre.display_name)}"
        nouveau_salon = await categorie_cible.create_text_channel(name=nom_salon, overwrites=overwrites)

        salons_fiche_perso.add(nouveau_salon.id)
        sauvegarder_salons_fiche()

        # Attribution des rôles automatiques
        for r_id in ROLES_AUTOMATIQUES_FICHE:
            r = guild.get_role(r_id)
            if r and r not in membre.roles:
                try:
                    await membre.add_roles(r)
                except Exception:
                    pass

        # Rafraîchissement des données du membre pour récupérer les rôles fraîchement ajoutés
        try:
            membre = await guild.fetch_member(membre.id)
        except Exception:
            pass

        # Extraction Nom / Prénom depuis le pseudo
        parties_nom = membre.display_name.split(" ", 1)
        prenom = parties_nom[0]
        nom = parties_nom[1] if len(parties_nom) > 1 else "N/A"

        # Détection des rôles de grades du membre
        roles_membres = [r.mention for r in membre.roles if r.id in LISTE_ROLES_GRADES]
        texte_roles = ", ".join(roles_membres) if roles_membres else "Aucun grade attribué"

        date_recrutement = datetime.datetime.now(HEURE_FRANCE).strftime("%d/%m/%Y")

        # Message complet
        contenu_message = (
            f"# 🪪 FICHE PERSONNELLE DE {membre.mention}\n\n"
            f"👤 **Nom :** {nom}\n"
            f"👤 **Prénom :** {prenom}\n"
            f"🎖️ **Rôles / Grade :** {texte_roles}\n"
            f"📅 **Date de recrutement :** {date_recrutement}\n\n"
            f"----------------------------------------\n\n"
            f"👋 **Bienvenue parmi nous {membre.mention} !**\n"
            f"Ce salon est ta fiche personnelle. Tu y trouveras l'historique de tes activités et de ton suivi.\n\n"
            f"📖 **COMMENT UTILISER LA COMMANDE `/activite` :**\n"
            f"Chaque fois que tu effectues une activité sur le serveur, tu dois la déclarer ici même :\n"
            f"1️⃣ Tape la commande `/activite` dans ce salon.\n"
            f"2️⃣ Remplis les champs requis (Type d'activité, détails, preuves si nécessaire).\n"
            f"3️⃣ Valide pour ajouter automatiquement tes points / heures à ton compteur."
        )

        await nouveau_salon.send(contenu_message)
        await interaction.followup.send(f"✅ Fiche créée : {nouveau_salon.mention}", ephemeral=True)

    @app_commands.command(name="renamesalon", description="Renomme le salon de fiche perso actuel")
    @verifier_roles(ROLES_STAFF)
    async def renamesalon(self, interaction: discord.Interaction, nouveau_nom: str):
        if interaction.channel_id not in salons_fiche_perso:
            await interaction.response.send_message("❌ Réservé aux salons fiches persos.", ephemeral=True)
            return

        nom_clean = re.sub(r"[^a-z0-9\-_]", "", nouveau_nom.lower().replace(" ", "-"))
        if not nom_clean:
            await interaction.response.send_message("❌ Nom invalide.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await interaction.channel.edit(name=nom_clean)
        await interaction.followup.send(f"✅ Salon renommé en `{nom_clean}`", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(FichePersoCog(bot))
