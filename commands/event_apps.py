import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from views.event_apps_views import EventAppButton
import config
import os

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

        questions_file = 'data/questions.json'
        if not os.path.exists(questions_file):
            await interaction.response.send_message("No questions found. Please add questions first.", ephemeral=True)
            return

        with open(questions_file, 'r') as f:
            data = json.load(f)
            if not data.get("questions") or len(data["questions"]) == 0:
                await interaction.response.send_message("No questions found. Please add questions first.", ephemeral=True)
                return
                
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
            "Successfully posted the ET Application!")

    @app_commands.command(
        name="purge-cooldown",
        description="Remove the Event App Cooldown from all members")
    @app_commands.guild_only()
    async def purge_cooldown(self, interaction: discord.Interaction):
        with open('data/setup-data.json', 'r') as f:
            role_data = json.load(f)
            cooldown_role_id = int(role_data['app_cooldown_role_id'])
                    
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

    @app_commands.command(name="add-question", description="Add questions to the Event Application")
    @app_commands.guild_only()
    @app_commands.describe(label="What will be the question?")
    @app_commands.describe(placeholder="Placeholder for the answer field")
    @app_commands.choices(style=[
        app_commands.Choice(name="Short", value="short"),
        app_commands.Choice(name="Long", value="long"),
        app_commands.Choice(name="Paragraph", value="paragraph")
    ])
    @app_commands.describe(max_length="Max length of answer (shouldn't exceed 1000)")
    @app_commands.describe(required="Required or Optional?")
    async def add_question(self, interaction: discord.Interaction, label: str, style: app_commands.Choice[str], max_length: int, required: bool, placeholder: str = None):
        questions_file = 'data/questions.json'
        if not os.path.exists(questions_file):
            with open(questions_file, 'w') as f:
                json.dump({"questions": []}, f, indent=4)

        with open(questions_file, 'r+') as f:
            data = json.load(f)
            question_number = len(data["questions"]) + 1

            if placeholder is None:
                placeholder = ""

            question_data = {
                "label": label,
                "placeholder": placeholder,
                "style": style.value,
                "max_length": max_length,
                "required": required,
                "id": question_number
            }
            data["questions"].append(question_data)
            f.seek(0)
            json.dump(data, f, indent=4)

        await interaction.response.send_message(f"Question **#{question_number}** added successfully!", ephemeral=True)

    @app_commands.command(name="delete-question", description="Delete a question from the Event Application")
    @app_commands.guild_only()
    @app_commands.describe(label="Select the question to delete")
    async def delete_question(self, interaction: discord.Interaction, label: str):
        questions_file = 'data/questions.json'
        if not os.path.exists(questions_file):
            await interaction.response.send_message("No questions found to delete.", ephemeral=True)
            return

        with open(questions_file, 'r+') as f:
            data = json.load(f)
            question_to_delete = next((q for q in data["questions"] if q["label"] == label), None)

            if question_to_delete is None:
                await interaction.response.send_message(f"No question found with the label **'{label}'**.", ephemeral=True)
                return

            data["questions"].remove(question_to_delete)
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=4)

        await interaction.response.send_message(f"Question deleted successfully!")

    @delete_question.autocomplete('label')
    async def autocomplete_label(self, interaction: discord.Interaction, current: str):
        questions_file = 'data/questions.json'
        if not os.path.exists(questions_file):
            return []

        with open(questions_file, 'r') as f:
            data = json.load(f)
            return [
                app_commands.Choice(name=q["label"], value=q["label"])
                for q in data["questions"] if current.lower() in q["label"].lower()
            ]

async def setup(bot):
    await bot.add_cog(EventTeamApp(bot))
                               
