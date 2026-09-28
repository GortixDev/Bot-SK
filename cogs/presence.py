import asyncio
import datetime
import re
import discord
from discord import app_commands
from discord.ext import commands
from config import HEURE_FRANCE, ROLES_PRESENCE, ROLES_MODIFIER_PRESENCE, verifier_roles, utilisateur_a_role

def construire_message_presence(motif: str, date: str, heure: str, lieu: str) -> str:
    return (
        "**<@&1539031656076410976>**\n\n"
        "**Qui sera présent ?**\n\n"
        f"**Motif : {motif}**\n\n"
        "**✅ Je serais à l'heure ( aucun retard toléré )**\n\n"
        "**⌛ Je serais présent mais avec du retard**\n\n"
        "**❌ Je ne serais pas là de la soirée**\n\n"
        f"**{date} - {heure} - {lieu}**\n\n"
        "**Cordialement,**\n<@&1539031656176951317>\n\u200b"
    )

REGEX_PRESENCE_MOTIF = re.compile(r"\*\*Motif\s*:\s*(.+?)\*\*")
REGEX_PRESENCE_DETAILS = re.compile(r"\*\*(.+?) - (.+?) - (.+?)\*\*\n\n\*\*Cordialement")

def extraire_donnees_presence(contenu: str) -> tuple[str, str, str, str]:
    match_motif = REGEX_PRESENCE_MOTIF.search(contenu)
    motif = match_motif.group(1).strip() if match_motif else ""

    match_details = REGEX_PRESENCE_DETAILS.search(contenu)
    if match_details:
        date, heure, lieu = (v.strip() for v in match_details.groups())
    else:
        date = datetime.datetime.now(HEURE_FRANCE).strftime("%d/%m/%Y")
        heure = "21h00"
        lieu = "TOUS au CH. (côté bat)"

    return motif, date, heure, lieu

class ModifierPresenceModal(discord.ui.Modal, title="Modifier la présence"):
    def __init__(self, message: discord.Message, motif: str, date: str, heure: str, lieu: str):
        super().__init__()
        self.message = message
        self.champ_motif = discord.ui.TextInput(label="Motif", default=motif, required=True, max_length=200)
        self.champ_date = discord.ui.TextInput(label="Date", default=date, required=True, max_length=50)
        self.champ_heure = discord.ui.TextInput(label="Heure", default=heure, required=True, max_length=50)
        self.champ_lieu = discord.ui.TextInput(label="Lieu", default=lieu, required=True, max_length=200)

        self.add_item(self.champ_motif)
        self.add_item(self.champ_date)
        self.add_item(self.champ_heure)
        self.add_item(self.champ_lieu)

    async def on_submit(self, interaction: discord.Interaction):
        nouveau_contenu = construire_message_presence(
            self.champ_motif.value, self.champ_date.value, self.champ_heure.value, self.champ_lieu.value
        )
        try:
            await self.message.edit(content=nouveau_contenu)
            await interaction.response.send_message("✅ Message de présence mis à jour !", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : `{e}`", ephemeral=True)

class PresenceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✏️ Modifier", style=discord.ButtonStyle.secondary, custom_id="presence_bouton_modifier")
    async def modifier(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not utilisateur_a_role(interaction.user, ROLES_MODIFIER_PRESENCE):
            await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
            return

        motif, date, heure, lieu = extraire_donnees_presence(interaction.message.content)
        await interaction.response.send_modal(ModifierPresenceModal(interaction.message, motif, date, heure, lieu))

class PresenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="presence", description="Génère le message de prise de présence")
    @app_commands.describe(
        motif="Préciser le motif de la soirée",
        date="Date du rendez-vous",
        heure="Heure du rendez-vous",
        lieu="Lieu du rendez-vous"
    )
    @verifier_roles(ROLES_PRESENCE)
    async def presence(
        self,
        interaction: discord.Interaction,
        motif: str,
        date: str | None = None,
        heure: str = "21h00",
        lieu: str = "TOUS au CH. (côté bat)",
    ):
        await interaction.response.defer(ephemeral=True)
        date_effective = date or datetime.datetime.now(HEURE_FRANCE).strftime("%d/%m/%Y")
        msg_text = construire_message_presence(motif, date_effective, heure, lieu)

        try:
            msg = await interaction.channel.send(msg_text, view=PresenceView())
            for emoji in ("✅", "⌛", "❌"):
                await msg.add_reaction(emoji)
            await interaction.followup.send("✅ Message de présence envoyé !", ephemeral=True)
            await asyncio.sleep(2)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"Erreur présence : {e}")

async def setup(bot: commands.Bot):
    bot.add_view(PresenceView())
    await bot.add_cog(PresenceCog(bot))