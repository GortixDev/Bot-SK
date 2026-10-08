import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import (
    ID_CATEGORIE_FICHE, LISTE_ROLES_GRADES, ROLES_STAFF, 
    normaliser_nom_salon_fiche, salons_fiche_perso, verifier_roles
)

ID_SALON_PROMOTIONS_GLOBAL = 1435750825304784926

CHOICES_GRADES = [
    app_commands.Choice(name="🔘・Soldat", value="1435687023305298002"),
    app_commands.Choice(name="🔘・Soldat 1ʳᵉ classe", value="1435687017441919026"),
    app_commands.Choice(name="🔘・Caporal", value="1435687014157521047"),
    app_commands.Choice(name="🔘・Caporal-Chef", value="1435687009774469273"),
    app_commands.Choice(name="🔘・Caporal-Chef 1ʳᵉ Classe", value="1435687004774858762"),
    app_commands.Choice(name="🟡・Sergent", value="1435687000509513800"),
    app_commands.Choice(name="🟡・Sergent-Chef BM2", value="1435686996281659525"),
    app_commands.Choice(name="🟡・Adjudant", value="1435686992095740044"),
    app_commands.Choice(name="🟡・Adjudant-Chef", value="1435686988035653702"),
    app_commands.Choice(name="🟡・Major", value="1435686983770046545"),
    app_commands.Choice(name="🟢・Aspirant", value="1435686978522710066"),
    app_commands.Choice(name="🟢・Sous-Lieutenant", value="1435686975003693086"),
    app_commands.Choice(name="🟢・Lieutenant", value="1435686971333804193"),
    app_commands.Choice(name="🟢・Capitaine", value="1435686967152214036"),
    app_commands.Choice(name="🟢・Commandant", value="1435686962882412554"),
    app_commands.Choice(name="🟢・Lieutenant-Colonel", value="1435686958541049867"),
    app_commands.Choice(name="🟢・Colonel", value="1435686954133094502"),
    app_commands.Choice(name="⭐⭐️・Général de Brigade", value="1435686948034314321"),
    app_commands.Choice(name="⭐⭐️⭐・Général de Division", value="1435686942665609256"),
    app_commands.Choice(name="⭐⭐⭐️⭐・Général de corps d'armée", value="1435686937548820652"),
    app_commands.Choice(name="⭐⭐⭐⭐⭐️・Général d'armée", value="1435686815330996224"),
    app_commands.Choice(name="🌟・Maréchal", value="1435681997057163364"),
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

        if not guild:
            await interaction.followup.send("❌ Serveur introuvable.", ephemeral=True)
            return

        # Rafraîchissement direct du membre depuis Discord pour éviter les problèmes de cache
        try:
            membre = await guild.fetch_member(membre.id)
        except Exception:
            pass

        nouveau_role = guild.get_role(int(nouveau_grade.value))
        if not nouveau_role:
            await interaction.followup.send("❌ Rôle introuvable.", ephemeral=True)
            return

        # 1. Extraction exacte des anciens rôles de grade à supprimer
        roles_a_retirer = [
            role for role in membre.roles 
            if role.id in LISTE_ROLES_GRADES and role.id != nouveau_role.id
        ]

        # 2. Retrait des anciens rôles
        if roles_a_retirer:
            try:
                await membre.remove_roles(*roles_a_retirer)
            except Exception as e:
                print(f"Erreur retrait anciens rôles : {e}")

        # 3. Ajout du nouveau rôle
        try:
            await membre.add_roles(nouveau_role)
        except Exception as e:
            await interaction.followup.send(f"❌ Impossible d'ajouter le rôle : {e}", ephemeral=True)
            return

        # 4. Recherche du salon fiche perso
        salon_fiche = None
        for s_id in salons_fiche_perso:
            s = guild.get_channel(s_id)
            if isinstance(s, discord.TextChannel) and s.permissions_for(membre).read_messages:
                salon_fiche = s
                break

        # 5. Embed d'annonce visuelle
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

        # Envoi dans le salon global
        salon_global = guild.get_channel(ID_SALON_PROMOTIONS_GLOBAL)
        if salon_global and isinstance(salon_global, discord.TextChannel):
            await salon_global.send(content=f"{membre.mention}", embed=embed_promo)

        # Envoi dans la fiche perso
        if salon_fiche:
            await salon_fiche.send(content=f"{membre.mention}", embed=embed_promo)

        await interaction.followup.send(f"✅ Promotion de {membre.mention} effectuée avec succès !", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PromotionsCog(bot))
