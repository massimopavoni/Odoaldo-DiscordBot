from json import load as json_load
from logging import getLogger
from os.path import join as path_join

from discord.ext import commands as discord_commands

# Setting up extension logger
logger = getLogger(__name__.split('.', 1)[-1])

# Get extension level config
with open(path_join('bot', 'src', 'extensions', 'music.json'), 'r', encoding='utf-8') as f:
    _config = json_load(f)


class Music(discord_commands.Cog):
    """
    Music bot extension.
    """

    def __init__(self, bot):
        self.bot = bot
        self.__embeds_color = int(_config['embeds_color'], 16)


async def setup(bot):
    await bot.add_cog(Music(bot))


async def teardown(bot):
    await bot.remove_cog(Music(bot))
