import discord
from discord.ext import commands
import random
from utils import *
import aiohttp
import settings

class General(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='ping', description='Replies with Pong! and the bot\'s latency.')
    async def ping(self, ctx: commands.Context):
        """Replies with Pong! and the bot's latency in milliseconds."""
        latency = round(self.bot.latency * 1000)  # Convert to milliseconds
        await ctx.reply(f'Pong! {latency}ms')

    @commands.hybrid_command(name='userinfo', description='Displays information about a user.')
    async def userinfo(self, ctx: commands.Context, user: discord.User = None):
        """Displays information about a user, including their ID, name, discriminator, and whether they are a bot."""
        user: discord.Member = user or ctx.author
        embed = discord.Embed(
            title=f"User Info: {user}",
            color=discord.Color.blue()
        )
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Name", value=user.name, inline=True)
        embed.add_field(name="Bot", value=user.bot, inline=True)
        embed.add_field(name="Display Name", value=user.display_name, inline=True)
        embed.set_thumbnail(url=user.avatar.url)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='serverinfo', description='Displays information about the server.')
    async def serverinfo(self, ctx: commands.Context):
        """Displays information about the server, including its ID, owner, member count, and creation date."""
        server = ctx.guild
        embed = discord.Embed(
            title=f"Server Info: {server.name}",
            color=discord.Color.green()
        )
        embed.add_field(name="ID", value=server.id, inline=True)
        embed.add_field(name="Owner", value=server.owner, inline=True)
        embed.add_field(name="Members", value=server.member_count, inline=True)
        embed.add_field(name="Created At", value=server.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        
        if server.icon:
            embed.set_thumbnail(url=server.icon.url)
        else:
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='roll', description='Rolls a random number between 1 and the specified maximum.')
    async def roll(self, ctx: commands.Context, max: int = 100):
        """Rolls a random number between 1 and the specified maximum value (default is 100)."""
        result = random.randint(1, max)
        await ctx.reply(f'🎲 You rolled a {result}!')

    @commands.hybrid_command(name='say', description='Makes the bot say a message.')
    @commands.has_permissions(administrator=True)
    async def say(self, ctx: commands.Context, *, message: str):
        """Deletes the command message and makes the bot say the provided message (admin only)."""
        await ctx.message.delete()
        await ctx.send(message)

    @commands.hybrid_command(name='avatar', description='Displays the avatar of a user.')
    async def avatar(self, ctx: commands.Context, user: discord.User = None):
        """Displays the avatar of a user. If no user is specified, it displays the avatar of the command author."""
        user = user or ctx.author
        embed = discord.Embed(
            title=f"{user}'s Avatar",
            color=discord.Color.purple()
        )
        embed.set_image(url=user.avatar.url)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='invite', description='Sends an invite link to add the bot to your server.')
    async def invite(self, ctx: commands.Context):
        """Provides an invite link to add the bot to another server."""
        invite_link = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8"
        await ctx.reply(f"Add me to your server using [this link]({invite_link})!")

    @commands.hybrid_command(name='fact', description='Fetches a random fact from a facts API.')
    async def fact(self, ctx: commands.Context):
        """Fetches and displays a random fact from an external API."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://uselessfacts.jsph.pl/random.json?language=en') as response:
                data = await response.json()
        
        if 'text' not in data:
            embed=discord.Embed(
                description="Failed to retrieve a fact from the API.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return
        
        fact = data['text']
        await ctx.reply(f"Here's a random fact: {fact}")

    @commands.hybrid_command(name='quote', description='Fetches a random motivational quote.')
    async def quote(self, ctx: commands.Context):
        """Fetches and displays a random motivational quote from an external API."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en') as response:
                data = await response.json()
        
        if 'quoteText' not in data or 'quoteAuthor' not in data:
            embed=discord.Embed(
                description="Failed to retrieve a quote from the API.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return
        
        quote = data['quoteText']
        author = data['quoteAuthor']
        await ctx.reply(f'"{quote}" — {author}')

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
