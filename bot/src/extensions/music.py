from asyncio import Event, get_event_loop as asyncio_get_event_loop, Queue, TimeoutError
from functools import partial as functools_partial
from itertools import islice
from json import load as json_load
from logging import getLogger
from math import ceil as math_ceil
from os.path import join as path_join
from random import shuffle as random_shuffle

from async_timeout import timeout
from discord import Embed as DiscordEmbed, FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands as discord_commands
from yt_dlp import utils as ytdl_utils, YoutubeDL

# Setting up extension logger
logger = getLogger(__name__.split('.', 1)[-1])

# Get extension level config
with open(path_join('bot', 'src', 'extensions', 'music.json'), 'r', encoding='utf-8') as f:
    _config = json_load(f)

# Suppress ytdl noise about console usage from errors
ytdl_utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    """
    Voice specific error class.
    """

    pass


class YTDLError(Exception):
    """
    YTDL specific error class.
    """

    pass


class YTDLSource(PCMVolumeTransformer):
    """
    YTDLSource class for music.
    """

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
        self.upload_date = f"{date[6:8]}.{date[4:6]}.{date[0:4]}"
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.url = data.get('webpage_url')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

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
            raise YTDLError(f"Could not fetch \"{webpage_url}\"")
        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError(f"Could not retrieve any matches for `{webpage_url}`")
        return cls(ctx, FFmpegPCMAudio(info['url'], before_options=cls.__ffmpeg_options['before_options'],
                                       options=cls.__ffmpeg_options['options']), data=info)

    @staticmethod
    def parse_duration(duration):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        duration = []
        if days > 0:
            duration.append(f"{days}d")
        if hours > 0:
            duration.append(f"{hours}h")
        if minutes > 0:
            duration.append(f"{minutes}'")
        if seconds > 0:
            duration.append(f"{seconds}''")
        return ' '.join(duration)


class MusicInfo:
    """
    MusicInfo class for embed.
    """

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester
        self.__embeds_color = int(_config['embeds_color'], 16)

    def create_embed(self):
        embed_msg = (DiscordEmbed(title='Now playing',
                                  description='```\n{0.source.title}\n```'.format(self),
                                  color=self.__embeds_color))
        embed_msg.add_field(name='Duration', value=self.source.duration)
        embed_msg.add_field(name='Requested by', value=self.requester.mention)
        embed_msg.add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
        embed_msg.add_field(name='URL', value='[Click]({0.source.url})'.format(self))
        embed_msg.set_thumbnail(url=self.source.thumbnail)
        return embed_msg


class MusicQueue(Queue):
    """
    MusicQueue class.
    """

    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random_shuffle(self._queue)

    def remove(self, index):
        del self._queue[index]


