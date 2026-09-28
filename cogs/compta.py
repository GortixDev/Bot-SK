import datetime
import re
import discord
from discord import app_commands
from discord.ext import commands
from config import ROLES_STAFF, verifier_roles

CATEGORIES = [
    "atm", "atm rate", "cambu", "cambu rate", "gofast", "go fast", "gofast rate", "go fast rate",
    "conteneur", "conteneur rate", "superrette", "supperette", "superette", "superete", "supérette",
    "superrette rate", "supperette rate", "superette rate", "supérette rate", "ammunation", "ammu",
    "ammunation rate", "ammu rate", "disqueuse", "disqueuse rate", "vente de drogue", "vente de drogue rate",
]

PATTERN_CAT = r"|".join(map(re.escape, CATEGORIES))
REGEX_CAT = re.compile(PATTERN_CAT, re.IGNORECASE)
REGEX_CHIFFRES = re.compile(r"\d+")

async def obtenir_calculs_semaine(channel):
    maintenant = datetime.datetime.now(datetime.timezone.utc)
    lundi_courant = (maintenant - datetime.timedelta(days=maintenant.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    total_argent, total_kg = 0, 0

    async for message in channel.history(limit=200, after=lundi_courant):
        texte = message.content
        for embed in message.embeds:
            if embed.description:
                texte += "\n" + embed.description

        for ligne in texte.splitlines():
            if REGEX_CAT.search(ligne):
                nombres = [int(n) for n in REGEX_CHIFFRES.findall(ligne)]
                if "kg" in ligne.lower():
                    total_kg += sum(nombres)
                else:
                    total_argent += sum(nombres)

    return total_argent, total_kg

class ComptaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="salaire", description="Affiche le total en $ et en kg pour la semaine")
    @verifier_roles(ROLES_STAFF)
    async def salaire(self, interaction: discord.Interaction):
        await interaction.response.defer()
        total_argent, total_kg = await obtenir_calculs_semaine(interaction.channel)

        if total_argent == 0 and total_kg == 0:
            await interaction.followup.send("Aucune donnée valide trouvée pour cette semaine.", ephemeral=True)
            return

        embed = discord.Embed(title="💼 Récapitulatif de la semaine", color=discord.Color.dark_gray(), timestamp=datetime.datetime.now(datetime.timezone.utc))
        embed.add_field(name="💰 Total argent", value=f"{total_argent:,}$".replace(",", " "), inline=True)
        embed.add_field(name="📦 Total poids", value=f"{total_kg:,} kg".replace(",", " "), inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="compta", description="Génère la fiche de comptabilité officielle")
    @verifier_roles(ROLES_STAFF)
    async def compta(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.response.defer()
        total_argent, total_kg = await obtenir_calculs_semaine(interaction.channel)

        if total_argent == 0 and total_kg == 0:
            await interaction.followup.send("Aucun montant ou kg trouvé pour calculer la compta.", ephemeral=True)
            return

        message_compta = (
            f"**__🐦‍⬛ Souls Knight 🐦‍⬛__**\n\n"
            f"**Compta :**\n\n"
            f"**Bénéfice argent :** {total_argent:,}$".replace(",", " ") + "\n"
            f"**Bénéfice poids :** {total_kg:,} kg".replace(",", " ") + "\n\n"
            f"**Cordialement,**\n<@&1539031656176951318>\n\n"
            f"**Pour :** {membre.mention}"
        )
        await interaction.followup.send(message_compta)

async def setup(bot: commands.Bot):
    await bot.add_cog(ComptaCog(bot))