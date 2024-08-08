import discord
from utils import *
from pretty_help import PrettyHelp
import traceback
from discord.ext import commands
import settings

def main(bot: commands.Bot):
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user.name}')
        await setup_database()
        await load_cogs(bot)

    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("You are missing a required argument. Please check the command usage by executing ``s!help [command]`` and try again.")
        elif isinstance(error, commands.BadArgument):
            await ctx.reply("One or more arguments are invalid. Please check the command usage by executing ``s!help [command]`` and try again.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.reply("This command does not exist. Please check the command name and try again.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.reply("You do not have the required permissions to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.reply("I do not have the required permissions to execute this command.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply("You cannot use this command. You might not meet the required conditions.")
        else:
            await ctx.reply("An unexpected error occurred. Please try again later.")
            traceback.print_exception(type(error), error, error.__traceback__)

    bot.run(settings.TOKEN)

if __name__ == "__main__":
    bot = commands.Bot(
        command_prefix=settings.COMMAND_PREFIX, 
        intents=settings.INTENTS, 
        activity=settings.ACTIVITY, 
        help_command=PrettyHelp()
    )

    main(bot)
