import discord
from discord.ext import commands, tasks
import settings
import settings.command_info as cmd_info
from utils import *

class Other(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.post_potd.start()

    @commands.hybrid_command(name=cmd_info.SETUP_POTD_NAME, description=cmd_info.SETUP_POTD_DESC, aliases=cmd_info.SETUP_POTD_ALIASES)
    @commands.has_permissions(administrator=True)
    async def setup_potd(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        This command sets up a channel for displaying Space Photo Of The Day (POTD) messages.

        Parameters:
        channel (discord.TextChannel): The channel to be set up for POTD messages.

        Returns:
        A success message.
        """
        msg = await ctx.reply("Working on it...")
        await add_channel(ctx.guild.id, channel.id)
        await msg.edit(content=f"Channel {channel.mention} has been set up for Space Photo Of The Day!")

    @tasks.loop(seconds=30)
    async def post_potd(self):
        posted = await potd(self.bot)
        if posted != "Already posted":
            print("POTD posted!")

    @post_potd.before_loop
    async def before_post_potd(self):
        await self.bot.wait_until_ready()
        print("Starting post-potd loop!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Other(bot))
