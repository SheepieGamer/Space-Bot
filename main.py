import discord
from utils import *
from pretty_help import PrettyHelp
from discord.ext import commands, tasks
import settings
import settings.command_info as cmd_info


def main(bot: commands.Bot):
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user.name}')
        await setup_database()
        post_potd.start()
        await load_cogs(bot)


    @bot.command(name=cmd_info.SETUP_POTD_NAME, description=cmd_info.SETUP_POTD_DESC, aliases=cmd_info.SETUP_POTD_ALIASES)
    @commands.has_permissions(administrator=True)
    async def setup_potd(ctx: commands.Context, channel: discord.TextChannel):
        msg = await ctx.reply("Working on it...")
        await add_channel(ctx.guild.id, channel.id)
        await msg.edit(content=f"Channel {channel.mention} has been set up for Space Photo Of The Day!")

    @tasks.loop(hours=24)
    async def post_potd():
        posted = await potd(bot)
        if posted != "Already posted":
            print("Potd posted!")


    bot.run(settings.TOKEN)

if __name__ == "__main__":
    bot = commands.Bot(
        command_prefix=settings.COMMAND_PREFIX, 
        intents=settings.INTENTS, 
        activity=settings.ACTIVITY, 
        help_command=PrettyHelp()
    )
    
    main(bot)