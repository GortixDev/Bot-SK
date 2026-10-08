import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import (
    LISTE_ROLES_GRADES, ROLES_STAFF, 
    salons_fiche_perso, verifier_roles
)

ID_SALON_PROMOTIONS_GLOBAL = 1435750825304784926
ID_ROLE_TF141 = 1435753877889749043

CATEGORIES_GRADES = {
    # ▬▬▬ Officiers Généraux (1435706034554540103)
    1435681997057163364: 1435706034554540103,  # Maréchal
    1435686815330996224: 1435706034554540103,  # Général d'armée
    1435686937548820652: 1435706034554540103,  # Général de corps d'armée
    1435686942665609256: 1435706034554540103,  # Général de Division
    1435686948034314321: 1435706034554540103,  # Général de Brigade

    # ▬▬▬ Officiers (1435706419390447768)
    1435686954133094502: 1435706419390447768,  # Colonel
    1435686958541049867: 1435706419390447768,  # Lieutenant-Colonel
    1435686962882412554: 1435706419390447768,  # Commandant
    1435686967152214036: 1435706419390447768,  # Capitaine
    1435686971333804193: 1435706419390447768,  # Lieutenant
    1435686975003693086: 1435706419390447768,  # Sous-Lieutenant
    1435686978522710066: 1435706419390447768,  # Aspirant

    # ▬▬▬ Sous-Officiers (1435706488118317217)
    1435686983770046545: 1435706488118317217,  # Major
    1435686988035653702: 1435706488118317217,  # Adjudant-Chef
    1435686992095740044: 1435706488118317217,  # Adjudant
    1435686996281659525: 1435706488118317217,  # Sergent-Chef BM2
    1435687000509513800: 1435706488118317217,  # Sergent

    # ▬▬▬ Militaires de Rang (1435706505176416256)
    1435687004774858762: 1435706505176416256,  # Caporal-Chef 1ʳᵉ Classe
    1435687009774469273: 1435706505176416256,  # Caporal-Chef
    1435687014157521047: 1435706505176416256,  # Caporal
    1435687017441919026: 1435706505176416256,  # Soldat 1ʳᵉ classe
    1435687023305298002: 1435706505176416256,  # Soldat
}

ROLES_CATEGORIES_TOUTES = set(CATEGORIES_GRADES.values())

CHOICES_GRADES = [
    app_commands.Choice(name="🌟・Maréchal", value="1435681997057163364"),
    app_commands.Choice(name="⭐⭐⭐⭐⭐️・Général d'armée", value="1435686815330996224"),
    app_commands.Choice(name="⭐⭐⭐️⭐・Général de corps d'armée", value="1435686937548820652"),
    app_commands.Choice(name="⭐⭐️⭐・Général de Division", value="1435686942665609256"),
    app_commands.Choice(name="⭐⭐️・Général de Brigade", value="1435686948034314321"),
    app_commands.Choice(name="🟢・Colonel", value="1435686954133094502"),
    app_commands.Choice(name="🟢・Lieutenant-Colonel", value="1435686958541049867"),
    app_commands.Choice(name="🟢・Commandant", value="1435686962882412554"),
    app_commands.Choice(name="🟢・Capitaine", value="1435686967152214036"),
    app_commands.Choice(name="🟢・Lieutenant", value="1435686971333804193"),
    app_commands.Choice(name="🟢・Sous-Lieutenant", value="1435686975003693086"),
    app_commands.Choice(name="🟢・Aspirant", value="1435686978522710066"),
    app_commands.Choice(name="🟡・Major", value="1435686983770046545"),
    app_commands.Choice(name="🟡・Adjudant-Chef", value="1435686988035653702"),
    app_commands.Choice(name="🟡・Adjudant", value="1435686992095740044"),
    app_commands.Choice(name="🟡・Sergent-Chef BM2", value="1435686996281659525"),
    app_commands.Choice(name="🟡・Sergent", value="1435687000509513800"),
    app_commands.Choice(name="🔘・Caporal-Chef 1ʳᵉ Classe", value="1435687004774858762"),
    app_commands.Choice(name="🔘・Caporal-Chef", value="1435687009774469273"),
    app_commands.Choice(name="🔘・Caporal", value="1435687014157521047"),
    app_commands.Choice(name="🔘・Soldat 1ʳᵉ classe", value="1435687017441919026"),
    app_commands.Choice(name="🔘・Soldat", value="1435687023305298002"),
]

class PromotionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="promotions", description="Promeut un membre en attribuant le nouveau grade et sa catégorie")
    @app_commands.choices(nouveau_grade=CHOICES_GRADES)
    @verifier_roles(ROLES_STAFF)
    async def promotions(self, interaction: discord.Interaction, membre: discord.Member, nouveau_grade: app_commands.Choice[str]):
        # Vérification du salon d'exécution
        if interaction.channel_id != ID_SALON_PROMOTIONS_GLOBAL:
            await interaction.response.send_message(
                f"❌ Cette commande doit être exécutée uniquement dans le salon <#{ID_SALON_PROMOTIONS_GLOBAL}>.", 
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        if not guild:
            await interaction.followup.send("❌ Serveur introuvable.", ephemeral=True)
            return

        try:
            membre = await guild.fetch_member(membre.id)
        except Exception:
            pass

        nouveau_grade_id = int(nouveau_grade.value)
        nouveau_role = guild.get_role(nouveau_grade_id)
        
        if not nouveau_role:
            await interaction.followup.send("❌ Rôle de grade introuvable sur le serveur.", ephemeral=True)
            return

        id_categorie_cible = CATEGORIES_GRADES.get(nouveau_grade_id)
        role_categorie_cible = guild.get_role(id_categorie_cible) if id_categorie_cible else None
        role_tf141 = guild.get_role(ID_ROLE_TF141)

        # Retrait des anciens grades et anciennes catégories
        roles_a_retirer = [
            r for r in membre.roles 
            if (r.id in LISTE_ROLES_GRADES and r.id != nouveau_grade_id)
            or (r.id in ROLES_CATEGORIES_TOUTES and r.id != id_categorie_cible)
        ]

        if roles_a_retirer:
            try:
                await membre.remove_roles(*roles_a_retirer)
            except Exception as e:
                print(f"Erreur lors du retrait des anciens rôles : {e}")

        # Ajout des nouveaux rôles (Grade + Catégorie + TF141)
        roles_a_ajouter = [nouveau_role]
        if role_categorie_cible and role_categorie_cible not in membre.roles:
            roles_a_ajouter.append(role_categorie_cible)
        if role_tf141 and role_tf141 not in membre.roles:
            roles_a_ajouter.append(role_tf141)

        try:
            await membre.add_roles(*roles_a_ajouter)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur lors de l'attribution des rôles : {e}", ephemeral=True)
            return

        # Recherche du salon fiche perso
        salon_fiche = None
        for s_id in salons_fiche_perso:
            s = guild.get_channel(s_id)
            if isinstance(s, discord.TextChannel) and s.permissions_for(membre).read_messages:
                salon_fiche = s
                break

        # Embed d'annonce
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

        # Envoi dans le salon autorisé (ID_SALON_PROMOTIONS_GLOBAL)
        salon_global = guild.get_channel(ID_SALON_PROMOTIONS_GLOBAL)
        if salon_global and isinstance(salon_global, discord.TextChannel):
            await salon_global.send(content=f"{membre.mention}", embed=embed_promo)

        # Envoi dans le salon fiche perso
        if salon_fiche:
            await salon_fiche.send(content=f"{membre.mention}", embed=embed_promo)

        await interaction.followup.send(f"✅ Promotion de {membre.mention} au grade {nouveau_role.mention} effectuée avec succès !", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PromotionsCog(bot))
