import discord
from discord.ext import commands
from json import load as load_json
from os import getenv as os_getenv

with open('bot/bot_config.json', 'r', encoding='utf-8') as f:
    bot_config = load_json(f)

bot = commands.Bot(command_prefix='.',
                   case_insensitive=True,
                   description=bot_config['bot_description'])
token = os_getenv('DISCORD_BOT_TOKEN')


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening, name='.help'))
    print("\n>>> Odoaldo is online")


@bot.command(brief=bot_config['close_brief'],
             description=bot_config['close_description']
             if (bot_config['close_description'] != '') else bot_config['close_brief'])
@commands.has_permissions(administrator=True)
async def close(ctx):
    await bot.change_presence(status=discord.Status.offline)
    await bot.close()
    print(">>> Odoaldo is offline")


if __name__ == "__main__":
    print(f"Attempting to load startup extensions: {bot_config['startup_extensions']}")
    for extension in bot_config['startup_extensions']:
        try:
            bot.load_extension('extensions.' + extension)
            print(extension + ' loaded')
        except Exception as e:
            print(f"Failed to load extension {extension}\n{type(e).__name__}: {e}")

    bot.run(token)
