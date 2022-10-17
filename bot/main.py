import typing
from asyncio import run as asyncio_run
from json import load as json_load
from logging import basicConfig as logging_basicConfig, getLogger, INFO
from os import getenv as os_getenv
from os.path import join as path_join
from urllib.parse import quote_plus

import discord
from discord.ext import commands as discord_commands

from src.utils.mongo import MongoUtil

# Setting up basic config and root logger
logging_basicConfig(format='[%(asctime)s] [%(name)-24s] [%(levelname)-8s] - %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S", level=INFO)
logger = getLogger()

# Get bot level config and create discord bot object with intents, token and main bot embeds color
with open(path_join('bot', os_getenv('BOT_CONFIG')), 'r', encoding='utf-8') as f:
    _bot_config = json_load(f)
__intents = discord.Intents.default()
__intents.message_content = True
bot = discord_commands.Bot(command_prefix=_bot_config['command_prefix'],
                           case_insensitive=True,
                           description=_bot_config['bot_description'],
                           intents=__intents)
__token = os_getenv('DISCORD_TOKEN')
__embeds_color = int(_bot_config['embeds_color'], 16)


@bot.event
async def on_ready():
    # Show Odoaldo activity, suggesting help command
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening,
                                                        name=f'{bot.command_prefix}help'))
    logger.info(f"Odoaldo is online: command prefix is {bot.command_prefix}")


@bot.event
async def on_command(ctx: discord_commands.Context):
    logger.info(f"Command {bot.command_prefix}{ctx.command} "
                f"invoked by @{ctx.author.name} in #{ctx.channel.name}")


@bot.event
async def on_command_completion(ctx: discord_commands.Context):
    logger.info(f"Command {bot.command_prefix}{ctx.command} successfully executed")


@bot.event
async def on_command_error(ctx: discord_commands.Context, error: discord_commands.CommandError):
    logger.error(f"{error.__class__.__name__}: {error}")
    # Match type of error
    match error:
        case discord_commands.CommandNotFound():
            # Command not found
            embed_msg = discord.Embed(title="Command not found",
                                      description=_bot_config['command_not_found_description'].format(
                                          bot.command_prefix),
                                      color=__embeds_color)
        case discord_commands.MissingRequiredArgument():
            # Command is missing required arguments
            embed_msg = discord.Embed(title="Missing required argument",
                                      description=f"""{_bot_config['missing_required_argument_description'].format(
                                          bot.command_prefix,
                                          ctx.command)}
                                          \n\n```Error: {error}```""",
                                      color=__embeds_color)
        case discord_commands.CommandInvokeError():
            # Command invoked raised an exception
            embed_msg = discord.Embed(title="Command invoke error",
                                      description=f"""{_bot_config['command_invoke_error_description'].format(
                                          bot.command_prefix,
                                          ctx.command)}
                                          \n\n```Error: {error}```""",
                                      color=__embeds_color)
        case _:
            # Generic error
            embed_msg = discord.Embed(title="An error occurred",
                                      description=f"{_bot_config['generic_error_description']}"
                                                  f"\n\n```Error: {error}```",
                                      color=__embeds_color)
    # Send error message
    await ctx.send(embed=embed_msg)


@bot.command(name='shutdown',
             aliases=['close', 'die'],
             brief=_bot_config['shutdown_brief'],
             description=_bot_config['shutdown_description'])
@discord_commands.has_permissions(administrator=True)
async def shutdown(ctx: discord_commands.Context):
    # Send offline message
    embed_msg = discord.Embed(description=_bot_config['shutdown_message'], color=__embeds_color)
    await ctx.send(embed=embed_msg)
    # Change Odoaldo presence to offline
    await bot.change_presence(status=discord.Status.offline)
    logger.info("Odoaldo is offline")
    # Shutdown bot
    await bot.close()


@bot.command(name='getextensions',
             aliases=['getexts', 'gexts', 'extensions', 'exts'],
             brief=_bot_config['get_extensions_brief'],
             description=_bot_config['get_extensions_description'])
@discord_commands.has_permissions(administrator=True)
async def get_extensions(ctx: discord_commands.Context):
    embed_msg = discord.Embed(description="Available extensions' info:", color=__embeds_color)
    # Send message with available extensions' information
    for extension in _bot_config['available_extensions']:
        if extension in (key.split('.')[-1] for key in bot.extensions.keys()):
            embed_msg.description += f"\n- :white_check_mark: {extension} is currently loaded"
        else:
            embed_msg.description += f"\n- :no_entry: {extension} is currently unloaded"
    await ctx.send(embed=embed_msg)


@bot.command(name='loadextensions',
             aliases=['loadexts', 'lexts'],
             brief=_bot_config['load_extensions_brief'],
             description=_bot_config['load_extensions_description'])
@discord_commands.has_permissions(administrator=True)
async def load_extensions(ctx: discord_commands.Context,
                          *,
                          extensions: str = discord_commands.parameter(description=_bot_config['extensions_list'])):
    embed_msg = discord.Embed(color=__embeds_color)
    embed_msg.description = _bot_config['extensions_output_message_start']
    extensions = extensions.split()
    logger.info(f"Loading extensions: {extensions}")
    # Send message with requested extensions to load information
    for extension in extensions:
        # Check for inconsistencies with available extensions
        if extension not in _bot_config['available_extensions']:
            embed_msg.description += f"\n- :interrobang: {extension} is not an extension"
            logger.warning(f"{extension} extension does not exist")
            continue
        if extension in (key.split('.')[-1] for key in bot.extensions.keys()):
            embed_msg.description += f"\n- :warning: {extension} is already loaded"
            logger.warning(f"{extension} extension is already loaded")
            continue
        # Try and load extension
        try:
            await bot.load_extension(_bot_config['extensions_directory'] + extension)
            logger.info(f"{extension} extension loaded")
            embed_msg.description += f"\n- :white_check_mark: {extension} loaded"
        except Exception as ex:
            logger.error(f"Failed to load {extension} extension: [{type(ex).__name__}: {ex}]")
            embed_msg.description += f"\n- :no_entry: failed to load {extension}"
    await ctx.send(embed=embed_msg)


