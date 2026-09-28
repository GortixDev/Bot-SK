import datetime
import json
import discord
from discord import app_commands
from discord.ext import commands
from config import FICHIER_COFFRE, HEURE_FRANCE, ROLES_STAFF, envoyer_log, verifier_roles

def charger_coffre() -> dict:
    if not FICHIER_COFFRE.exists():
        return {"stock": {}, "historique": []}
    try:
        with open(FICHIER_COFFRE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"stock": {}, "historique": []}

def sauvegarder_coffre(donnees: dict):
    try:
        with open(FICHIER_COFFRE, "w", encoding="utf-8") as f:
            json.dump(donnees, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur sauvegarde coffre : {e}")

class ArmurerieCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ajout", description="Ajoute une nouvelle arme au registre du MC")
    @verifier_roles(ROLES_STAFF)
    async def ajout(self, interaction: discord.Interaction, nom_arme: str, categorie: str | None = None):
        donnees = charger_coffre()
        stock = donnees.setdefault("stock", {})
        nom_clean = nom_arme.strip().upper()

        if nom_clean in stock:
            await interaction.response.send_message(f"⚠️ **{nom_clean}** existe déjà.", ephemeral=True)
            return

        stock[nom_clean] = 0
        sauvegarder_coffre(donnees)

        embed = discord.Embed(title="➕ Arme ajoutée", description=f"**{nom_clean}** enregistrée.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        await envoyer_log(self.bot, "ARMURERIE MC - AJOUT", f"Arme : {nom_clean}", discord.Color.blue())

    @app_commands.command(name="arme", description="Gérer les mouvements d'armes dans le coffre")
    @app_commands.choices(action=[
        app_commands.Choice(name="📥 Déposer au coffre", value="DEPOT"),
        app_commands.Choice(name="📤 Prendre du coffre", value="RETRAIT"),
        app_commands.Choice(name="💀 Arme perdue / saisie", value="PERTE"),
    ])
    @verifier_roles(ROLES_STAFF)
    async def arme(self, interaction: discord.Interaction, action: app_commands.Choice[str], arme: str, quantite: int, motif: str | None = None):
        if quantite <= 0:
            await interaction.response.send_message("❌ Quantité invalide.", ephemeral=True)
            return

        donnees = charger_coffre()
        stock, historique = donnees.setdefault("stock", {}), donnees.setdefault("historique", [])
        nom_arme, type_action = arme.strip().upper(), action.value

        if type_action in ["RETRAIT", "PERTE"]:
            if stock.get(nom_arme, 0) < quantite:
                await interaction.response.send_message(f"❌ Stock insuffisant pour **{nom_arme}**.", ephemeral=True)
                return
            stock[nom_arme] -= quantite
        else:
            stock[nom_arme] = stock.get(nom_arme, 0) + quantite

        historique.append({
            "date": datetime.datetime.now(HEURE_FRANCE).strftime("%Y-%m-%d %H:%M"),
            "action": type_action,
            "membre": interaction.user.display_name,
            "arme": nom_arme,
            "quantite": quantite,
            "motif": motif or "Non précisé",
        })
        sauvegarder_coffre(donnees)

        await interaction.response.send_message(f"✅ Operation **{type_action}** enregistrée pour **{nom_arme}** (x{quantite}).")

    @app_commands.command(name="coffre", description="Affiche l'état du coffre d'armes")
    @verifier_roles(ROLES_STAFF)
    async def coffre(self, interaction: discord.Interaction):
        donnees = charger_coffre()
        stock = donnees.get("stock", {})
        embed = discord.Embed(title="🔫 Coffre d'Armes", color=discord.Color.dark_red())
        embed.description = "\n".join([f"• **{a}** : `{q}` en stock" for a, q in sorted(stock.items())]) if stock else "Coffre vide."
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="historique_armes", description="Affiche les 10 derniers mouvements")
    @verifier_roles(ROLES_STAFF)
    async def historique_armes(self, interaction: discord.Interaction):
        donnees = charger_coffre()
        historique = list(reversed(donnees.get("historique", [])))[:10]
        embed = discord.Embed(title="📜 Historique Armes", color=discord.Color.dark_gray())
        embed.description = "\n".join([f"• **[{log['date']}]** `{log['action']}` par **{log['membre']}** : {log['arme']} (x{log['quantite']})" for log in historique]) if historique else "Aucun historique."
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ArmurerieCog(bot))