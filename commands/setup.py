import discord
from discord.ext import commands
from discord import app_commands
from views.setup_views import SetupButtons, FAQButtons
import config

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Setup and configuration editor")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def _setup(self, interaction: discord.Interaction):

        embed = discord.Embed(title="🧪  Setup Wizard", description="Configure the Event Team role IDs and other stuff using this interactive menu. Press the buttons below to continue!", color=0x27272F)

        view = SetupButtons(self.bot, interaction)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="faqs", description="Setup FAQs")
    @app_commands.guild_only()
    async def _setup_faq(self, interaction: discord.Interaction):

        embed = discord.Embed(title=f"{config.QUESTION} Edit FAQs", description="Use the `Edit FAQs` button to edit the frequently asked questions for the ongoing event.", color=0x27272F)

        view = FAQButtons(self.bot, interaction)
        
        await interaction.response.send_message(embed=embed, view=view)
        
async def setup(bot):
    await bot.add_cog(Setup(bot))
