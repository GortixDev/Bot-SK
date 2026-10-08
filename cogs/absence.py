import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import HEURE_FRANCE, LISTE_ROLES_GRADES, ID_ROLE_SECRETARY

class FormulaireAbsence(discord.ui.Modal, title="Déclaration d'absence"):
    def __init__(self, role_mention: str, auteur: discord.Member):
        super().__init__()
        self.role_mention = role_mention
        self.auteur = auteur

    date_depart = discord.ui.TextInput(
        label="Date De Départ",
        placeholder="Ex : 25/08/2026",
        default=datetime.datetime.now(HEURE_FRANCE).strftime("%d/%m/%Y"),
        required=True,
    )
    date_retour = discord.ui.TextInput(
        label="Date De Retour", 
        placeholder="Ex : 30/08/2026", 
        required=True
    )
    raison = discord.ui.TextInput(
        label="Raison De L'absence", 
        style=discord.TextStyle.paragraph, 
        placeholder="Précisez le motif de votre absence...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Création d'un Embed au rendu propre
        embed = discord.Embed(
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        embed.description = (
            f"**Nom Prénom :** {self.auteur.mention}\n"
            f"**Grade :** {self.role_mention}\n"
            f"**Date De Départ :** {self.date_depart.value}\n"
            f"**Date De Retour :** {self.date_retour.value}\n"
            f"**Raison De L'absence :** {self.raison.value}\n\n"
            f"**Cordialement,**\n<@&{ID_ROLE_SECRETARY}>"
        )
        
        if self.auteur.avatar:
            embed.set_author(name=self.auteur.display_name, icon_url=self.auteur.avatar.url)

        # Envoi de l'embed dans le salon
        await interaction.channel.send(embed=embed)
        
        # Confirmation éphémère pour l'utilisateur
        await interaction.response.send_message("✅ Déclaration d'absence envoyée !", ephemeral=True)

class AbsenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def grade_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if not interaction.guild:
            return []

        choices = []
        for role_id in LISTE_ROLES_GRADES:
            role = interaction.guild.get_role(role_id)
            if role:
                if current.lower() in role.name.lower():
                    choices.append(app_commands.Choice(name=role.name, value=str(role.id)))

        return choices[:25]

    @app_commands.command(name="absence", description="Déclarer une absence via un formulaire")
    @app_commands.autocomplete(grade=grade_autocomplete)
    @app_commands.describe(grade="Tape le nom de ton grade pour le chercher")
    async def absence(self, interaction: discord.Interaction, grade: str):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Commande utilisable uniquement sur un serveur.", ephemeral=True)
            return

        role_mention = f"<@&{grade}>"
        await interaction.response.send_modal(FormulaireAbsence(role_mention, interaction.user))

async def setup(bot: commands.Bot):
    await bot.add_cog(AbsenceCog(bot))