class VoiceState:
    """
    VoiceState class for bot voice.
    """

    def __init__(self, bot: discord_commands.Bot, ctx: discord_commands.Context):
        self.bot = bot
        self.__ctx = ctx
        self.current = None
        self.voice = None
        self.next = Event()
        self.music_queue = MusicQueue()
        self.__loop = False
        self.__volume = _config['starting_volume']
        self.skip_votes = set()
        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self.__loop

    @loop.setter
    def loop(self, value):
        self.__loop = value

    @property
    def volume(self):
        return self.__volume

    @volume.setter
    def volume(self, value):
        self.__volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            if not self.__loop:
                # Try to get the next song within an amount of seconds
                try:
                    async with timeout(_config['voice_timeout']):
                        self.current = await self.music_queue.get()
                except TimeoutError:
                    # If no song is added to the queue, stop
                    self.bot.loop.create_task(self.stop())
                    return
            else:
                new_source = await YTDLSource.create(self.__ctx, self.current.source.url, loop=self.bot.loop)
                new_source = MusicInfo(new_source)
                self.current = new_source
            self.current.source.volume = self.__volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())
            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(error)
        self.next.set()

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.music_queue.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(discord_commands.Cog):
    """
    Music bot extension.
    """

    def __init__(self, bot: discord_commands.Bot):
        self.bot = bot
        self.description = _config['extension_description']
        self.__embeds_color = int(_config['embeds_color'], 16)
        self.voice_state: VoiceState = None

    def get_voice_state(self, ctx: discord_commands.Context):
        if not self.voice_state:
            self.voice_state = VoiceState(self.bot, ctx)
        return self.voice_state

    def cog_unload(self):
        self.bot.loop.create_task(self.voice_state.stop())

    def cog_check(self, ctx: discord_commands.Context):
        if not ctx.guild:
            raise discord_commands.NoPrivateMessage("This command cannot be used in DM channels.")
        return True

    async def cog_before_invoke(self, ctx: discord_commands.Context):
        self.voice_state = self.get_voice_state(ctx)

    @discord_commands.command(name='connect',
                              aliases=['join', 'voice'],
                              brief=_config['connect_brief'],
                              description=_config['connect_description'])
    async def connect(self, ctx: discord_commands.Context):
        destination = ctx.author.voice.channel
        if self.voice_state.voice:
            await self.voice_state.voice.move_to(destination)
        else:
            self.voice_state.voice = await destination.connect()

    @discord_commands.command(name='disconnect',
                              aliases=['leave'],
                              brief=_config['disconnect_brief'],
                              description=_config['disconnect_description'])
    async def disconnect(self, ctx: discord_commands.Context):
        if not self.voice_state.voice:
            embed_msg = DiscordEmbed(description=_config['disconnect_no_voice'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            await self.voice_state.stop()
            self.voice_state = None

    @discord_commands.command(name='setvolume',
                              aliases=['volume', 'vol'],
                              brief=_config['set_volume_brief'],
                              description=_config['set_volume_description'])
    async def set_volume(self, ctx: discord_commands.Context,
                         volume: int = discord_commands.parameter(description=_config['set_volume_volume'])):
        embed_msg = DiscordEmbed(color=self.__embeds_color)
        if not self.voice_state.is_playing:
            embed_msg.description = _config['no_player']
            await ctx.send(embed=embed_msg)
        else:
            if volume < 0:
                volume = 0
            elif volume > 100:
                volume = 100
            self.voice_state.volume = volume / 100
            embed_msg.description = _config['set_volume_set'].format(volume)
            await ctx.send(embed=embed_msg)

    @discord_commands.command(name='nowplaying',
                              aliases=['playingnow', 'playing', 'current'],
                              brief=_config['now_playing_brief'],
                              description=_config['now_playing_description'])
    async def now_playing(self, ctx: discord_commands.Context):
        if not self.voice_state.is_playing:
            embed_msg = DiscordEmbed(description=_config['no_player'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            await ctx.send(embed=self.voice_state.current.create_embed())

    @discord_commands.command(name='pauseresume',
                              aliases=['pause', 'resume'],
                              brief=_config['pause_resume_brief'],
                              description=_config['pause_resume_description'])
    async def pause_resume(self, ctx: discord_commands.Context):
        if not self.voice_state.is_playing:
            embed_msg = DiscordEmbed(description=_config['no_player'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            if self.voice_state.is_playing:
                if self.voice_state.voice.is_playing():
                    self.voice_state.voice.pause()
                    await ctx.message.add_reaction('⏯️')
                elif self.voice_state.voice.is_paused():
                    self.voice_state.voice.resume()
                    await ctx.message.add_reaction('⏯️')

    @discord_commands.command(name='stop',
                              aliases=['nomusic'],
                              brief=_config['stop_brief'],
                              description=_config['stop_description'])
    async def stop(self, ctx: discord_commands.Context):
        if not self.voice_state.is_playing:
            embed_msg = DiscordEmbed(description=_config['no_player'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            self.voice_state.music_queue.clear()
            if not self.voice_state.is_playing:
                self.voice_state.voice.stop()
                await ctx.message.add_reaction('⏹️')

    @discord_commands.command(name='skip',
                              aliases=['next'],
                              brief=_config['skip_brief'],
                              description=_config['skip_description'].format(_config['skip_votes_amount']))
    async def skip(self, ctx: discord_commands.Context):
        if not self.voice_state.is_playing:
            embed_msg = DiscordEmbed(description=_config['no_player'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            voter = ctx.author
            if voter == self.voice_state.current.requester:
                await ctx.message.add_reaction('⏭️')
                self.voice_state.skip()
            elif voter.id not in self.voice_state.skip_votes:
                self.voice_state.skip_votes.add(voter.id)
                total_votes = len(self.voice_state.skip_votes)
                if total_votes >= _config['skip_votes_amount']:
                    await ctx.message.add_reaction('⏭️')
                    self.voice_state.skip()
                else:
                    embed_msg = DiscordEmbed(
                        description=_config['skip_vote_added'].format(total_votes, _config['skip_votes_amount']),
                        color=self.__embeds_color)
                    await ctx.send(embed=embed_msg)
            else:
                embed_msg = DiscordEmbed(description=_config['skip_vote_already_added'].format(ctx.author.mention),
                                         color=self.__embeds_color)
                await ctx.send(embed=embed_msg)

    @discord_commands.command(name='showqueue',
                              aliases=['queue'],
                              brief=_config['show_queue_brief'],
                              description=_config['show_queue_description'])
    async def show_queue(self, ctx: discord_commands.Context,
                         page: int = discord_commands.parameter(description=_config['show_queue_page'], default=1)):
        embed_msg = DiscordEmbed(color=self.__embeds_color)
        queue_len = len(self.voice_state.music_queue)
        if not queue_len:
            embed_msg.description = _config['queue_empty']
        else:
            page_density = _config['show_queue_page_density']
            pages = math_ceil(queue_len / page_density)
            if page < 1:
                page = 1
            elif page > pages:
                page = pages
            start = (page - 1) * page_density
            end = start + page_density
            queue = '\n'.join([f"`{i + 1}.` [**{music.source.title}**]({music.source.url})" for i, music in
                               enumerate(self.voice_state.music_queue[start:end], start=start)])
            embed_msg.description = f"**{queue_len} tracks:**\n\n{queue}"
            embed_msg.set_footer(text=f"Page {page}/{pages}")
        await ctx.send(embed=embed_msg)

    @discord_commands.command(name='shufflequeue',
                              aliases=['shuffle'],
                              brief=_config['shuffle_queue_brief'],
                              description=_config['shuffle_queue_description'])
    async def shuffle_queue(self, ctx: discord_commands.Context):
        if not len(self.voice_state.music_queue):
            embed_msg = DiscordEmbed(description=_config['queue_empty'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            self.voice_state.music_queue.shuffle()
            await ctx.message.add_reaction('🔀')

    @discord_commands.command(name='removefromqueue',
                              aliases=['removequeue', 'removemusic', 'remove'],
                              brief=_config['remove_from_queue_brief'],
                              description=_config['remove_from_queue_description'])
    async def remove_from_queue(self, ctx: discord_commands.Context,
                                index: int = discord_commands.parameter(description=_config['remove_from_queue_index'],
                                                                        default=1)):
        if not len(self.voice_state.music_queue):
            embed_msg = DiscordEmbed(description=_config['queue_empty'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            self.voice_state.music_queue.remove(index - 1)
            await ctx.message.add_reaction('⤴️')

    @discord_commands.command(name='looptrack',
                              aliases=['loop', 'repeat'],
                              brief=_config['loop_track_brief'],
                              description=_config['loop_track_description'])
    async def loop_track(self, ctx: discord_commands.Context):
        if not self.voice_state.is_playing:
            embed_msg = DiscordEmbed(description=_config['no_player'], color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            self.voice_state.loop = not self.voice_state.loop
            await ctx.message.add_reaction('🔂')

    @discord_commands.command(name='play',
                              aliases=['music'],
                              brief=_config['play_brief'],
                              description=_config['play_description'])
    async def play(self, ctx: discord_commands.Context, *,
                   search: str = discord_commands.parameter(description=_config['play_search'])):
        if not self.voice_state.voice:
            await ctx.invoke(self.connect)
        async with ctx.typing():
            try:
                source = await YTDLSource.create(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                raise e
            else:
                track = MusicInfo(source)
                await self.voice_state.music_queue.put(track)
                embed_msg = DiscordEmbed(description=f"Enqueued {str(source)}", color=self.__embeds_color)
                await ctx.send(embed=embed_msg)

    @connect.before_invoke
    @play.before_invoke
    async def ensure_voice_state(self, ctx: discord_commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise discord_commands.CommandError("User is not connected to any voice channel.")
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise discord_commands.CommandError("Bot is already in a voice channel.")


async def setup(bot):
    await bot.add_cog(Music(bot))


async def teardown(bot):
    await bot.remove_cog(Music(bot))
