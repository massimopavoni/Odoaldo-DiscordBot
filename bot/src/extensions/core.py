from json import load as json_load
from logging import getLogger
from os.path import join as path_join

from discord import Embed as DiscordEmbed
from discord.ext import commands as discord_commands

from ..utils.mongo import MongoUtil

# Setting up extension logger
logger = getLogger(__name__.split('.', 1)[-1])

# Get bot and extension level config
with open(path_join('bot', 'bot_config.json'), 'r', encoding='utf-8') as f:
    _bot_config = json_load(f)
with open(path_join('bot', 'src', 'extensions', 'core.json'), 'r', encoding='utf-8') as f:
    _config = json_load(f)


class Core(discord_commands.Cog):
    """
    Core bot extension.
    """

    def __init__(self, bot):
        self.bot = bot
        self.__mongo_util = MongoUtil()
        self.__embeds_color = int(_config['embeds_color'], 16)

    @discord_commands.command(aliases=['purge'],
                              brief=_config['clear_brief'],
                              description=_config['clear_description'])
    @discord_commands.has_permissions(administrator=True)
    async def clear(self, ctx: discord_commands.Context,
                    amount: int = discord_commands.parameter(default=3, description=_config['clear_amount'])):
        logger.info(f"Clearing {amount} messages from #{ctx.channel}")
        await ctx.channel.purge(limit=amount + 1)

    @discord_commands.command(aliases=['marco'],
                              brief=_config['ping_brief'],
                              description=_config['ping_description'])
    async def ping(self, ctx: discord_commands.Context):
        latency = str(round(self.bot.latency * 1000))
        embed_msg = DiscordEmbed(
            description=f":ping_pong: {'Polo' if ctx.invoked_with.lower() == '.marco' else 'Pong'}! "
                        f"with {latency}ms",
            color=self.__embeds_color)
        logger.info(f"Bot latency: {latency}ms")
        await ctx.send(embed=embed_msg)

    @discord_commands.command(aliases=['odoaldo'],
                              brief=_config['info_brief'],
                              description=_config['info_description'])
    async def info(self, ctx: discord_commands.Context):
        embed_msg = DiscordEmbed(title=_bot_config['name'], color=self.__embeds_color)
        embed_msg.add_field(name='Version', value=f"`{_bot_config['version']}`")
        embed_msg.add_field(name='Source', value=f"[GitHub repository]({_bot_config['url']})")
        embed_msg.add_field(name='\u200b', value='\u200b')
        embed_msg.add_field(name='License', value=_bot_config['license'])
        embed_msg.add_field(name='Author', value=_bot_config['author'])
        embed_msg.add_field(name='\u200b', value='\u200b')
        embed_msg.add_field(name='\u200b', value=_config['info_message'], inline=False)
        await ctx.send(embed=embed_msg)

    @discord_commands.command(aliases=['chisono'],
                              brief=_config['whoami_brief'],
                              description=_config['whoami_description'])
    async def whoami(self, ctx: discord_commands.Context):
        embed_msg = DiscordEmbed(description=f"You are {ctx.message.author.mention}", color=self.__embeds_color)
        await ctx.send(embed=embed_msg)

    @discord_commands.command(
        aliases=['resetdatabase', 'databasereset', 'resetdata', 'datareset', 'resetdb', 'dbreset'],
        brief=_config['reset_database_brief'],
        description=_config['reset_database_description'])
    @discord_commands.has_permissions(administrator=True)
    async def reset_database(self, ctx: discord_commands.Context):
        self.__mongo_util.load_init_data(reset=True)
        embed_msg = DiscordEmbed(description=_config['reset_database_message'], color=self.__embeds_color)
        await ctx.send(embed=embed_msg)


async def setup(bot):
    await bot.add_cog(Core(bot))


async def teardown(bot):
    await bot.remove_cog(Core(bot))
