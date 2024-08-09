import discord
from utils import *
from pretty_help import PrettyHelp
import traceback
from discord.ext import commands
import settings
from economy.job import add_job
from economy import setup_database, initialize_stocks
from economy.stocks import random_price_fluctuation

def main(bot: commands.Bot):
    @bot.event
    async def on_ready():
        try:
            print(f'Logged in as {bot.user} ({bot.user.id})')
            
            # Load cogs
            await load_cogs(bot)
            print("Cogs loaded")

            # Initialize the database
            await setup_database()
            print("Database initialized")

            # Initialize stocks
            await initialize_stocks()

            # Start random price fluctuations
            bot.loop.create_task(random_price_fluctuation())
            
            # Add initial jobs
            await add_job("astronaut", "Astronaut", "Explore space and conduct research.", 5000, 0.2)
            await add_job("engineer", "Space Engineer", "Design and build spacecraft.", 3000, 0.4)
            await add_job("pilot", "Spacecraft Pilot", "Pilot spacecraft on missions.", 4000, 0.3)
            await add_job("scientist", "Space Scientist", "Conduct scientific experiments in space.", 3500, 0.35)
            await add_job("technician", "Space Technician", "Maintain and repair spacecraft.", 2500, 0.5)
            print("Economy, jobs, and the stock market have been initialized.")

        except Exception as e:
            print(f"An error occurred during on_ready: {e}")


    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(embed=make_embed(description="You are missing a required argument. Please check the command usage by executing ``s!help [command]`` and try again.", color=discord.Color.red()))
        elif isinstance(error, commands.BadArgument):
            await ctx.reply(embed=make_embed(description="One or more arguments are invalid. Please check the command usage by executing ``s!help [command]`` and try again.", color=discord.Color.red()))
        elif isinstance(error, commands.CommandNotFound):
            try: cmd = ctx.message.content.split("s!")[1]
            except IndexError: cmd = ctx.message.content.split("> ")[1]
            await ctx.reply(embed=make_embed(description=f"The command **\"{cmd}\"** does not exist. Please check the command name and try again.", color=discord.Color.red()))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.reply(embed=make_embed(description="You do not have the required permissions to use this command.", color=discord.Color.red()))
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.reply(embed=make_embed(description="I do not have the required permissions to execute this command.", color=discord.Color.red()))
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(embed=make_embed(description="You cannot use this command. You might not meet the required conditions.", color=discord.Color.red()))
        elif isinstance(error, commands.CommandOnCooldown):
            pass
        else:
            await ctx.reply(embed=make_embed(description=f"An unexpected error occurred. Please try again later.\nError:```{error}```", color=discord.Color.red()))
            traceback.print_exception(type(error), error, error.__traceback__)

    bot.run(settings.TOKEN)

if __name__ == "__main__":
    bot = commands.Bot(
        command_prefix=settings.COMMAND_PREFIX, 
        intents=settings.INTENTS, 
        activity=settings.ACTIVITY,
        status=settings.STATUS,
        help_command=PrettyHelp()
    )

    main(bot)
