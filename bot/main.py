from json import load as json_load
from os import getenv as os_getenv

import discord
from discord.ext import commands as discord_commands

with open('bot/bot_config.json', 'r', encoding='utf-8') as f:
    bot_config = json_load(f)
bot = discord_commands.Bot(command_prefix='.',
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
    match error:
        case discord_commands.CommandNotFound():
            embed_msg = discord.Embed(title="Command not found",
                                      description=bot_config['command_not_found_description'], color=embeds_color)
        case discord_commands.MissingRequiredArgument():
            embed_msg = discord.Embed(title="Missing required argument",
                                      description=bot_config['missing_required_argument_description'].format(
                                          ctx.invoked_with.replace('.', '')) + f"\n\n```Error: {error}```",
                                      color=embeds_color)
        case _:
            embed_msg = discord.Embed(title="An error occurred",
                                      description=bot_config['generic_error_description'] + f"\n\n```Error: {error}```",
                                      color=embeds_color)
    await ctx.send(embed=embed_msg)


@bot.command(aliases=['shutdown'],
             brief=bot_config['close_brief'],
             description=bot_config['close_description'])
@discord_commands.has_permissions(administrator=True)
async def close(ctx):
    embed_msg = discord.Embed(description=bot_config['close_message'], color=embeds_color)
    await ctx.send(embed=embed_msg)
    await bot.change_presence(status=discord.Status.offline)
    await bot.close()
    print(">>> Odoaldo is offline\n\n\n")


@bot.command(aliases=['getextensions', 'getexts', 'gexts', 'extensions', 'exts'],
             brief=bot_config['get_extensions_brief'],
             description=bot_config['get_extensions_description'])
@discord_commands.has_permissions(administrator=True)
async def get_extensions(ctx):
    embed_msg = discord.Embed(description="Available extensions' info:", color=embeds_color)
    for get_extension in bot_config['extensions']:
        if get_extension in (key.split('.')[1] for key in bot.extensions.keys()):
            embed_msg.description += f"\n- :white_check_mark: {get_extension} is currently loaded"
        else:
            embed_msg.description += f"\n- :no_entry: {get_extension} is currently unloaded"
    await ctx.send(embed=embed_msg)


@bot.command(aliases=['loadextensions', 'loadexts', 'lexts'],
             brief=bot_config['load_extensions_brief'],
             description=bot_config['load_extensions_description'])
@discord_commands.has_permissions(administrator=True)
async def load_extensions(ctx, *extensions_list):
    embed_msg = discord.Embed(color=embeds_color)
    if len(extensions_list) == 0:
        embed_msg.description = "No extensions provided."
    else:
        embed_msg.description = "Output:"
        for extension_item in extensions_list:
            if extension_item not in bot_config['extensions']:
                embed_msg.description += f"\n- :interrobang: {extension_item} is not an extension"
                continue
            if extension_item in (key.split('.')[1] for key in bot.extensions.keys()):
                embed_msg.description += f"\n- :warning: {extension_item} is currently already loaded"
                continue
            try:
                bot.load_extension('extensions.' + extension_item)
                print(f">>> {extension_item} loaded")
                embed_msg.description += f"\n- :white_check_mark: {extension_item} loaded"
            except Exception as ex:
                print(f">>> Failed to load extension {extension_item} [{type(ex).__name__}: {ex}]")
                embed_msg.description += f"\n- :no_entry: {extension_item} not loaded"
    await ctx.send(embed=embed_msg)


@bot.command(aliases=['unloadextensions', 'unloadexts', 'ulexts'],
             brief=bot_config['unload_extensions_brief'],
             description=bot_config['unload_extensions_description'])
@discord_commands.has_permissions(administrator=True)
async def unload_extensions(ctx, *extensions_list):
    embed_msg = discord.Embed(color=embeds_color)
    if len(extensions_list) == 0:
        embed_msg.description = "No extensions provided."
    else:
        embed_msg.description = "Output:"
        for extension_item in extensions_list:
            if extension_item not in bot_config['extensions']:
                embed_msg.description += f"\n- :interrobang: {extension_item} is not an extension"
                continue
            if extension_item not in (key.split('.')[1] for key in bot.extensions.keys()):
                embed_msg.description += f"\n- :warning: {extension_item} is currently not loaded"
                continue
            try:
                bot.unload_extension('extensions.' + extension_item)
                print(f">>> {extension_item} unloaded")
                embed_msg.description += f"\n- :white_check_mark: {extension_item} unloaded"
            except Exception as ex:
                print(f">>> Failed to unload extension {extension_item} [{type(ex).__name__}: {ex}]")
                embed_msg.description += f"\n- :no_entry: {extension_item} not unloaded"
    await ctx.send(embed=embed_msg)


@bot.command(aliases=['reloadextensions', 'reloadexts', 'rlexts'],
             brief=bot_config['reload_extensions_brief'],
             description=bot_config['reload_extensions_description'])
@discord_commands.has_permissions(administrator=True)
async def reload_extensions(ctx, *extensions_list):
    embed_msg = discord.Embed(color=embeds_color)
    if len(extensions_list) == 0:
        embed_msg.description = "No extensions provided."
    else:
        embed_msg.description = "Output:"
        for extension_item in extensions_list:
            if extension_item not in bot_config['extensions']:
                embed_msg.description += f"\n- :interrobang: {extension_item} is not an extension"
                continue
            if extension_item not in (key.split('.')[1] for key in bot.extensions.keys()):
                embed_msg.description += f"\n- :warning: {extension_item} is currently not loaded"
                continue
            try:
                bot.reload_extension('extensions.' + extension_item)
                print(f">>> {extension_item} reloaded")
                embed_msg.description += f"\n- :white_check_mark: {extension_item} reloaded"
            except Exception as ex:
                print(f">>> Failed to reload extension {extension_item} [{type(ex).__name__}: {ex}]")
                embed_msg.description += f"\n- :no_entry: {extension_item} not reloaded"
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
