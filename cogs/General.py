import discord
from discord.ext import commands
import settings


class General(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))