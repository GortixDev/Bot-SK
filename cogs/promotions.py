import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import ID_CATEGORIE_FICHE, LISTE_ROLES_GRADES, ROLES_STAFF, normaliser_nom_salon_fiche, salons_fiche_perso, verifier_roles

# ID du salon d'annonce des promotions
ID_SALON_PROMOTIONS_GLOBAL = 1548757881485000785

CHOICES_GRADES = [
    app_commands.Choice(name="🔧 • Prospects", value="1539031656139071530"),
    app_commands.Choice(name="🐦‍⬛ • Nomad", value="1539031656139071531"),
    app_commands.Choice(name="🛠️ • Member", value="1539031656139071532"),
    app_commands.Choice(name="🌙 • Soul Night", value="1539031656139071533"),
    app_commands.Choice(name="😡 • Ass-Kicker", value="1539031656139071534"),
    app_commands.Choice(name="🛵 • Tail-Gunner", value="1539031656139071535"),
    app_commands.Choice(name="☠️ • Soul Reaper", value="1539031656139071537"),
    app_commands.Choice(name="💪 • Enforcer", value="1539031656139071536"),
    app_commands.Choice(name="🏍️ • Road Captain", value="1539031656139071538"),
    app_commands.Choice(name="🗓️ • Secretary", value="1539031656176951317"),
    app_commands.Choice(name="💲 • Treasurer", value="1539031656176951318"),
    app_commands.Choice(name="🔫 • Sergeant At Arms", value="1553411598494867486"),
    app_commands.Choice(name="🚬 • V-Président", value="1539031656176951320"),
    app_commands.Choice(name="⚒️ • Président", value="1539031656176951321"),
]

class PromotionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="promotions", description="Promeut un membre")
    @app_commands.choices(nouveau_grade=CHOICES_GRADES)
    @verifier_roles(ROLES_STAFF)
    async def promotions(self, interaction: discord.Interaction, membre: discord.Member, nouveau_grade: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        nouveau_role = guild.get_role(int(nouveau_grade.value)) if guild else None

        if not nouveau_role:
            await interaction.followup.send("❌ Rôle introuvable.", ephemeral=True)
            return

        # Retrait des anciens grades et ajout du nouveau
        anciens_roles = [r for r in membre.roles if r.id in LISTE_ROLES_GRADES and r.id != nouveau_role.id]
        if anciens_roles:
            await membre.remove_roles(*anciens_roles)
        await membre.add_roles(nouveau_role)

        # Recherche du salon fiche perso du membre
        salon_fiche = None
        for s_id in salons_fiche_perso:
            s = guild.get_channel(s_id)
            if isinstance(s, discord.TextChannel) and s.permissions_for(membre).read_messages:
                salon_fiche = s
                break

        # Création de l'Embed au format exact
        embed_promo = discord.Embed(
            title="🎉 Félicitations !",
            description=(
                f"Bravo {membre.mention} pour ta promotion !\n\n"
                f"Tu passes au grade {nouveau_role.mention}.\n\n"
                f"Promotion effectuée par {interaction.user.mention}."
            ),
            color=discord.Color.green(),
        )
        embed_promo.set_footer(text="Félicitations pour ton nouveau grade !")
        embed_promo.timestamp = datetime.datetime.now(datetime.timezone.utc)

        # 1. Envoi dans le salon global d'annonce (Mention + Embed)
        salon_global = guild.get_channel(ID_SALON_PROMOTIONS_GLOBAL)
        if salon_global and isinstance(salon_global, discord.TextChannel):
            await salon_global.send(content=f"{membre.mention}", embed=embed_promo)

        # 2. Envoi dans le salon individuel du membre (Mention + Embed)
        if salon_fiche:
            await salon_fiche.send(content=f"{membre.mention}", embed=embed_promo)

        await interaction.followup.send(f"✅ Promotion de {membre.mention} effectuée avec succès !", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PromotionsCog(bot))
