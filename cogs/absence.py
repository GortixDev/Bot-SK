import asyncio
import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import HEURE_FRANCE, LISTE_ROLES_GRADES

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
    date_retour = discord.ui.TextInput(label="Date De Retour", placeholder="Ex : 30/08/2026", required=True)
    raison = discord.ui.TextInput(label="Raison De L'absence", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message_absence = (
            f"**Nom Prénom :** {self.auteur.mention}\n"
            f"**Grade :** {self.role_mention}\n"
            f"**Date De Départ :** {self.date_depart.value}\n"
            f"**Date De Retour :** {self.date_retour.value}\n"
            f"**Raison De L'absence :** {self.raison.value}\n\n"
            f"**Cordialement,**\n<@&1539031656176951317>"
        )
        await interaction.channel.send(message_absence)
        await interaction.followup.send("✅ Déclaration d'absence envoyée !", ephemeral=True)
        await asyncio.sleep(2)
        await interaction.delete_original_response()

class SelectGradeView(discord.ui.View):
    def __init__(self, guild: discord.Guild, auteur: discord.Member):
        super().__init__(timeout=60)
        self.auteur = auteur
        options = []
        for role_id in LISTE_ROLES_GRADES:
            role = guild.get_role(role_id)
            if role:
                options.append(discord.SelectOption(label=role.name, value=str(role.id)))
        if not options:
            options.append(discord.SelectOption(label="Aucun rôle trouvé", value="0"))

        self.select = discord.ui.Select(placeholder="Choisis ton grade...", min_values=1, max_values=1, options=options[:25])
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        role_id = self.select.values[0]
        role_mention = f"<@&{role_id}>"
        await interaction.response.send_modal(FormulaireAbsence(role_mention, self.auteur))

class AbsenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="absence", description="Déclarer une absence via un formulaire")
    async def absence(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Commande utilisable uniquement sur un serveur.", ephemeral=True)
            return

        view = SelectGradeView(interaction.guild, interaction.user)
        await interaction.response.send_message("Sélectionne ton grade ci-dessous :", view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AbsenceCog(bot))