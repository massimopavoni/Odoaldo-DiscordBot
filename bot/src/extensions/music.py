from json import load as json_load
from logging import getLogger
from os.path import join as path_join

from discord import Embed as DiscordEmbed, PCMVolumeTransformer, VoiceClient
from discord.ext import commands as discord_commands
from yt_dlp import utils as ytdl_utils, YoutubeDL

# Setting up extension logger
logger = getLogger(__name__.split('.', 1)[-1])

# Get extension level config
with open(path_join('bot', 'src', 'extensions', 'music.json'), 'r', encoding='utf-8') as f:
    _config = json_load(f)
__ytdl_format_options = _config['ytdl_format_options']
__ffmpeg_options = _config['ffmpeg_options']

# Suppress ytdl noise about console usage from errors
ytdl_utils.bug_reports_message = lambda: ''
__ytdl = YoutubeDL(__ytdl_format_options)


class YTDLSource(PCMVolumeTransformer):
    pass


class Music(discord_commands.Cog):
    """
    Music bot extension.
    """

    def __init__(self, bot: discord_commands.Bot):
        self.bot = bot
        self.description = _config['extension_description']
        self.__embeds_color = int(_config['embeds_color'], 16)

    @discord_commands.command(name='connect',
                              aliases=['join', 'voice'],
                              brief=_config['connect_brief'],
                              description=_config['connect_description'])
    async def connect(self, ctx: discord_commands.Context):
        author_voice = ctx.author.voice
        # Author has to be in a voice channel
        if author_voice:
            bot_voice: VoiceClient = ctx.voice_client
            # Check if bot is already connected
            if bot_voice:
                # Move bot if voice channel is different
                if bot_voice.channel.id == author_voice.channel.id:
                    embed_msg = DiscordEmbed(description=_config['connect_already_voice'].format(ctx.author.mention),
                                             color=self.__embeds_color)
                    await ctx.send(embed=embed_msg)
                else:
                    logger.info(f"Bot moving from <{bot_voice.channel.name} to <{author_voice.channel.name}")
                    await bot_voice.move_to(author_voice.channel)
            else:
                logger.info(f"Bot connecting to <{author_voice.channel.name}")
                await author_voice.channel.connect()
        else:
            embed_msg = DiscordEmbed(description=_config['connect_no_voice'].format(ctx.author.mention),
                                     color=self.__embeds_color)
            await ctx.send(embed=embed_msg)

    @discord_commands.command(name='disconnect',
                              aliases=['leave', 'stop'],
                              brief=_config['disconnect_brief'],
                              description=_config['disconnect_description'])
    async def disconnect(self, ctx: discord_commands.Context):
        bot_voice: VoiceClient = ctx.voice_client
        # Disconnect if bot is connected
        if bot_voice:
            logger.info(f"Bot disconnecting from <{bot_voice.channel.name}")
            await bot_voice.disconnect()
        else:
            embed_msg = DiscordEmbed(description=_config['disconnect_no_voice'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)


async def setup(bot):
    await bot.add_cog(Music(bot))


async def teardown(bot):
    await bot.remove_cog(Music(bot))
