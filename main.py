import os
import sys
import asyncio
from flask import Flask
import discord
from discord.ext import commands
from config import envoyer_log

app = Flask("")

@app.route("/")
def home():
    return "Bot SK OK", 200

async def run_flask():
    # Sur Render, il faut écouter sur 0.0.0.0 et sur le port fourni par $PORT
    port = int(os.environ.get("PORT", 10000))
    config = WerkzeugConfig() if False else None
    # Lancement du serveur Web léger sans bloquer la boucle Discord
    from werkzeug.serving import run_simple
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: run_simple("0.0.0.0", port, app, use_reloader=False, threaded=True))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

class MonBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Lancement du serveur web Flask en tâche d'arrière-plan
        self.loop.create_task(run_flask())

        # Chargement des Cogs
        if os.path.exists("./cogs"):
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    try:
                        await self.load_extension(f"cogs.{filename[:-3]}")
                        print(f"✅ Cog chargé : {filename[:-3]}")
                    except Exception as e:
                        print(f"❌ Erreur lors du chargement de cogs/{filename}: {e}")
        
        # Synchronisation des commandes slash
        try:
            synced = await self.tree.sync()
            print(f"✅ Synchronisé {len(synced)} commande(s) slash.")
        except Exception as e:
            print(f"❌ Erreur lors de la synchronisation des commandes : {e}")

bot = MonBot()

@bot.event
async def on_ready():
    print(f"🤖 Connecté en tant que : {bot.user}")
    await envoyer_log(
        bot,
        "🔄 Redémarrage / Connexion du Bot",
        f"Le bot **{bot.user}** vient de démarrer et toutes les commandes sont opérationnelles.",
        discord.Color.blue(),
    )

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CheckFailure):
        msg = "❌ Tu n'as pas le rôle requis pour utiliser cette commande."
    else:
        msg = f"❌ Une erreur est survenue lors de l'exécution : {error}"
        print(f"Erreur AppCommand: {error}")

    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except Exception as e:
        print(f"Impossible d'envoyer le message d'erreur : {e}")

if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ TOKEN MANQUANT")
        sys.exit(1)
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Erreur lors du lancement : {e}")
