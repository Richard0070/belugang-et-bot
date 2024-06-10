import discord
from discord.utils import get
import json
import config 
import os

class EventAppModal(discord.ui.Modal,
                    title='Fill this to apply for events team'):

    def __init__(self, bot):
        super().__init__(timeout=3600)
        self.bot = bot
        self.q1 = discord.ui.TextInput(
            label='Tell us about you!',
            placeholder=
            'Who are you, what is your age (necessary) and what are you interested in, your hobbies, etc.',
            style=discord.TextStyle.long,
            max_length=1018,
            required=True)
        self.q2 = discord.ui.TextInput(label='What is your timezone?',
                                       placeholder='Example: GMT +5:30',
                                       required=True,
                                       style=discord.TextStyle.short,
                                       max_length=10)
        self.q3 = discord.ui.TextInput(
            label='Do you have a working mic to speak on stage?',
            placeholder=
            'Note that event management is prioritizing applicants who can speak on stages!',
            required=True,
            style=discord.TextStyle.long,
            max_length=1018)
        self.q4 = discord.ui.TextInput(
            label='Why do you want to join the Events Team?',
            style=discord.TextStyle.long,
            max_length=1018,
            required=True)
        self.q5 = discord.ui.TextInput(
            label='What does this role mean to you?',
            required=True,
            style=discord.TextStyle.long,
            max_length=1018)

        self.add_item(self.q1)
        self.add_item(self.q2)
        self.add_item(self.q3)
        self.add_item(self.q4)
        self.add_item(self.q5)

    async def on_submit(self, interaction: discord.Interaction):
        with open('data/setup-data.json', 'r') as f:
            config = json.load(f)

        forum_channel_id = int(config['app_submission_channel_id'])
        cooldown_role_id = int(config['app_cooldown_role_id'])

        guild = interaction.guild
        if guild is None:
            print("Guild not found.")
            return

        # print(f"Guild roles: {[role.name for role in guild.roles]}")

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
            value=
            f"{interaction.user.mention} (@{interaction.user}, `{interaction.user.id}`)",
            inline=False)
        embed.add_field(name="1. Tell us about you!",
                        value=f"```{self.q1.value}```",
                        inline=False)
        embed.add_field(name="2. What is your timezone?",
                        value=f"```{self.q2.value}```",
                        inline=False)
        embed.add_field(
            name=
            "3. Do you have a working mic and are you able to speak on stage?",
            value=f"```{self.q3.value}```",
            inline=False)
        embed.add_field(
            name="4. Why do you want to become a part of the Events Team?",
            value=f"```{self.q4.value}```",
            inline=False)
        embed.add_field(
            name="5. What does the role of an Events Team member mean to you?",
            value=f"```{self.q5.value}```",
            inline=False)

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
    async def create_tag_callback(self, interaction: discord.Interaction,
                                  button: discord.ui.Button):
        with open('data/setup-data.json', 'r') as f:
            config = json.load(f)

        cooldown_role_id = int(config['app_cooldown_role_id'])

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
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
        else:
            await interaction.response.send_modal(EventAppModal(self.bot))
