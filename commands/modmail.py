import discord
import json
import os
from discord.ext import commands
from discord import app_commands
from views.modmail_views import ModmailButton
import config
import io
from datetime import datetime, timedelta

class Modmail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_folder = 'data'
        self.persistent_view = ModmailButton(self.bot)
        self.closed_tag = "closed"
        self.open_tag = "open"
        self.blacklist_file = os.path.join(self.data_folder, 'blacklist.json')
        self.ticket_file = os.path.join(self.data_folder, 'tickets.json')
        self.last_dm_attempt = {}

        os.makedirs(self.data_folder, exist_ok=True)

        if os.path.exists(self.ticket_file):
            with open(self.ticket_file, 'r') as f:
                self.tickets = json.load(f)
        else:
            self.tickets = {}
            self.save_tickets()

        if not os.path.exists(self.blacklist_file):
            self.save_blacklist({"blacklisted_users": []})

    async def cog_load(self):
        self.bot.add_view(self.persistent_view)

    async def cog_unload(self):
        await self.persistent_view.wait()

    def load_blacklist(self):
        if os.path.exists(self.blacklist_file):
            with open(self.blacklist_file, 'r') as f:
                data = json.load(f)
                if "blacklisted_users" not in data:
                    data["blacklisted_users"] = []
                return data
        return {"blacklisted_users": []}

    async def load_blacklisted_users(self):
        try:
            with open(self.blacklist_file, 'r') as f:
                return json.load(f).get("blacklisted_users", [])
        except FileNotFoundError:
            return []

    def save_blacklist(self, blacklist):
        with open(self.blacklist_file, 'w') as f:
            json.dump(blacklist, f, indent=4)

    def save_tickets(self):
        with open(self.ticket_file, 'w') as f:
            json.dump(self.tickets, f, indent=4)

    async def handle_user_dm(self, message):
        embed = discord.Embed(
            title=f"{config.ET} Event Query",
            description="_ _\n1. Check frequently asked questions about the ongoing event using the **FAQs** button.\n2. For personalized assistance or inquiries, use the **Contact Event Team** button to directly communicate with our ET staff.",
            color=0x6e5ce7
        )

        embed.set_footer(text="@ BeluGANG Event Management")

        view = ModmailButton(self.bot)
        await message.author.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message):
            
        if isinstance(message.channel, discord.DMChannel) and not message.author.bot:

            if str(message.author.id) in self.tickets:
                await self.forward_message_to_forum(message)
            else:
                await self.handle_user_dm(message)
        elif isinstance(message.channel, discord.Thread) and not message.author.bot:
            if self.tickets:
                matching_tickets = [
                    ticket for ticket in self.tickets.values()
                    if ticket['thread_id'] == message.channel.id
                ]
                
                if matching_tickets:
                    await self.forward_message_to_user(message)

    async def send_dm(self, user, message=None, embeds=None):
        success = True
        now = datetime.utcnow()
        last_attempt = self.last_dm_attempt.get(user.id)

        if last_attempt and now - last_attempt < timedelta(minutes=5):
            return False

        try:
            if message:
                await user.send(content=message, embeds=embeds)
            else:
                await user.send(embeds=embeds)
            success = True
        except (discord.Forbidden, discord.HTTPException) as e:
            self.last_dm_attempt[user.id] = now
            success = False
            print(f"Error sending DM: {e}")

        return success

    async def forward_message_to_user(self, message):
        try:
            ticket = next(ticket for ticket in self.tickets.values()
                          if ticket['thread_id'] == int(message.channel.id))
            user = self.bot.get_user(int(ticket['user_id']))
            
            if user:
                embeds = []
                if message.content:

                    if len(message.content) > 2000:
                        message.content = message[:1997] + "..."

                    embed = discord.Embed(description=message.content, color=0x27272F)
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
                    embeds.append(embed)

                for attachment in message.attachments:
                    embed = discord.Embed(color=0x27272F)
                    embed.set_image(url=attachment.url)
                    embeds.append(embed)

                for embed in message.embeds:
                    embeds.append(embed)

                dm_success = await self.send_dm(user, embeds=embeds)

                if not dm_success:
                    await message.channel.send(embed=discord.Embed(description=f"{config.ERROR} Failed to DM user. Try again after 5-10 minutes to avoid getting rate limited.", color=0xff0000))
        except Exception as e:
            print(f"Error in 'forward_message_to_user' function: {e}")

    async def forward_message_to_forum(self, message):
        ticket = self.tickets[str(message.author.id)]
        thread = self.bot.get_channel(ticket['thread_id'])
        if thread:
            embeds = []
                            
            if message.content:

                if len(message.content) > 2000:
                    message.content = message[:1997] + "..."
                                
                embed = discord.Embed(description=message.content, color=0x27272F)
                embed.set_author(
                    name=message.author.name,
                    icon_url=message.author.avatar.url if message.author.avatar
                    else message.author.default_avatar.url
                )
                embeds.append(embed)

            for attachment in message.attachments:
                embed = discord.Embed(color=0x27272F)
                embed.set_image(url=attachment.url)
                embeds.append(embed)

            await thread.send(embeds=embeds)
        else:
            print(
                f"Could not find the active ticket thread - {message.author.id} / {message.author.name}"
            )

    async def notify_ticket_closed(self, user):
        embed = discord.Embed(
            title=f"{config.CLOSE} Ticket Closed",
            description="Your ticket has been closed by the Event Team. If you have further questions, feel free to open a new ticket.",
            color=0x27272F
        )
        await self.send_dm(user, embeds=[embed])

    def save_ticket(self, user_id, thread_id):
        self.tickets[user_id] = {'thread_id': thread_id, 'user_id': user_id}
        self.save_tickets()

    def delete_ticket(self, user_id):
        if user_id in self.tickets:
            del self.tickets[user_id]
            self.save_tickets()

    async def check_tag(self, channel, tag_name):
        for tag in channel.available_tags:
            if tag.name.lower() == tag_name.lower():
                return tag
        return None

    @app_commands.command(name="close", description="Close an active ticket")
    @app_commands.guild_only()
    async def close_ticket(self, interaction: discord.Interaction):
        if interaction.guild and isinstance(interaction.channel, discord.Thread):
            thread = interaction.channel
            forum_channel = thread.parent
            if isinstance(forum_channel, discord.ForumChannel):
                open_tag_id = await self.check_tag(forum_channel, self.open_tag)
                closed_tag_id = await self.check_tag(forum_channel, self.closed_tag)

                if open_tag_id is None or closed_tag_id is None:
                    await interaction.response.send_message(
                        "Error: Could not find necessary tags.",
                        ephemeral=True
                    )
                    return

                applied_tags = [
                    tag for tag in thread.applied_tags if tag != open_tag_id
                ]
                applied_tags.append(closed_tag_id)

                await thread.edit(applied_tags=applied_tags, locked=True, reason=f"closed by {interaction.user.name} ({interaction.user.id})")

            for user_id, ticket in self.tickets.items():
                if ticket['thread_id'] == interaction.channel.id:
                    user = self.bot.get_user(int(user_id))
                    if user:
                        await self.notify_ticket_closed(user)
                    self.delete_ticket(user_id)

                    embed = discord.Embed(
                        description=f"{config.CLOSE} The ticket has been closed.",
                        color=0xffffff
                    )

                    await interaction.response.send_message(embed=embed)
                    return
            await interaction.response.send_message(
                "No active ticket found for this thread.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "This command can only be used in ticket threads.",
                ephemeral=True
            )

    @app_commands.command(name="blacklist", description="Blacklist a user from creating tickets")
    @app_commands.guild_only()
    @app_commands.describe(user="The user to blacklist")
    async def blacklist(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()
        blacklist = self.load_blacklist()

        if user.id in blacklist["blacklisted_users"]:
            await interaction.followup.send(
                f"**{user.name}#{user.discriminator}** is already blacklisted!"
            )
        else:
            blacklist["blacklisted_users"].append(user.id)
            self.save_blacklist(blacklist)
            await interaction.followup.send(
                f"**{user.name}#{user.discriminator}** has been blacklisted."
            )

    @app_commands.command(name="whitelist", description="Whitelist a user")
    @app_commands.guild_only()
    @app_commands.describe(user="The user to whitelist")
    async def whitelist(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()
        blacklist = self.load_blacklist()
        if user.id not in blacklist["blacklisted_users"]:
            await interaction.followup.send(
                f"**{user.name}#{user.discriminator}** isn't blacklisted!"
            )
        else:
            blacklist["blacklisted_users"].remove(user.id)
            self.save_blacklist(blacklist)
            await interaction.followup.send(
                f"**{user.name}#{user.discriminator}** has been whitelisted."
            )

    @app_commands.command(name="blacklisted-users", description="List of blacklisted users")
    @app_commands.guild_only()
    async def blacklist_users(self, interaction: discord.Interaction):

        blacklisted_users =  await self.load_blacklisted_users()

        if not blacklisted_users:
            await interaction.response.send_message("No users are currently blacklisted.", ephemeral=True)
            return

        blacklist_text = "\n".join(str(user_id) for user_id in blacklisted_users)

        file = discord.File(io.BytesIO(blacklist_text.encode()), filename="blacklisted_users.txt")
        await interaction.response.send_message("**Here is the list of blacklisted users:**", file=file)

async def setup(bot):
    await bot.add_cog(Modmail(bot))
