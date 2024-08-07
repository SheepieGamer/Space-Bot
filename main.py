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