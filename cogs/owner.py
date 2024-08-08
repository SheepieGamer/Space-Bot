import discord
from discord.ext import commands
import settings



class Owner(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.hybrid_command(name="sync-tree")
    @commands.is_owner()
    async def sync_tree(self, ctx: commands.Context) -> None:
        msg: discord.Message = await ctx.reply("Syncing..")
        if ctx.author == ctx.bot.user:
            return
        ctx.bot.tree.copy_global_to(guild=ctx.bot.guilds[0])
        ctx.bot.tree.copy_global_to(guild=ctx.bot.guilds[1])
        await ctx.bot.tree.sync()
        print("Tree loaded successfully")
        await msg.edit(content="Tree loaded successfully")

    @commands.hybrid_command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        msg: discord.Message = await ctx.reply("Syncing...")
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await msg.edit(content=f"Synced {len(fmt)} commands to the current guild.")

    @commands.command(aliases=["reload"])
    @commands.is_owner()
    async def reload_cog(self, ctx: commands.Context, cog: str):
        if not cog.endswith(".py"):
            cog += ".py"
        try:
            module = f"cogs.{cog[:-3]}"
            await ctx.bot.reload_extension(module)
            await ctx.send(f"Reloaded {cog}")
            print(f"{cog} successfully reloaded")
        except Exception as e:
            await ctx.send(f"Error reloading {cog}: {str(e)}")

    @commands.command(aliases=["unload"])
    @commands.is_owner()
    async def unload_cog(self, ctx: commands.Context, cog: str):
        if not cog.endswith(".py"):
            cog += ".py"
        try:
            module = f"cogs.{cog[:-3]}"
            await ctx.bot.unload_extension(module)
            await ctx.send(f"Unloaded {cog}")
            print(f"{cog} successfully unloaded")
        except Exception as e:
            await ctx.send(f"Error unloading {cog}: {str(e)}")
    
    @commands.command(aliases=["load"])
    @commands.is_owner()
    async def load_cog(self, ctx: commands.Context, cog: str):
        if not cog.endswith(".py"):
            cog += ".py"
        try:
            module = f"cogs.{cog[:-3]}"
            await ctx.bot.load_extension(module)
            await ctx.send(f"Loaded {cog}")
            print(f"{cog} successfully loaded")
        except Exception as e:
            await ctx.send(f"Error loading {cog}: {str(e)}")

    @commands.hybrid_command(name='serverlist', description='Lists all servers the bot is a member of.')
    @commands.is_owner()
    async def serverlist(self, ctx: commands.Context):
        """Lists all servers the bot is a member of (owner only)."""
        servers = [guild.name for guild in self.bot.guilds]
        embed=discord.Embed(
            description="\n".join(servers) if servers else "The bot is not in any servers.",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))