@bot.command(name='unloadextensions',
             aliases=['unloadexts', 'ulexts'],
             brief=_bot_config['unload_extensions_brief'],
             description=_bot_config['unload_extensions_description'])
@discord_commands.has_permissions(administrator=True)
async def unload_extensions(ctx: discord_commands.Context,
                            *,
                            extensions: str = discord_commands.parameter(description=_bot_config['extensions_list'])):
    embed_msg = discord.Embed(color=__embeds_color)
    embed_msg.description = _bot_config['extensions_output_message_start']
    extensions = extensions.split()
    logger.info(f"Unloading extensions: {extensions}")
    # Send message with requested extensions to unload information
    for extension in extensions:
        # Check for inconsistencies with available extensions
        if extension not in _bot_config['available_extensions']:
            embed_msg.description += f"\n- :interrobang: {extension} is not an extension"
            logger.warning(f"{extension} extension does not exist")
            continue
        if extension not in (key.split('.')[-1] for key in bot.extensions.keys()):
            embed_msg.description += f"\n- :warning: {extension} is already unloaded"
            logger.warning(f"{extension} extension is already unloaded")
            continue
        # Try and unload extension
        try:
            await bot.unload_extension(_bot_config['extensions_directory'] + extension)
            logger.info(f"{extension} extension unloaded")
            embed_msg.description += f"\n- :white_check_mark: {extension} unloaded"
        except Exception as ex:
            logger.error(f"Failed to unload {extension} extension: [{type(ex).__name__}: {ex}]")
            embed_msg.description += f"\n- :no_entry: failed to unload {extension}"
    await ctx.send(embed=embed_msg)


@bot.command(name='reloadextensions',
             aliases=['reloadexts', 'rlexts'],
             brief=_bot_config['reload_extensions_brief'],
             description=_bot_config['reload_extensions_description'])
@discord_commands.has_permissions(administrator=True)
async def reload_extensions(ctx: discord_commands.Context,
                            *,
                            extensions: str = discord_commands.parameter(description=_bot_config['extensions_list'])):
    embed_msg = discord.Embed(color=__embeds_color)
    embed_msg.description = _bot_config['extensions_output_message_start']
    extensions = extensions.split()
    logger.info(f"Reloading extensions: {extensions}")
    # Send message with requested extensions to reload information
    for extension in extensions:
        # Check for inconsistencies with available extensions
        if extension not in _bot_config['available_extensions']:
            embed_msg.description += f"\n- :interrobang: {extension} is not an extension"
            logger.warning(f"{extension} extension does not exist")
            continue
        if extension not in (key.split('.')[-1] for key in bot.extensions.keys()):
            embed_msg.description += f"\n- :warning: {extension} is unloaded"
            logger.warning(f"{extension} extension is unloaded")
            continue
        # Try and reload extension
        try:
            await bot.reload_extension(_bot_config['extensions_directory'] + extension)
            logger.info(f"{extension} extension reloaded")
            embed_msg.description += f"\n- :white_check_mark: {extension} reloaded"
        except Exception as ex:
            logger.error(f"Failed to reload {extension} extension: [{type(ex).__name__}: {ex}]")
            embed_msg.description += f"\n- :no_entry: failed to reload {extension}"
    await ctx.send(embed=embed_msg)


async def main():
    # Log basic bot information
    logger.info(f"{'-' * 80}")
    logger.info(f"{_bot_config['name']} - Version {_bot_config['version']} - {_bot_config['url']}")
    logger.info(f"Licensed under {_bot_config['license']} by {_bot_config['author']} <{_bot_config['author_email']}>")
    logger.info(f"{'-' * 80}")
    logger.info("Attempting to connect to mongo instance")
    # Create mongo util singleton instance
    mongo_uri = 'mongodb://%s:%s@%s:%s' % (
        quote_plus(os_getenv('MONGO_USER')), quote_plus(os_getenv('MONGO_PASSWORD')),
        os_getenv('MONGO_HOST'), os_getenv('MONGO_PORT'))
    mongo_util = MongoUtil(mongo_uri=mongo_uri)
    # Test reachability
    ping = mongo_util.ping()
    if ping:
        logger.critical(f"Odoaldo won't raise from the sandwiches' crumbles")
        logger.critical(f"Failed to locate and connect to mongo instance: [{type(ping).__name__}: {ping}]")
    else:
        logger.info("Mongo instance is reachable")
        # Load extensions' init data
        mongo_util.load_init_data()
        logger.info(f"Available extensions: {_bot_config['available_extensions']}")
        logger.info(f"Loading startup extensions: {_bot_config['startup_extensions']}")
        # Try and load startup extensions
        for extension in _bot_config['startup_extensions']:
            try:
                await bot.load_extension(_bot_config['extensions_directory'] + extension)
                logger.info(f"{extension} extension loaded")
            except Exception as e:
                logger.error(f"Failed to load {extension} extension: [{type(e).__name__}: {e}]")
        await bot.start(__token)


if __name__ == "__main__":
    asyncio_run(main())
