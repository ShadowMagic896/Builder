import logging
from typing import Optional

import discord
import wavelink
from discord import ClientException, app_commands
from discord.ext import commands

from settings import DEVELOPMENT_GUILD_IDS

from ..utils.abc import BaseCog
from ..utils.bot_abc import Builder, BuilderContext, BuilderWave, QueueType
from ..utils.errors import AlreadyConnected, NotConnected


class Jams(BaseCog):
    def __init__(self, bot: Builder) -> None:
        logger = logging.getLogger("wavelink")
        logger.setLevel(logging.INFO)
        super().__init__(bot)

    @commands.command()
    @app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
    async def _create_node(self, ctx: BuilderContext):
        await aquire_nodes(self.bot)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node: <{node.identifier}> is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, player: BuilderWave, track: wavelink.Track, reason: str
    ):
        if reason in {"FINISHED", "REPLACED"}:
            print(f"Track: <{track.title}> finished!")
            track = await player.play_next()
            if track is None:
                await player.stop()
                embed = await player.ctx.format(
                    title="Queue Empty",
                    desc="The queue is empty, the player has been stopped.",
                )
                await player.ctx.send(embed=embed)
            else:
                await self.playing(player.ctx)

    @commands.hybrid_group()
    async def jams(self, ctx: BuilderContext) -> None:
        pass

    @jams.command()
    async def connect(self, ctx: BuilderContext, queue_type: QueueType):
        """Connects the bot to a voice channel"""
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            raise NotConnected("You need to be in a voice channel to use this command")

        channel = ctx.author.voice.channel
        try:
            await channel.connect(
                cls=BuilderWave(ctx, QueueType(queue_type)), self_deaf=True
            )
        except ClientException as err:
            raise AlreadyConnected(
                "I am already connected to a voice channel! Please ask the the owner to disconnect me"
            )

        embed = await ctx.format(
            title="Successfully Connected",
            desc="Lets get those tunes rolling!",
        )
        await ctx.send(embed=embed)

    @jams.command()
    async def play(self, ctx: BuilderContext):
        """Plays the next song, then removes it from the queue"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        track = await player.play_next()
        if track is None:
            raise ValueError("The queue is empty!")
        embed = await fmt_track_info(ctx, track)
        embed.title = "Now Jamming Out"

        await ctx.send(embed=embed)

    @jams.command()
    async def skip(self, ctx: BuilderContext):
        """Skips the currently playing song"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        if player.queue.is_empty:
            await player.stop()
        if player.is_playing():
            if player.queue.is_empty:
                ...
            else:
                await player.play_next()
        await self.playing(ctx)

    @jams.command()
    async def pause(self, ctx: BuilderContext):
        """Pauses music playback"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        await player.set_pause(True)

        embed = await ctx.format(title="Paused Jams")
        await ctx.send(embed=embed)

    @jams.command()
    async def resume(self, ctx: BuilderContext):
        """Resumes music playback"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        await player.set_pause(False)

        embed = await ctx.format(title="Jams Unpaused")
        await ctx.send(embed=embed)

    @jams.command()
    async def stop(self, ctx: BuilderContext):
        """Stops music playback"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        await player.disconnect()
        player.cleanup()

        embed = await ctx.format(title="Stopped Jams")
        await ctx.send(embed=embed)

    @jams.command()
    async def playing(self, ctx: BuilderContext):
        """Shows the currently playing song"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        if not player.is_playing():
            embed = await ctx.format(
                title="Nothing is playing",
                desc="Use `/jams queue add <query>` to add a song to the queue, or `/jams play` to start the queue!",
            )
            await ctx.send(embed=embed)
            return
        else:
            track = player.track

        embed = await fmt_track_info(ctx, track)
        embed.title = "Currently Playing..."
        embed.description += f"**Current Time:** `{fmt_time(player.position)}` / `{fmt_time(track.duration)}`\n"
        embed.description += (
            f"**Is Playing:** `{'Yes' if player.is_playing() else 'No'}`\n"
        )
        embed.description += f"**Is Paused:** `{'Yes' if player.is_paused() else 'No'}`"
        await ctx.send(embed=embed)

    @jams.group()
    async def queue(self, ctx: BuilderContext):
        pass

    @queue.command()
    async def set_type(self, ctx: BuilderContext, queue_type: QueueType):
        """Sets the queue type"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        player.queue_type = QueueType(queue_type)

        if queue_type == QueueType.default:
            desc = "The queue is now a **`default`** queue, meainng it will play every song once, in order, then stop."
        elif queue_type == QueueType.loop:
            desc = "The queue is now a **`loop`** queue, meaning it will play every song once, in order, then repeat the queue."
        elif queue_type == QueueType.shuffle:
            desc = "The queue is now a **`shuffle`** queue, meaning it will play every song in a random order."

        embed = await ctx.format(title="Queue Type Set", desc=desc)
        await ctx.send(embed=embed)

    @queue.command()
    async def view(self, ctx: BuilderContext):
        """Shows you the current queue"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        embed = await ctx.format(title=f"Viewing `{len(player.queue)}` Tracks", desc="")
        for i, track in enumerate(player.queue):
            fmt_count = f"{i+1}".rjust(2, "0")
            embed.description += f"`{fmt_count}`: [{track.info['title']}]({track.info['uri']}) [`{fmt_time(track.info['length'], div_by=True)}`]\n"

        await ctx.send(embed=embed)

    @queue.command()
    @app_commands.describe(
        track="The query for the track you want to add to the queue",
        location="Where to place the song",
    )
    @app_commands.choices(
        location=[
            app_commands.Choice(name="Front of Queue", value=0),
            app_commands.Choice(name="End of Queue", value=1),
        ]
    )
    async def add(
        self,
        ctx: BuilderContext,
        track: wavelink.YouTubeTrack,
        location: Optional[app_commands.Choice[int]] = 1,
    ):
        """Add a track to the queue"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        if location == 0:
            player.queue.put_at_front(track)
        else:
            player.queue.put(track)

        embed = await fmt_track_info(ctx, track)
        embed.title = "Track Added to Queue"

        await ctx.send(embed=embed)

    @queue.command()
    @app_commands.describe(
        track_num="The number of the track you want to remove from the queue (not zero-indexed)"
    )
    async def remove(self, ctx: BuilderContext, track_num: int):
        """Remove a track from the queue"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        try:
            track = player.queue[track_num - 1]
            del player.queue[track_num - 1]
        except IndexError:
            raise ValueError("Could not find that track in the queue.")

        embed = await fmt_track_info(ctx, track)
        embed.title = "Removed Track"
        await ctx.send(embed=embed)

    @queue.command()
    async def clear(self, ctx: BuilderContext):
        """Clear the queue"""
        if (player := ctx.voice_client) is None:
            raise NotConnected("I am not connected to a channel!")

        queue = player.queue.copy()
        player.queue.clear()
        embed = await ctx.format(
            title="Queue Cleared", desc=f"Cleared `{len(queue)}` tracks"
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        client = member.guild.voice_client
        voice = member.guild.me.voice
        if (
            before.channel is not None and voice is not None
        ):  # The user left a voice channel and we are in one
            if voice.channel == before.channel:  # They left the channel I am in
                if (
                    len(voice.channel.members) == 1
                ):  # The only member in the channel is me
                    # Cleanup VoiceClient and leave channel
                    client.cleanup()
                    await client.disconnect()


def fmt_time(time: int, div_by: bool = False) -> str:
    if div_by:
        time /= 1000
    minutes, seconds = divmod(time, 60)
    return f"{int(minutes):02}:{int(seconds):02}"


async def fmt_track_info(ctx: BuilderContext, track: wavelink.abc.Playable):
    return await ctx.format(
        title="foobar reee",  # Should be set by whatever command is calling this
        desc=f"**Name:** `{track.title}`\n"
        f"**Duration:** `{fmt_time(track.duration)}`\n"
        f"**URL:** `{track.uri or '*Not Available, Sorry*'}`\n"
        f"**Author:** `{track.author or '*Not Available, Sorry*'}`\n",
    )


async def aquire_nodes(bot: Builder) -> None:
    await wavelink.NodePool.create_node(
        bot=bot, host="127.0.0.1", port=2334, password="youshallnotpass"
    )


async def setup(bot: Builder) -> None:
    await bot.add_cog(Jams(bot))
