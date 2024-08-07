import discord
from discord.ext import commands
import settings



class Owner(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.hybrid_command(name="sync-tree")
    @commands.is_owner()
    async def sync_tree(self, ctx: commands.Context) -> None:
        if ctx.author == ctx.bot.user:
            return
        ctx.bot.tree.copy_global_to(guild=ctx.bot.guilds[0])
        ctx.bot.tree.copy_global_to(guild=ctx.bot.guilds[1])
        await ctx.bot.tree.sync()
        print("Tree loaded successfully")
        await ctx.send("Tree loaded successfully")

    @commands.hybrid_command()
    @commands.is_owner()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(fmt)} commands to the current guild.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))