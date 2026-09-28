import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from config import ROLES_SUPP, verifier_roles

class SuppCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="supp", description="Supprime un nombre précis de messages dans le salon")
    @app_commands.describe(nombre="Nombre de messages à supprimer (ex: 5, 10, 50)")
    @verifier_roles(ROLES_SUPP)
    async def supp(self, interaction: discord.Interaction, nombre: int):
        if nombre <= 0:
            await interaction.response.send_message("Veuillez indiquer un nombre supérieur à 0.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        nombre_a_supprimer = min(nombre, 100)
        deleted = await interaction.channel.purge(limit=nombre_a_supprimer)

        await interaction.followup.send(f"✅ **{len(deleted)} message(s)** supprimé(s).", ephemeral=True)
        await asyncio.sleep(2)
        await interaction.delete_original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(SuppCog(bot))