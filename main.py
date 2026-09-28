import os
import sys
import threading
import discord
from discord.ext import commands
from flask import Flask
from config import envoyer_log

app = Flask("")

@app.route("/")
def home():
    return "Bot SK OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

class MonBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"Cog chargé : {filename[:-3]}")
        await self.tree.sync()

bot = MonBot()
deja_annonce = False

@bot.event
async def on_ready():
    global deja_annonce
    print(f"Connecté : {bot.user}")
    if not deja_annonce:
        deja_annonce = True
        await envoyer_log(
            bot,
            "🟢 Le Bot Est En Ligne",
            f"Connecté en tant que **{bot.user}**. Toutes les commandes sont opérationnelles.",
            discord.Color.green(),
        )

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CheckFailure):
        msg = "❌ Tu n'as pas le rôle requis pour utiliser cette commande."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ TOKEN MANQUANT")
        sys.exit(1)
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Erreur lors du lancement : {e}")