import discord
from discord.ext import commands
import os
import config

bot = commands.Bot(command_prefix="+", case_insensitive=True, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"\nConnected to {bot.user.name}\n")
    await load_extensions()    
    await sync_commands()
    activity = discord.Game(name="DM me to contact Event Staff")
    await bot.change_presence(activity=activity)
  
  
async def load_extensions():
    for filename in os.listdir('./commands'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'commands.{filename[:-3]}')
                print(f"[+] {filename[:-3]}.py — online")
            except commands.ExtensionError as e:
                print(f"[-] {filename[:-3]}.py — offline ({e})")

async def sync_commands():
    synced = await bot.tree.sync()
    print(f"\nSynced {len(synced)} commands")

bot.remove_command('help')

@bot.event
async def on_message(message):
    if not message.author.bot:
        await bot.process_commands(message)

bot.run(config.TOKEN)