"""
Odoaldo-DiscordBot
Copyright (C) 2021  Massimo Pavoni

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from asyncio import Event, get_event_loop as asyncio_get_event_loop, Queue, TimeoutError
from functools import partial as functools_partial
from itertools import islice
from json import load as json_load
from logging import getLogger
from math import ceil as math_ceil
from os.path import join as path_join
from random import shuffle as random_shuffle

from async_timeout import timeout
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

    # Libraries options and ytdl object
    __ytdl_format_options = _config['ytdl_format_options']
    __ffmpeg_options = _config['ffmpeg_options']
    __ytdl = YoutubeDL(__ytdl_format_options)

    def __init__(self, ctx: discord_commands.Context, source: FFmpegPCMAudio, *, data, volume=0.5):
        # Parent constructor
        super().__init__(source, volume)
        # Get various information about the request and the source data
        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = f"{date[0:4]}.{date[4:6]}.{date[6:8]}"
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.url = data.get('webpage_url')
        self.stream_url = data.get('url')

    def __str__(self):
        return f"**{self.title}** by **{self.uploader}**"

    @classmethod
    async def create(cls, ctx: discord_commands.Context, search, *, loop=None):
        # Static method to create class object
        loop = loop or asyncio_get_event_loop()
        # Run a partial of ytdl extract_info method with search, inside executor
        data = await loop.run_in_executor(None, functools_partial(cls.__ytdl.extract_info, search, download=False,
                                                                  process=False))
        # Find info in data and get first result of playlists
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
        # Get actual info and get first result of playlists
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
        # Create object and audio with ffmpeg options
        return cls(ctx, FFmpegPCMAudio(info['url'], before_options=cls.__ffmpeg_options['before_options'],
                                       options=cls.__ffmpeg_options['options']), data=info)

    @staticmethod
    def parse_duration(duration):
        # Parse seconds duration
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
        self.__embeds_color = int(_config['embeds_color'], 16)

    def create_embed(self):
        # Create organized embed for music currently playing
        embed_msg = (
            DiscordEmbed(title='Now playing', description=f"```\n{self.source.title}\n```", color=self.__embeds_color))
        embed_msg.add_field(name='Duration', value=self.source.duration)
        embed_msg.add_field(name='Requested by', value=self.source.requester.mention)
        embed_msg.add_field(name='Uploader', value=f"[{self.source.uploader}]({self.source.uploader_url})")
        embed_msg.add_field(name='Upload date', value=self.source.upload_date)
        embed_msg.add_field(name='URL', value=f"[Click me]({self.source.url})")
        embed_msg.add_field(name='\u200b', value='\u200b')
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
        # Constructor with bot object and context for playing, specific current music and queue, looping and volume
        self.bot = bot
        self.__ctx = ctx
        self.current: MusicInfo = None
        self.voice: VoiceClient = None
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
                # If loop, recreate the same source
                new_source = await YTDLSource.create(self.__ctx, self.current.source.url, loop=self.bot.loop)
                new_source = MusicInfo(new_source)
                self.current = new_source
            # Then update volume and play
            self.current.source.volume = self.__volume
            self.voice.play(self.current.source, after=self.play_next_song)
            logger.info(f"Playing music on <{self.voice.channel.name}> "
                        f"requested by @{self.current.source.requester.name} in #{self.__ctx.channel.name}")
            await self.current.source.channel.send(embed=self.current.create_embed())
            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(error)
        self.next.set()

    def skip(self):
        # Clear votes pool and skip
        self.skip_votes.clear()
        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        # Stopping clears the queue and disconnects
        self.music_queue.clear()
        if self.voice:
            logger.info(f"Disconnecting from <{self.voice.channel.name}>")
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
        # Get existing voice or create it
        if not self.voice_state:
            self.voice_state = VoiceState(self.bot, ctx)
        return self.voice_state

    def cog_unload(self):
        # Stop voice task
        self.bot.loop.create_task(self.voice_state.stop())

    def cog_check(self, ctx: discord_commands.Context):
        # DM messages check
        if not ctx.guild:
            raise discord_commands.NoPrivateMessage("This command cannot be used in DM channels.")
        return True

    async def cog_before_invoke(self, ctx: discord_commands.Context):
        # Get voice before every command
        self.voice_state = self.get_voice_state(ctx)

    @discord_commands.command(name='connect',
                              aliases=['join', 'voice'],
                              brief=_config['connect_brief'],
                              description=_config['connect_description'])
    async def connect(self, ctx: discord_commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            embed_msg = DiscordEmbed(description=_config['connect_no_voice'].format(ctx.author.mention),
                                     color=self.__embeds_color)
            await ctx.send(embed=embed_msg)
        else:
            destination_channel = ctx.author.voice.channel
            if self.voice_state.voice:
                if ctx.voice_client.channel != destination_channel and ctx.author.guild_permissions.administrator:
                    # Move to voice channel
                    logger.info(f"Moving from <{self.voice_state.voice.channel.name}> to <{destination_channel.name}>")
                    await self.voice_state.voice.move_to(destination_channel)
                    await ctx.message.add_reaction('🆙')
                else:
                    embed_msg = DiscordEmbed(description=_config['connect_no_move'].format(ctx.author.mention),
                                             color=self.__embeds_color)
                    await ctx.send(embed=embed_msg)
            else:
                # Connect to voice channel
                logger.info(f"Connecting to <{destination_channel.name}>")
                self.voice_state.voice = await destination_channel.connect()
                await ctx.message.add_reaction('🆙')

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
            # Change volume
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
            # Show currently playing music
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
            # Toggle pause
            if self.voice_state.voice.is_playing():
                logger.info(f"Music player pausing on <{self.voice_state.voice.channel.name}>")
                self.voice_state.voice.pause()
            elif self.voice_state.voice.is_paused():
                logger.info(f"Music player resuming on <{self.voice_state.voice.channel.name}>")
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
            # Stop music
            logger.info(f"Music player stopping on <{self.voice_state.voice.channel.name}>")
            self.voice_state.music_queue.clear()
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
            if voter.id not in self.voice_state.skip_votes:
                self.voice_state.skip_votes.add(voter.id)
                total_votes = len(self.voice_state.skip_votes)
                if total_votes >= _config['skip_votes_amount'] or voter == self.voice_state.current.source.requester:
                    # Skip music
                    logger.info(f"Music player skipping on <{self.voice_state.voice.channel.name}>")
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
            # Show wanted queue page
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
            embed_msg.description = f"Queue (**{queue_len} tracks):**\n\n{queue}"
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
            # Shuffle music in queue
            logger.info("Music player shuffling queue")
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
            # Remove music
            logger.info(f"Music player removing track at index {index - 1} from queue")
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
            # Toggle current track loop
            logger.info(f"Music player {'disabling' if self.voice_state.loop else 'enabling'} current track repeat")
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
            # Try and enqueue requested music
            try:
                source = await YTDLSource.create(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                raise e
            else:
                logger.info(f"Music player enqueuing track requested by @{source.requester.name}")
                track = MusicInfo(source)
                await self.voice_state.music_queue.put(track)
                embed_msg = DiscordEmbed(description=f"Enqueued {str(source)}", color=self.__embeds_color)
                await ctx.send(embed=embed_msg)


async def setup(bot):
    await bot.add_cog(Music(bot))


async def teardown(bot):
    await bot.remove_cog(Music(bot))
