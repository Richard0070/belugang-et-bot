import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from views.event_apps_views import EventAppButton
import config

class EventTeamApp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.persistent_view = EventAppButton(self.bot)

    async def cog_load(self):
        self.bot.add_view(self.persistent_view)

    async def cog_unload(self):
        await self.persistent_view.wait()

    @app_commands.command(name="event-app",
                          description="Post the Event Team Application")
    @app_commands.guild_only()
    @app_commands.describe(
        channel="Channel to post the Event Application embed")
    async def sendeventapp(self,
                           interaction: discord.Interaction,
                           channel: discord.TextChannel = None):
        if channel is None:
            channel = interaction.channel

        embed = discord.Embed(
            title="BeluGANG Event Team Application!",
            description=
            "_ _\nClick the button below to initiate the application process, during which you'll have a 60-minute window to complete it, and you can cancel it at any point.\n\nPlease note that completing this application does not guarantee you the role. We evaluate your chat history, behavior, and other factors, and we reserve the right to deny your application for any reason, without disclosing the specific reason.\n _ _",
            color=0x6e5ce7)

        embed.set_image(
            url="https://i.ibb.co/3WL7FTz/Untitled27-20240528083555.png")

        embed.set_footer(text="@ BeluGANG Event Management")

        await channel.send(embed=embed, view=self.persistent_view)
        await interaction.response.send_message(
            "Successfully posted the ET Application embed!") # btw you can add "ephemeral=True" to make the message only visible to the user who triggered the command. For example: await interaction.response.send_message("Successfully posted the ET Application embed!", ephemeral=True)

    @app_commands.command(
        name="purge-cooldown",
        description="Remove the Event App Cooldown from all members")
    @app_commands.guild_only()
    async def purge_cooldown(self, interaction: discord.Interaction):
        with open('data/setup-data.json', 'r') as f:
            config = json.load(f)
            cooldown_role_id = int(config['app_cooldown_role_id'])

            guild = interaction.guild

            if guild is None:
                print("Guild not found.")
                return

            cooldown_role = get(guild.roles, id=cooldown_role_id)

            if cooldown_role is None:
                await interaction.response.send_message(
                    "Cooldown role not found in this server.", ephemeral=True)
                return

            members_with_role = [
                member for member in interaction.guild.members
                if cooldown_role in member.roles
            ]

            if len(members_with_role) == 0:  
                await interaction.response.send_message(
                f"Couldn't find any user with the cooldown role.",
                ephemeral=True)                
                return                

            for member in members_with_role:
                await member.remove_roles(cooldown_role)

            await interaction.response.send_message(
                f"Removed the cooldown role from **{len(members_with_role)}** member(s).")
                
async def setup(bot):
    await bot.add_cog(EventTeamApp(bot))
