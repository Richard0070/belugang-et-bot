import discord
import os
import json
import config 

class SetupButtons(discord.ui.View):
    def __init__(self, bot, interaction):
        super().__init__(timeout=None)
        self.bot = bot
        self.author = interaction.user
        
    @discord.ui.button(label="View Configuration", style=discord.ButtonStyle.blurple)
    async def _view_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        if not os.path.exists('data/setup-data.json'):
            return

        with open('data/setup-data.json', 'r') as file:
            setup_data = json.load(file)

        event_team_role_ids = setup_data.get('event_team_role_ids', [])
        event_manager_role_ids = setup_data.get('event_manager_role_ids', [])
        modmail_channel_id = setup_data.get('modmail_channel_id')
        app_submission_channel_id = setup_data.get('app_submission_channel_id')
        app_cooldown_role_id = setup_data.get('app_cooldown_role_id')

        event_team_role_ids = [role_id for role_id in setup_data.get('event_team_role_ids', []) if role_id]
        event_manager_role_ids = [role_id for role_id in setup_data.get('event_manager_role_ids', []) if role_id]
        modmail_channel_id = setup_data.get('modmail_channel_id')
        app_submission_channel_id = setup_data.get('app_submission_channel_id')

        event_team_roles = ', '.join(f'<@&{role_id}>' for role_id in event_team_role_ids) if event_team_role_ids else 'Not set'
        event_manager_roles = ', '.join(f'<@&{role_id}>' for role_id in event_manager_role_ids) if event_manager_role_ids else 'Not set'
        modmail_channel = f'<#{modmail_channel_id}>' if modmail_channel_id else 'Not set'
        app_submission_channel = f'<#{app_submission_channel_id}>' if app_submission_channel_id else 'Not set'
        app_cooldown_role_id = f'<@&{app_cooldown_role_id}>' if app_cooldown_role_id else 'Not set'
               
        embed=discord.Embed(title="Current Configuration", color=0x6e5ce7)

        embed.add_field(name=f"{config.ET}  Event Team Role(s)", value=f"{config.REPLY}  {event_team_roles}", inline=False)

        embed.add_field(name=f"{config.EM}  Event Manager Role(s)", value=f"{config.REPLY}  {event_manager_roles}", inline=False)

        embed.add_field(name=f"{config.CHANNEL}  Modmail Channel", value=f"{config.REPLY}  {modmail_channel}", inline=False)

        embed.add_field(name=f"{config.CHANNEL}  App Submission Channel", value=f"{config.REPLY}  {app_submission_channel}", inline=False) 
        
        embed.add_field(name=f"{config.MENTION}  App Cooldown Role ID", value=f"{config.REPLY}  {app_cooldown_role_id}", inline=False) 
        
        if self.author.id == interaction.user.id:
          await interaction.response.send_message(embed=embed, ephemeral=True)        
        else:
            await interaction.response.send_message("You can't control these buttons!", ephemeral=True)
        
    @discord.ui.button(label='Configure', style=discord.ButtonStyle.secondary, custom_id='setup_button')
    async def _configure(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author.id == interaction.user.id:
            await interaction.response.send_modal(SetupModal(self.bot, interaction))
        else:
            await interaction.response.send_message("You can't control these buttons!", ephemeral=True)

    @discord.ui.button(emoji=config.DELETE, style=discord.ButtonStyle.red, custom_id='delete_button')
    async def _delete(self, interaction: discord.Interaction, button: discord.ui.Button):
      view = ResetButton(self.bot)
      await interaction.response.send_message("This will reset everything. Are you sure?", view=view, ephemeral=True)

class ResetButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Yes, I'm sure" ,style=discord.ButtonStyle.green, custom_id='reset')
    async def _reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            with open('data/setup-data.json', 'w') as file:
              json.dump({}, file)
            await interaction.response.send_message("Setup data has been reset successfully!", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.defer()

class SetupModal(discord.ui.Modal):
    def __init__(self, bot, interaction):
        self.bot = bot
        self.interaction = interaction
        super().__init__(title='Configure')

        setup_data = {}
        if os.path.exists('data/setup-data.json'):
            with open('data/setup-data.json', 'r') as file:
                setup_data = json.load(file)

        event_team_role_ids = ', '.join(setup_data.get('event_team_role_ids', []))
        event_manager_role_ids = ', '.join(setup_data.get('event_manager_role_ids', []))
        modmail_channel_id = setup_data.get('modmail_channel_id', '')
        app_submission_channel_id = setup_data.get('app_submission_channel_id', '')
        app_cooldown_role_id = setup_data.get('app_cooldown_role_id', '')

        # Set default values from setup data
        self.add_item(
            discord.ui.TextInput(
                label='Event Team Role IDs',
                placeholder='role id 1, role id 2...',
                default=event_team_role_ids,
                required=False
            )
        )

        self.add_item(
            discord.ui.TextInput(
                label='Event Manager Role IDs',
                placeholder='role id 1, role id 2...',
                default=event_manager_role_ids,
                required=False
            )
        )

        self.add_item(
            discord.ui.TextInput(
                label='Modmail Channel ID',
                placeholder='',
                default=modmail_channel_id,
                required=False
            )
        )

        self.add_item(
            discord.ui.TextInput(
                label='App Submission Channel ID',
                placeholder='',
                default=app_submission_channel_id,
                required=False
            )
        )

        self.add_item(
            discord.ui.TextInput(
                label='App Cooldown Role ID',
                placeholder='',
                default=app_cooldown_role_id,
                required=False
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        event_team_ids = self.children[0].value.split(',')
        event_manager_ids = self.children[1].value.split(',')
        modmail_channel_id = self.children[2].value.strip()
        app_submission_channel_id = self.children[3].value.strip()
        app_cooldown_role_id = self.children[4].value.strip()

        setup_data = {
            'event_team_role_ids': [role_id.strip() for role_id in event_team_ids],
            'event_manager_role_ids': [role_id.strip() for role_id in event_manager_ids],
            'modmail_channel_id': modmail_channel_id,
            'app_submission_channel_id': app_submission_channel_id,
            'app_cooldown_role_id': app_cooldown_role_id
        }

        with open('data/setup-data.json', 'w') as file:
            json.dump(setup_data, file, indent=4)

        await interaction.response.send_message("Configuration saved!", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Oops! Something went wrong.', ephemeral=True)
        print(error)

class FAQButtons(discord.ui.View):
    def __init__(self, bot, interaction):
        super().__init__(timeout=None)
        self.bot = bot
        self.author = interaction.user
        
    @discord.ui.button(label="View FAQs", style=discord.ButtonStyle.blurple)
    async def _view_faq(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not os.path.exists('data/faq.json'):
            return

        with open('data/faq.json', 'r') as file:
            faq_data = json.load(file)

        faqs = faq_data.get('faqs', [])

        if not faqs:
          await interaction.response.send_message("No FAQs data found.", ephemeral=True)
          return

        embed = discord.Embed(title="Current FAQs", color=0x6e5ce7)

        for i, faq in enumerate(faqs, 1):
          embed.add_field(name=f"{i}. {faq['question']}", value=faq['answer'], inline=False)

        if self.author.id == interaction.user.id:
            await interaction.response.send_message(embed=embed, ephemeral=True)        
        else:
            await interaction.response.send_message("You can't control these buttons!", ephemeral=True)
        
    @discord.ui.button(label='Edit FAQs', style=discord.ButtonStyle.secondary, custom_id='edit_faq_button')
    async def _edit_faq(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author.id == interaction.user.id:
            await interaction.response.send_modal(FAQModal(self.bot, interaction))
        else:
            await interaction.response.send_message("You can't control these buttons!", ephemeral=True)

    @discord.ui.button(emoji=config.DELETE, style=discord.ButtonStyle.red, custom_id='reset_faq_button')
    async def _reset_faq(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = FAQResetButton(self.bot)
        await interaction.response.send_message("This will delete all the FAQs data. Are you sure?", view=view, ephemeral=True)

class FAQResetButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Yes, I'm sure" ,style=discord.ButtonStyle.green, custom_id='reset')
    async def _reset_faq_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            with open('data/faq.json', 'w') as file:
                json.dump({}, file)
            await interaction.response.send_message("FAQs data has been reset successfully!", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.defer()

class FAQModal(discord.ui.Modal):
    def __init__(self, bot, interaction):
        self.bot = bot
        self.interaction = interaction
        super().__init__(title='Edit FAQs')

        faq_data = {}
        if os.path.exists('data/faq.json'):
            with open('data/faq.json', 'r') as file:
                faq_data = json.load(file)

        self.add_item(
            discord.ui.TextInput(
                label='Question',
                placeholder='Enter the FAQ question',
                required=True,                
                max_length=256
            )
        )
        self.add_item(
            discord.ui.TextInput(
                label='Answer',
                placeholder='Enter the FAQ answer',
                required=True,
                max_length=1000
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        question = self.children[0].value
        answer = self.children[1].value

        faq_data = {}
        if os.path.exists('data/faq.json'):
            with open('data/faq.json', 'r') as file:
                faq_data = json.load(file)

        faqs = faq_data.get('faqs', [])
        faqs.append({'question': question, 'answer': answer})

        with open('data/faq.json', 'w') as file:
            json.dump({'faqs': faqs}, file, indent=4)

        await interaction.response.send_message("FAQ saved!", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Oops! Something went wrong.', ephemeral=True)
        print(error)
        