from json import load as json_load
from logging import getLogger
from os.path import join as path_join

from discord import Embed as DiscordEmbed
from discord.ext import commands as discord_commands

from ..utils.mongo import MongoUtil

# Setting up extension logger
logger = getLogger(__name__.split('.', 1)[-1])

# Get extension level config
with open(path_join('bot', 'src', 'extensions', 'mortadella.json'), 'r', encoding='utf-8') as f:
    _config = json_load(f)


class Mortadella(discord_commands.Cog):
    """
    Mortadella bot extension.
    """

    def __init__(self, bot):
        self.bot = bot
        self.__mongo_db = MongoUtil().db()
        self.__jokes_collection = 'mortadella.jokes'
        self.__embeds_color = int(_config['embeds_color'], 16)

    @discord_commands.command(aliases=['morta', 'della', 'mortade'],
                              brief=_config['mortadella_brief'],
                              description=_config['mortadella_description'])
    async def mortadella(self, ctx: discord_commands.Context):
        embed_msg = DiscordEmbed(title=_config['mortadella_message'], color=self.__embeds_color)
        await ctx.send(embed=embed_msg)

    @discord_commands.command(aliases=['j', 'pun'],
                              brief=_config['joke_brief'],
                              description=_config['joke_description'])
    async def joke(self, ctx: discord_commands.Context):
        collection = self.__mongo_db[self.__jokes_collection]
        if collection.count_documents({}):
            embed_msg = DiscordEmbed(description=collection.aggregate([{'$sample': {'size': 1}}]).next()['joke'],
                                     color=self.__embeds_color)
        else:
            embed_msg = DiscordEmbed(description=_config['joke_empty_message'], color=self.__embeds_color)
            logger.warning(f"No objects available in {self.__jokes_collection} mongo collection")
        await ctx.send(embed=embed_msg)

    @discord_commands.command(aliases=['addjoke', 'ajoke', 'addj', 'aj'],
                              brief=_config['add_joke_brief'],
                              description=_config['add_joke_description'])
    async def add_joke(self, ctx: discord_commands.Context,
                       *,
                       joke: str = discord_commands.parameter(description=_config['add_joke_joke'])):
        self.__mongo_db[self.__jokes_collection].insert_one({'joke': joke})
        embed_msg = DiscordEmbed(description=f"New joke added by {ctx.author.mention}",
                                 color=self.__embeds_color)
        logger.info(f"New object added by @{ctx.author.name} to {self.__jokes_collection} mongo collection")
        await ctx.send(embed=embed_msg)


async def setup(bot):
    await bot.add_cog(Mortadella(bot))


async def teardown(bot):
    await bot.remove_cog(Mortadella(bot))
