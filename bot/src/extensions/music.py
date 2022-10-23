from asyncio import get_event_loop as asyncio_get_event_loop
from functools import partial as functools_partial
from json import load as json_load
from logging import getLogger
from os.path import join as path_join

from discord import Embed as DiscordEmbed, FFmpegPCMAudio, PCMVolumeTransformer, VoiceClient
from discord.ext import commands as discord_commands
from yt_dlp import utils as ytdl_utils, YoutubeDL

# Setting up extension logger
logger = getLogger(__name__.split('.', 1)[-1])

# Get extension level config
with open(path_join('bot', 'src', 'extensions', 'music.json'), 'r', encoding='utf-8') as f:
    _config = json_load(f)

# Suppress ytdl noise about console usage from errors
ytdl_utils.bug_reports_message = lambda: ''


class YTDLError(Exception):
    pass


class YTDLSource(PCMVolumeTransformer):
    __ytdl_format_options = _config['ytdl_format_options']
    __ffmpeg_options = _config['ffmpeg_options']
    __ytdl = YoutubeDL(__ytdl_format_options)

    def __init__(self, ctx: discord_commands.Context, source: FFmpegPCMAudio, *, data, volume=0.5):
        super().__init__(source, volume)
        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.url = data.get('webpage_url')
        self.stream_url = data.get('url')

    @classmethod
    async def create(cls, ctx: discord_commands.Context, search, *, loop=None):
        loop = loop or asyncio_get_event_loop()
        data = await loop.run_in_executor(None, functools_partial(cls.__ytdl.extract_info, search, download=False,
                                                                  process=False))

        if not data:
            raise YTDLError(f"Could not find any music that matches `{search}`")
        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError(f"Could not find anything that matches `{search}`")

        webpage_url = process_info['webpage_url']
        processed_info = await loop.run_in_executor(None, functools_partial(cls.__ytdl.extract_info, webpage_url,
                                                                            download=False))

        if processed_info is None:
            raise YTDLError(f"Could not fetch `{webpage_url}`")

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError(f"Could not retrieve any matches for `{webpage_url}`")

        return cls(ctx, FFmpegPCMAudio(info['url'], **cls.__ffmpeg_options), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))
        return ':'.join(duration)


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
                if bot_voice.channel.id != author_voice.channel.id:
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

    @discord_commands.command(name='play',
                              aliases=['music'],
                              brief=_config['play_brief'],
                              description=_config['play_description'])
    async def play(self, ctx, *, search):
        await self.connect(ctx)
        async with ctx.typing():
            player = await YTDLSource.create(ctx, search, loop=self.bot.loop)
            ctx.voice_client.play(player)
        embed_msg = DiscordEmbed(title=f"Now playing: {player.title}", color=self.__embeds_color)
        await ctx.send(embed=embed_msg)


async def setup(bot):
    await bot.add_cog(Music(bot))


async def teardown(bot):
    await bot.remove_cog(Music(bot))
