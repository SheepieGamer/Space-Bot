import discord
from discord.ext import commands
import math
import asyncio
from utils import *

class Economy(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='balance', description='Check your balance.', aliases=["bal"])
    async def balance(self, ctx: commands.Context, user: discord.Member = commands.Author):
        """Check the user's balance."""
        user_id = user.id
        balance = await get_balance(user_id)
        embed = discord.Embed(
            title=f"{user.display_name}'s Balance",
            description=f"{user.mention} has **{balance}** space credits.",
            color=discord.Color.blue()
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='daily', description='Claim your daily reward.')
    async def daily(self, ctx: commands.Context):
        """Claim the daily reward."""
        user_id = ctx.author.id
        
        can_claim, time_left = await can_claim_daily(user_id)
        if can_claim:
            reward = await claim_daily(user_id)
            embed = discord.Embed(
                title="Successfully claimed daily reward!",
                description=f"{ctx.author.mention}, you have earned **{reward}** space credits for claiming your daily reward!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                description=f"{ctx.author.mention}, you've already claimed your daily reward for today. Try again in {time_left.split('.')[0]}",
                color=discord.Color.red()
            )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='pay', description='Pay space credits to another user.')
    async def transfer(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Pay space credits to another user."""
        if amount <= 0:
            embed = discord.Embed(
                description="You can't pay a negative or zero amount.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        sender_id = ctx.author.id
        receiver_id = member.id
        sender_balance = await get_balance(sender_id)

        if sender_balance < amount:
            embed = discord.Embed(
                description="You don't have enough space credits to complete this transaction.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        await transfer_credits(sender_id, receiver_id, amount)
        embed = discord.Embed(
            title="Payment Successful",
            description=f"{ctx.author.mention} has paid {member.mention} {amount} space credits.",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='shop', description='Show available items in the shop.')
    async def shop(self, ctx: commands.Context, page: int = 1):
        """Show available items in the shop."""
        items = await get_shop_items()
        if not items:
            await ctx.reply("The shop is currently empty.")
            return
        
        items_per_page = 5
        total_pages = math.ceil(len(items) / items_per_page)
        page = max(1, min(page, total_pages))

        start = (page - 1) * items_per_page
        end = start + items_per_page
        items_on_page = items[start:end]

        embed = discord.Embed(
            title="Shop",
            description=f"Available items for purchase (Page {page}/{total_pages}):",
            color=discord.Color.gold()
        )
        for item_id, item_name, item_price in items_on_page:
            embed.add_field(
                name=f"{item_name}", 
                value=f"Price: **{item_price} space credits**\n Item ID: *{item_id}* (used for buying)", 
                inline=False
            )

        message = await ctx.reply(embed=embed)
        
        if total_pages > 1:
            await message.add_reaction('◀️')
            await message.add_reaction('▶️')

        def check(reaction, user):
            return user != self.bot.user and reaction.message.id == message.id and str(reaction.emoji) in ['◀️', '▶️']

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

            if str(reaction.emoji) == '◀️':
                page -= 1
                if page < 1:
                    page = total_pages
            elif str(reaction.emoji) == '▶️':
                page += 1
                if page > total_pages:
                    page = 1

            start = (page - 1) * items_per_page
            end = start + items_per_page
            items_on_page = items[start:end]
            
            embed = discord.Embed(
                title="Shop",
                description=f"Available items for purchase (Page {page}/{total_pages}):",
                color=discord.Color.gold()
            )
            for item_id, item_name, item_price in items_on_page:
                embed.add_field(
                    name=f"{item_name}", 
                    value=f"Price: **{item_price} space credits**\n Item ID: *{item_id}* (used for buying)", 
                    inline=False
                )

            await message.edit(embed=embed)
            await message.remove_reaction(reaction.emoji, user)

    @commands.hybrid_command(name='buy', description='Buy an item from the shop.')
    async def buy(self, ctx: commands.Context, item_id: str):
        """Buy an item from the shop."""
        user_id = ctx.author.id
        success, message = await buy_item(user_id, item_id)
        
        embed = discord.Embed(
            description=message,
            color=discord.Color.green() if success else discord.Color.red()
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='inventory', description='Show your inventory.')
    async def inventory(self, ctx: commands.Context, page: int = 1):
        """Show your inventory."""
        user_id = ctx.author.id
        inventory = await get_inventory(user_id)
        if not inventory:
            await ctx.reply("Your inventory is empty.")
            return

        items_per_page = 5
        total_pages = math.ceil(len(inventory) / items_per_page)
        page = max(1, min(page, total_pages))

        start = (page - 1) * items_per_page
        end = start + items_per_page
        items_on_page = inventory[start:end]

        embed = discord.Embed(
            title="Your Inventory",
            description=f"Items you own (Page {page}/{total_pages}):",
            color=discord.Color.blue()
        )
        for item_name, item_id, quantity in items_on_page:
            async with asqlite.connect('space.db') as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute('SELECT item_price FROM shop_items WHERE item_id = ?', (item_id,))
                    price = await cursor.fetchone()
                    sell_price = int(price[0] * 0.75) if price else 0

            embed.add_field(
                name=item_name,
                value=f"Quantity: **{quantity}**\nSell price: **{sell_price} space tokens\n**Item ID: *{item_id}* (used for selling)",
                inline=False
            )

        message = await ctx.reply(embed=embed)
        
        if total_pages > 1:
            await message.add_reaction('◀️')
            await message.add_reaction('▶️')

        def check(reaction, user):
            return user != self.bot.user and reaction.message.id == message.id and str(reaction.emoji) in ['◀️', '▶️']

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

            if str(reaction.emoji) == '◀️':
                page -= 1
                if page < 1:
                    page = total_pages
            elif str(reaction.emoji) == '▶️':
                page += 1
                if page > total_pages:
                    page = 1

            start = (page - 1) * items_per_page
            end = start + items_per_page
            items_on_page = inventory[start:end]

            embed = discord.Embed(
                title="Your Inventory",
                description=f"Items you own (Page {page}/{total_pages}):",
                color=discord.Color.blue()
            )
            for item_name, item_id, quantity in items_on_page:
                async with asqlite.connect('space.db') as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute('SELECT item_price FROM shop_items WHERE item_id = ?', (item_id,))
                        price = await cursor.fetchone()
                        sell_price = int(price[0] * 0.75) if price else 0

                embed.add_field(
                    name=item_name,
                    value=f"Quantity: **{quantity}**\nItem ID: *{item_id}* (used for selling)\nSell price: **{sell_price} space tokens**",
                    inline=False
                )

            await message.edit(embed=embed)
            await message.remove_reaction(reaction.emoji, user)


    @commands.hybrid_command(name='sell', description='Sell an item from your inventory.')
    async def sell(self, ctx: commands.Context, *, item_id: str):
        """Sell an item from your inventory."""
        user_id = ctx.author.id

        inventory = await get_inventory(user_id)
        item_found = False
        item_price = 0


        for item_name, id, qty in inventory:
            if id.lower() == item_id.lower():
                if qty < 1:
                    await ctx.reply("You do not have enough of that item to sell.")
                    return
                item_found = True
                async with asqlite.connect('space.db') as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute('SELECT item_price FROM shop_items WHERE item_id = ?', (item_id,))
                        price = await cursor.fetchone()
                        if price:
                            item_price = price[0]
                        else:
                            await ctx.reply("Item price not found.")
                            return
                break

        if not item_found:
            await ctx.reply("Item not found in your inventory.")
            return

        sell_price = int(item_price * 0.75)
        total_price = sell_price

        await remove_item(user_id, item_id, 1)
        await add_balance(user_id, total_price)

        embed = discord.Embed(
            title="Item Sold!",
            description=f"You have sold **1** of **{item_id}** for **{total_price}** space credits.",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
