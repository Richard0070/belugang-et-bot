import discord
import config
import os
import json

class ModmailButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.setup_data_file = 'data/setup-data.json'
                
    async def check_modmail_channel(self):

        if not os.path.exists(self.setup_data_file):
          return False
    
        with open(self.setup_data_file, 'r') as file:
          setup_data = json.load(file)

        modmail_channel_id = setup_data.get('modmail_channel_id')
        
        return modmail_channel_id is not None and modmail_channel_id != ""
        
    async def load_blacklist(self):
        blacklist_file = os.path.join('data', 'blacklist.json')
        if os.path.exists(blacklist_file):
            with open(blacklist_file, 'r') as f:
                return json.load(f)
        return {"blacklisted_users": []}
        
    async def load_tickets(self):
        ticket_file = os.path.join('data', 'tickets.json')
        if os.path.exists(ticket_file):
            with open(ticket_file, 'r') as f:
                return json.load(f)
        return {}        

    @discord.ui.button(label="FAQs",
                           style=discord.ButtonStyle.gray,
                           custom_id="faq_button", emoji=config.QUESTION)

    async def faq_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not os.path.exists('data/faq.json'):
            return

        with open('data/faq.json', 'r') as file:
            faq_data = json.load(file)

        faqs = faq_data.get('faqs', [])

        if not faqs:
          await interaction.response.send_message("FAQs will be updated shortly!", ephemeral=True)
          return

        embed = discord.Embed(title="Frequently Asked Questions (FAQs)", color=0x6e5ce7)

        for i, faq in enumerate(faqs, 1):
          embed.add_field(name=f"{i}. {faq['question']}", value=faq['answer'], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True) 

    @discord.ui.button(label="Contact Event Team",
                       style=discord.ButtonStyle.blurple,
                       custom_id="modmail_button", emoji=config.MESSAGE)
    
    async def modmail_callback(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user
        blacklist = await self.load_blacklist()
        tickets = await self.load_tickets()

        if not await self.check_modmail_channel():
            await interaction.response.send_message("Support has been temporarily paused.", ephemeral=True)
            return

        if user.id in blacklist["blacklisted_users"]:
            await interaction.response.send_message("You are blacklisted from creating tickets.", ephemeral=True)
            return

        if str(user.id) in tickets:
            await interaction.response.send_message("You already have an active ticket.", ephemeral=True)
            return
            
        await interaction.response.send_modal(ModmailModal(self.bot, interaction.user))

class ModmailModal(discord.ui.Modal):
    def __init__(self, bot, user):
        super().__init__(title="Contact Event Team")
        self.bot = bot
        self.user = user
        self.open_tag = "open"
        self.add_item(discord.ui.TextInput(label="Why are you creating this ticket?", style=discord.TextStyle.long, max_length=1000))
        
        with open('data/setup-data.json', 'r') as f:
            setup_data = json.load(f)

        self.modmail_channel_id = int(setup_data['modmail_channel_id'])

    async def check_tag(self, channel, tag_name):
        for tag in channel.available_tags:            
            if tag.name.lower() == tag_name.lower():
                return tag
                
        return None

    async def on_submit(self, interaction: discord.Interaction):
        question = self.children[0].value
        channel = self.bot.get_channel(self.modmail_channel_id)

        embed = discord.Embed(
            description=f"**User:** {self.user.mention}, `{self.user.id}`\n**Reason:** {question}",
            color=0x27272F
        )
        embed.set_author(name=f"{self.user.name}", icon_url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)

        embed2 = discord.Embed(
            title=f"{config.MESSAGE} Ticket Opened",
            description=f"```\n{question}\n```\nPlease wait for one of our Event Team staff to respond back. Misusing may lead to severe punishments including blacklist.",
            color=0x27272F
        )

        if channel and isinstance(channel, discord.ForumChannel):
            tag = await self.check_tag(channel, self.open_tag)
            if tag is None:
                await interaction.response.send_message(f"Error: Tag '{self.open_tag}' not found.", ephemeral=True)
                return
                
            thread = await channel.create_thread(
                name=f"{self.user.name}'s ticket",
                embed=embed,
                applied_tags=[tag]
            )
            modmail_cog = self.bot.get_cog("Modmail")

            modmail_cog.save_ticket(str(self.user.id), thread.thread.id)

            await interaction.response.send_message("Keep your DMs open and wait for an Event Team member to respond back.", ephemeral=True)
           
            await self.user.send(embed=embed2)

        else:
            print("There was an issue creating the thread.")
