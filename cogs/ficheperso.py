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

        if not guild:
            await interaction.followup.send("❌ Erreur : Serveur introuvable.", ephemeral=True)
            return

        # 1. Tentative de récupération de la catégorie via le cache
        categorie_cible = guild.get_channel(ID_CATEGORIE_FICHE)

        # 2. Si non trouvée dans le cache, recherche directe auprès de l'API Discord
        if not categorie_cible:
            try:
                categorie_cible = await guild.fetch_channel(ID_CATEGORIE_FICHE)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                categorie_cible = None

        # 3. Vérification de la validité de la catégorie
        if not isinstance(categorie_cible, discord.CategoryChannel):
            await interaction.followup.send(
                f"❌ Catégorie invalide ou introuvable (ID configuré : `{ID_CATEGORIE_FICHE}`).\n"
                "Vérifiez la valeur de `ID_CATEGORIE_FICHE` dans `config.py` ainsi que les permissions du bot.",
                ephemeral=True
            )
            return

        # Configuration des permissions du salon
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            membre: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        for role_id in ROLES_FICHE_PERSO:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True,
                    manage_channels=True
                )

        # Création du salon textuel dans la catégorie
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

        # Extraction Nom / Prénom depuis le pseudo
        parties_nom = membre.display_name.split(" ", 1)
        prenom = parties_nom[0]
        nom = parties_nom[1] if len(parties_nom) > 1 else "N/A"

        # Affichage direct du rôle Prospect
        texte_roles = "<@&1539031656139071530>"

        date_recrutement = datetime.datetime.now(HEURE_FRANCE).strftime("%d/%m/%Y")

        # Message de bienvenue et fiche personnelle
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
            f"2️⃣ Choisis la catégorie de ce que tu as fait en jeu.\n"
            f"3️⃣ Dans `montant_ou_poids`, indique l'argent ou le nombre de kg que tu as sur toi.\n"
            f"4️⃣ Une fois ceci rempli, appuie sur Entrée pour valider la commande."
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
        if isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.edit(name=nom_clean)
            await interaction.followup.send(f"✅ Salon renommé en `{nom_clean}`", ephemeral=True)
        else:
            await interaction.followup.send("❌ Impossible de renommer ce salon.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(FichePersoCog(bot))
