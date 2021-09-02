from json import load as load_json
from os import getenv as os_getenv

import discord
from discord.ext import commands

with open('bot/bot_config.json', 'r', encoding='utf-8') as f:
    bot_config = load_json(f)

bot = commands.Bot(command_prefix='.',
                   case_insensitive=True,
                   description=bot_config['bot_description'])
token = os_getenv('DISCORD_BOT_TOKEN')

embeds_color = int(bot_config['embeds_color'], 16)


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening, name='.help'))
    print("\n>>> Odoaldo is online")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed_msg = discord.Embed(description=bot_config['command_not_found'], color=embeds_color)
        await ctx.send(embed=embed_msg)
        return
    raise error


@bot.command(aliases=['shutdown'],
             brief=bot_config['close_brief'],
             description=bot_config['close_description'])
@commands.has_permissions(administrator=True)
async def close(ctx):
    embed_msg = discord.Embed(description=bot_config['close'], color=embeds_color)
    await ctx.send(embed=embed_msg)
    await bot.change_presence(status=discord.Status.offline)
    await bot.close()
    print(">>> Odoaldo is offline\n\n\n")


@bot.command(aliases=['getexts', 'gexts', 'extensions', 'exts'],
             brief=bot_config['get_extensions_brief'],
             description=bot_config['get_extensions_description'])
@commands.has_permissions(administrator=True)
async def getExtensions(ctx):
    embed_msg = discord.Embed(color=embeds_color)
    embed_msg.description = "Extensions info:"
    for get_extension in bot_config['extensions']:
        if get_extension in (key.split('.')[1] for key in bot.extensions.keys()):
            embed_msg.description += f"\n- :white_check_mark: {get_extension} is currently loaded"
        else:
            embed_msg.description += f"\n- :no_entry: {get_extension} is currently unloaded"
    await ctx.send(embed=embed_msg)


@bot.command(aliases=['loadexts', 'lexts'],
             brief=bot_config['load_extensions_brief'],
             description=bot_config['load_extensions_description'])
@commands.has_permissions(administrator=True)
async def loadExtensions(ctx, *load_extensions):
    embed_msg = discord.Embed(color=embeds_color)
    if len(load_extensions) == 0:
        embed_msg.description = "No extensions provided."
    else:
        embed_msg.description = "Output:"
        for load_extension in load_extensions:
            if load_extension not in bot_config['extensions']:
                embed_msg.description += f"\n- :interrobang: {load_extension} is not an extension"
                continue
            if load_extension in (key.split('.')[1] for key in bot.extensions.keys()):
                embed_msg.description += f"\n- :warning: {load_extension} is currently already loaded"
                continue
            try:
                bot.load_extension('extensions.' + load_extension)
                print(f">>> {load_extension} loaded")
                embed_msg.description += f"\n- :white_check_mark: {load_extension} loaded"
            except Exception as e:
                print(f">>> Failed to load extension {load_extension} [{type(e).__name__}: {e}]")
                embed_msg.description += f"\n- :no_entry: {load_extension} not loaded"
    await ctx.send(embed=embed_msg)


@bot.command(aliases=['unloadexts', 'ulexts'],
             brief=bot_config['unload_extensions_brief'],
             description=bot_config['unload_extensions_description'])
@commands.has_permissions(administrator=True)
async def unloadExtensions(ctx, *unload_extensions):
    embed_msg = discord.Embed(color=embeds_color)
    if len(unload_extensions) == 0:
        embed_msg.description = "No extensions provided."
    else:
        embed_msg.description = "Output:"
        for unload_extension in unload_extensions:
            if unload_extension not in bot_config['extensions']:
                embed_msg.description += f"\n- :interrobang: {unload_extension} is not an extension"
                continue
            if unload_extension not in (key.split('.')[1] for key in bot.extensions.keys()):
                embed_msg.description += f"\n- :warning: {unload_extension} is currently not loaded"
                continue
            try:
                bot.unload_extension('extensions.' + unload_extension)
                print(f">>> {unload_extension} unloaded")
                embed_msg.description += f"\n- :white_check_mark: {unload_extension} unloaded"
            except Exception as e:
                print(f">>> Failed to unload extension {unload_extension} [{type(e).__name__}: {e}]")
                embed_msg.description += f"\n- :no_entry: {unload_extension} not unloaded"
    await ctx.send(embed=embed_msg)


@bot.command(aliases=['reloadexts', 'rlexts'],
             brief=bot_config['reload_extensions_brief'],
             description=bot_config['reload_extensions_description'])
@commands.has_permissions(administrator=True)
async def reloadExtensions(ctx, *reload_extensions):
    embed_msg = discord.Embed(color=embeds_color)
    if len(reload_extensions) == 0:
        embed_msg.description = "No extensions provided."
    else:
        embed_msg.description = "Output:"
        for reload_extension in reload_extensions:
            if reload_extension not in bot_config['extensions']:
                embed_msg.description += f"\n- :interrobang: {reload_extension} is not an extension"
                continue
            if reload_extension not in (key.split('.')[1] for key in bot.extensions.keys()):
                embed_msg.description += f"\n- :warning: {reload_extension} is currently not loaded"
                continue
            try:
                bot.reload_extension('extensions.' + reload_extension)
                print(f">>> {reload_extension} reloaded")
                embed_msg.description += f"\n- :white_check_mark: {reload_extension} reloaded"
            except Exception as e:
                print(f">>> Failed to reload extension {reload_extension} [{type(e).__name__}: {e}]")
                embed_msg.description += f"\n- :no_entry: {reload_extension} not reloaded"
    await ctx.send(embed=embed_msg)


if __name__ == "__main__":
    print(f"\n\n\n{'-' * 80}")
    print(f"{bot_config['name']} - Version {bot_config['version']} - {bot_config['url']}")
    print(f"Licensed under {bot_config['license']} by {bot_config['author']} <{bot_config['author_email']}>")
    print(f"{'-' * 80}")
    print(f"\nAvailable extensions: {bot_config['extensions']}")
    print(f"Attempting to load startup extensions: {bot_config['startup_extensions']}")
    for extension in bot_config['startup_extensions']:
        try:
            bot.load_extension('extensions.' + extension)
            print(extension + ' loaded')
        except Exception as e:
            print(f"Failed to load extension {extension} [{type(e).__name__}: {e}]")

    bot.run(token)
