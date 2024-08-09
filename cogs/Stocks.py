import discord
import math
import asyncio
from discord.ext import commands
from economy.stocks import *

class Stocks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.price_adjustment = 0.025  # Price adjustment per share bought or sold

    @commands.command(name='buy_stock')
    async def buy_stock(self, ctx, stock_id: str, quantity: int):
        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT price FROM stocks WHERE stock_id = ?', (stock_id,))
                stock = await cursor.fetchone()

                if stock:
                    price = stock[0]
                    total_cost = price * quantity

                    if await check_user_balance(ctx.author.id, total_cost):
                        await update_user_balance(ctx.author.id, -total_cost)
                        await update_user_portfolio(ctx.author.id, stock_id, quantity)
                        
                        new_price = price * (1 + self.price_adjustment * quantity)
                        await update_stock_price(stock_id, new_price - price)

                        embed = discord.Embed(
                            title=f'Stock Purchase: {stock_id}',
                            description=f'Bought {quantity} {"shares" if quantity > 1 else "share"} of {stock_id} for **{price:.2f} space tokens**. New price: **{new_price:.2f} space tokens**',
                            color=discord.Color.green()
                        )
                        await ctx.reply(embed=embed)
                    else:
                        embed = discord.Embed(
                            title='Insufficient Funds',
                            description='You do not have enough space credits to purchase this stock.',
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed)
                else:
                    embed = discord.Embed(
                        title='Stock Not Found',
                        description='The specified stock does not exist.',
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed)

    @commands.command(name='sell_stock')
    async def sell_stock(self, ctx, stock_id: str, quantity: int):
        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                # Get stock details using stock_id
                await cursor.execute('SELECT price FROM stocks WHERE stock_id = ?', (stock_id,))
                stock = await cursor.fetchone()

                if stock:
                    price = stock[0]

                    user_quantity = await get_user_stock_quantity(ctx.author.id, stock_id)
                    if user_quantity >= quantity:
                        total_gain = price * quantity
                        await update_user_balance(ctx.author.id, total_gain)

                        # Update user portfolio
                        if user_quantity == quantity:
                            # Remove the stock from the portfolio if quantity is zero
                            await cursor.execute('DELETE FROM user_stocks WHERE user_id = ? AND stock_id = ?', (ctx.author.id, stock_id))
                        else:
                            # Reduce the quantity
                            await cursor.execute('UPDATE user_stocks SET quantity = quantity - ? WHERE user_id = ? AND stock_id = ?', (quantity, ctx.author.id, stock_id))

                        # Adjust the stock price downwards
                        new_price = price * (1 - self.price_adjustment * quantity)
                        await update_stock_price(stock_id, new_price - price)

                        await conn.commit()

                        embed = discord.Embed(
                            title=f'Stock Selling: {stock_id}',
                            description=f'Sold {quantity} {"shares" if quantity > 1 else "share"} of {stock_id} for **{total_gain:.2f} space tokens**. New price: **{new_price:.2f} space tokens**',
                            color=discord.Color.green()
                        )
                        await ctx.reply(embed=embed)
                    else:
                        embed = discord.Embed(
                            title='Insufficient Shares',
                            description='You do not own enough shares of this stock to sell.',
                            color=discord.Color.red()
                        )
                        await ctx.reply(embed=embed)
                else:
                    embed = discord.Embed(
                        title='Stock Not Found',
                        description='The specified stock does not exist.',
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed)

    @commands.command(name='stock_history')
    async def stock_history(self, ctx, stock_id: str):
        # Fetch stock history data
        msg: discord.Message = await ctx.reply("Working on it...")
        history = await fetch_stock_history(stock_id)
        
        if history:
            # Generate graph
            buffer = await asyncio.to_thread(generate_stock_graph, history, stock_id)
            
            file = discord.File(buffer, filename=f'stock_history_{stock_id}.png')
            embed = discord.Embed(title=f'Stock Price History for {stock_id}', color=discord.Color.blue())
            embed.set_image(url=f'attachment://stock_history_{stock_id}.png')
            await msg.edit(content=None, embed=embed, attachments=[file])
        else:
            embed = discord.Embed(
                title='No Stock History Found',
                description='No historical data found for this stock.',
                color=discord.Color.red()
            )
            await msg.edit(content=None, embed=embed)

    @commands.command(name='market_overview')
    async def market_overview(self, ctx, page: int = 1, sort: str = 'lowest'):
        """Show the stock market overview with pagination and sorting by highest or lowest price."""
        valid_sorts = ['highest', 'lowest']
        if sort not in valid_sorts:
            embed = discord.Embed(
                title='Invalid Sort Option',
                description=f"Invalid sort option. Use one of the following: {', '.join(valid_sorts)}.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        sort_order = 'DESC' if sort == 'highest' else 'ASC'

        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'SELECT stock_id, name, price FROM stocks ORDER BY price {sort_order}')
                stocks = await cursor.fetchall()

                if not stocks:
                    embed = discord.Embed(
                        description='No stocks found in the market.',
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed)
                    return

                items_per_page = 5
                total_pages = math.ceil(len(stocks) / items_per_page)
                page = max(1, min(page, total_pages))

                start = (page - 1) * items_per_page
                end = start + items_per_page
                stocks_on_page = stocks[start:end]

                embed = discord.Embed(
                    title="Market Overview",
                    description=f"Stocks sorted by {sort} price (Page {page}/{total_pages}):",
                    color=discord.Color.blue()
                )

                for stock in stocks_on_page:
                    stock_id, name, price = stock
                    embed.add_field(name=f"{name} (ID: {stock_id})", value=f'Price: {price:.2f} space credits', inline=False)

                message = await ctx.reply(embed=embed)

                if total_pages > 1:
                    await message.add_reaction('◀️')
                    await message.add_reaction('▶️')

                await message.add_reaction('⬆️')  # Add sort by highest price button
                await message.add_reaction('⬇️')  # Add sort by lowest price button

                def check(reaction, user):
                    return user != self.bot.user and reaction.message.id == message.id and str(reaction.emoji) in ['◀️', '▶️', '⬆️', '⬇️']

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
                    elif str(reaction.emoji) == '⬆️':
                        sort_order = 'DESC'
                        sort = 'highest'
                        await message.clear_reactions()  # Clear previous reactions
                    elif str(reaction.emoji) == '⬇️':
                        sort_order = 'ASC'
                        sort = 'lowest'
                        await message.clear_reactions()  # Clear previous reactions

                    # Update the stocks and the embed based on the new sort
                    async with asqlite.connect('space.db') as conn:
                        async with conn.cursor() as cursor:
                            await cursor.execute(f'SELECT stock_id, name, price FROM stocks ORDER BY price {sort_order}')
                            stocks = await cursor.fetchall()

                    items_per_page = 5
                    total_pages = math.ceil(len(stocks) / items_per_page)
                    page = max(1, min(page, total_pages))

                    start = (page - 1) * items_per_page
                    end = start + items_per_page
                    stocks_on_page = stocks[start:end]

                    embed = discord.Embed(
                        title="Market Overview",
                        description=f"Stocks sorted by {sort} price (Page {page}/{total_pages}):",
                        color=discord.Color.blue()
                    )

                    for stock in stocks_on_page:
                        stock_id, name, price = stock
                        embed.add_field(name=f"{name} (ID: {stock_id})", value=f'Price: {price:.2f} space credits', inline=False)

                    await message.edit(embed=embed)
                    await message.add_reaction('◀️')
                    await message.add_reaction('▶️')
                    await message.add_reaction('⬆️')  # Add sorting reaction again
                    await message.add_reaction('⬇️')  # Add sorting reaction again
                    await message.remove_reaction(reaction.emoji, user)

    @commands.command(name='market_trends')
    async def market_trends(self, ctx):
        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                # Example to show stock price changes in the last 24 hours
                twenty_four_hours_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat()
                await cursor.execute('''
                    SELECT s.name, h.price AS current_price, h2.price AS previous_price
                    FROM stocks s
                    JOIN stock_price_history h ON s.stock_id = h.stock_id
                    JOIN stock_price_history h2 ON s.stock_id = h2.stock_id
                    WHERE h.timestamp = (SELECT MAX(timestamp) FROM stock_price_history WHERE stock_id = s.stock_id)
                    AND h2.timestamp = (SELECT MAX(timestamp) FROM stock_price_history WHERE timestamp < ? AND stock_id = s.stock_id)
                ''', (twenty_four_hours_ago,))
                trends = await cursor.fetchall()
                
                if trends:
                    trends_str = '\n'.join([f'{trend[0]}: {trend[1] - trend[2]:.2f} change' for trend in trends])
                    embed = discord.Embed(
                        title='Market Trends',
                        description=f'Stock price changes in the last 24 hours:\n{trends_str}',
                        color=discord.Color.blue()
                    )
                    await ctx.reply(embed=embed)
                else:
                    embed = discord.Embed(
                        description='No trend data available.',
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed)

    @commands.command(name='portfolio')
    async def portfolio(self, ctx: commands.Context):
        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                # Get the user's stock holdings
                await cursor.execute('SELECT us.stock_id, s.name, us.quantity, s.price FROM user_stocks us JOIN stocks s ON us.stock_id = s.stock_id WHERE us.user_id = ?', (ctx.author.id,))
                portfolio = await cursor.fetchall()
                
                if portfolio:
                    portfolio_str = '\n'.join([f'`{item[1]} (ID: {item[0]})`: {item[2]} {"shares" if item[2] > 1 else "share"} at **{item[3]:.2f} space credits** each' for item in portfolio])
                    embed = discord.Embed(
                        title=f'{ctx.author.display_name}\'s Portfolio',
                        description=portfolio_str,
                        color=discord.Color.blue()
                    )
                    await ctx.reply(embed=embed)
                else:
                    embed = discord.Embed(
                        description='Your portfolio is empty.',
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))
