import discord
import json
import os
import config 
from discord.utils import get

class EventAppModal(discord.ui.Modal):
    def __init__(self, bot):
        with open('data/questions.json', 'r') as f:
            questions = json.load(f)['questions']

        super().__init__(title='Event Team Application', timeout=3600)
        self.bot = bot

        self.questions = []
        for q in questions:
            text_input = discord.ui.TextInput(
                label=q['label'],
                placeholder=q.get('placeholder', ''),
                style=discord.TextStyle.long if q['style'] == 'long' else discord.TextStyle.short,
                max_length=q.get('max_length', None),
                required=q.get('required', False),                 )
            self.add_item(text_input)
            self.questions.append(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        with open('data/setup-data.json', 'r') as f:
            config_data = json.load(f)

        forum_channel_id = int(config_data['app_submission_channel_id'])
        cooldown_role_id = int(config_data['app_cooldown_role_id'])

        guild = interaction.guild
        if guild is None:
            print("Guild not found.")
            return

        role = get(guild.roles, id=cooldown_role_id)
        if role is None:
            await interaction.response.send_message(
                f"Cooldown role with ID {cooldown_role_id} not found.",
                ephemeral=True)
            return

        await interaction.user.add_roles(role)

        embed = discord.Embed(title="Event Team Application", color=0xffffff)
        embed.add_field(
            name="Submitted by",
            value=f"{interaction.user.mention} (@{interaction.user}, `{interaction.user.id}`)",
            inline=False)

        for i, question in enumerate(self.questions, 1):
            embed.add_field(
                name=f"{i}. {question.label}",
                value=f"```{question.value}```",
                inline=False
            )

        forum_channel = guild.get_channel(forum_channel_id)
        if forum_channel is None:
            await interaction.response.send_message(
                f"Event Application submission has been temporarily paused.",
                ephemeral=True)
            return

        if isinstance(forum_channel, discord.ForumChannel):
            await forum_channel.create_thread(
                name=f"{interaction.user.name}'s Application", embed=embed)
            await interaction.response.send_message(
                "Your application has been submitted!", ephemeral=True)
        else:
            print("Forum channel is not a ForumChannel.")

class EventAppButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.setup_data_file = 'data/setup-data.json'

    async def check_app_channel(self):
        if not os.path.exists(self.setup_data_file):
            return False

        with open(self.setup_data_file, 'r') as file:
            setup_data = json.load(file)

        app_submission_channel_id = setup_data.get('app_submission_channel_id')

        return app_submission_channel_id is not None and app_submission_channel_id != ""        

    @discord.ui.button(label="Fill Application",
                       style=discord.ButtonStyle.blurple,
                       custom_id="fill_app",
                       emoji=config.FILL_APP)
    async def fill_app_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open(self.setup_data_file, 'r') as f:
            config_data = json.load(f)
            
        questions_file = 'data/questions.json'
        if not os.path.exists(questions_file):
            await interaction.response.send_message("Event Application submission has been temporarily paused.", ephemeral=True)
            return

        with open(questions_file, 'r') as f:
            data = json.load(f)
            if not data.get("questions") or len(data["questions"]) == 0:
                await interaction.response.send_message("Event Application submission has been temporarily paused.", ephemeral=True)
                return
                        
        cooldown_role_id = int(config_data['app_cooldown_role_id'])

        guild = interaction.guild
        if guild is None:
            print("Guild not found.")
            return

        cooldown_role = get(guild.roles, id=cooldown_role_id)
        if cooldown_role is None:
            print(f"Cooldown role with ID ({cooldown_role_id}) not found.")
            return

        if not await self.check_app_channel():
            await interaction.response.send_message("Event Application submission has been temporarily paused.", ephemeral=True)
            return

        if cooldown_role in interaction.user.roles:
            embed = discord.Embed(description="⏱️  You are on cooldown.",
                                  color=0xffffff)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_modal(EventAppModal(self.bot))
