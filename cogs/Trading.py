from discord.ext import commands
import discord
import settings
from economy import *
from economy.inventory import *
from economy.job import *
from economy.other import *
from economy.pay import *
from economy.store import *
from utils import *


class Trading(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="trade")
    async def trade(self, ctx, member: discord.Member, offer: str, credits_or_items_offer: str, request: str, credits_or_items_request: str):
        user1_id = ctx.author.id
        user2_id = member.id

        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                # Validate the offer
                if credits_or_items_offer.lower() == 'items' or credits_or_items_offer.lower() == 'item':
                    # Check if the user has the offered item
                    await cursor.execute(
                        "SELECT quantity FROM user_inventory WHERE user_id = ? AND item_id = ?",
                        (user1_id, offer)
                    )
                    offer_quantity = await cursor.fetchone()

                    if not offer_quantity or offer_quantity[0] < 1:
                        await ctx.reply(f"You don't have enough of the item: {offer}.")
                        return

                    offer_item = offer
                    offer_credits = None
                elif credits_or_items_offer.lower() == 'credits' or credits_or_items_request.lower() == 'credit':
                    try:
                        offer_item = None
                        offer_credits = int(offer)
                        if offer_credits <= 0:
                            await ctx.reply("Coin amounts must be greater than zero.")
                            return
                    except ValueError:
                        await ctx.reply("Please provide a valid coin amount.")
                        return
                else:
                    await ctx.reply("Invalid type for the offer. Please specify 'items' or 'credits'.")
                    return

                # Validate the request
                if credits_or_items_request.lower() == 'items' or credits_or_items_offer.lower() == 'item':
                    # Check if the target user has the requested item
                    await cursor.execute(
                        "SELECT quantity FROM user_inventory WHERE user_id = ? AND item_id = ?",
                        (user2_id, request)
                    )
                    request_quantity = await cursor.fetchone()

                    if not request_quantity or request_quantity[0] < 1:
                        await ctx.reply(f"{member.mention} doesn't have the item: {request}.")
                        return

                    request_item = request
                    request_credits = None
                elif credits_or_items_request.lower() == 'credits' or credits_or_items_request.lower() == 'credit':
                    try:
                        request_item = None
                        request_credits = int(request)
                        if request_credits <= 0:
                            await ctx.reply("Coin amounts must be greater than zero.")
                            return
                    except ValueError:
                        await ctx.reply("Please provide a valid coin amount.")
                        return
                else:
                    await ctx.reply("Invalid type for the request. Please specify 'items' or 'credits'.")
                    return

                # Store the trade in the database
                await cursor.execute(
                    "INSERT INTO trades (user1_id, user2_id, user1_items, user2_items, user1_credits, user2_credits, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user1_id, user2_id, offer_item, request_item, offer_credits, request_credits, 'pending')
                )
                # Fetch the last inserted row ID
                await cursor.execute("SELECT rowid FROM trades ORDER BY rowid DESC LIMIT 1")
                result = await cursor.fetchone()
                trade_id = result[0] if result else None

                if trade_id is not None:
                    embed = discord.Embed(
                        title="Trade Request Sent",
                        description=f"You have offered **{offer}** (type: {credits_or_items_offer}) and requested **{request}** (type: {credits_or_items_request}) in return.\n\n"
                                    f"{member.mention}, use `s!accept_trade {trade_id}` to accept the trade or `s!reject_trade {trade_id}` to reject it.",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="Error",
                        description="There was an issue creating the trade. Please try again.",
                        color=discord.Color.red()
                    )

        await ctx.reply(embed=embed)




    @commands.command(name="accept_trade")
    async def accept_trade(self, ctx, trade_id: int):
        user2_id = ctx.author.id

        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                # Retrieve trade details
                await cursor.execute("SELECT user1_id, user1_items, user1_credits, user2_items, user2_credits, status FROM trades WHERE rowid = ?", (trade_id,))
                trade = await cursor.fetchone()

                if not trade:
                    await ctx.reply("Trade not found.")
                    return

                user1_id, user1_items, user1_credits, user2_items, user2_credits, status = trade

                if status != 'pending':
                    await ctx.reply("This trade is not pending or has already been accepted/rejected.")
                    return

                # Ensure the user2_id is the one this trade was intended for
                if user2_id != ctx.author.id:
                    await ctx.reply("This trade was not intended for you.")
                    return

                # Handle credit transfer
                if user1_credits is not None:
                    if user1_credits > 0:
                        # Transfer credits from user1 to user2
                        await cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (user1_credits, user1_id))
                        await cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (user1_credits, user2_id))

                if user2_credits is not None:
                    if user2_credits > 0:
                        # Transfer credits from user2 to user1
                        await cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (user2_credits, user2_id))
                        await cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (user2_credits, user1_id))

                # Handle item transfer
                if user1_items:
                    item_list = user1_items.split(',')
                    for item in item_list:
                        # Check if the sender has the item in their inventory
                        await cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? AND item_id = ?", (user1_id, item))
                        result = await cursor.fetchone()

                        if not result or result[0] < 1:
                            await ctx.reply(f"User does not have enough of item: {item}")
                            return

                        # Remove item from sender's inventory
                        await cursor.execute("UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_id = ?", (user1_id, item))
                        await cursor.execute("DELETE FROM user_inventory WHERE user_id = ? AND item_id = ? AND quantity <= 0", (user1_id, item))

                        # Add item to recipient's inventory
                        await cursor.execute("INSERT INTO user_inventory (user_id, item_id, quantity) VALUES (?, ?, 1) "
                                            "ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + 1",
                                            (user2_id, item))

                if user2_items:
                    item_list = user2_items.split(',')
                    for item in item_list:
                        # Check if the recipient has the item in their inventory
                        await cursor.execute("SELECT quantity FROM user_inventory WHERE user_id = ? AND item_id = ?", (user2_id, item))
                        result = await cursor.fetchone()

                        if not result or result[0] < 1:
                            await ctx.reply(f"Recipient does not have enough of item: {item}")
                            return

                        # Remove item from recipient's inventory
                        await cursor.execute("UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_id = ?", (user2_id, item))
                        await cursor.execute("DELETE FROM user_inventory WHERE user_id = ? AND item_id = ? AND quantity <= 0", (user2_id, item))

                        # Add item to sender's inventory
                        await cursor.execute("INSERT INTO user_inventory (user_id, item_id, quantity) VALUES (?, ?, 1) "
                                            "ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + 1",
                                            (user1_id, item))

                # Update the trade status
                await cursor.execute("UPDATE trades SET status = 'accepted' WHERE rowid = ?", (trade_id,))

            await conn.commit()

        embed = discord.Embed(
            title="Trade Accepted",
            description="The trade has been accepted and completed.",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)




    @commands.command(name="reject_trade")
    async def reject_trade(self, ctx, trade_id: int):
        user2_id = ctx.author.id

        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT * FROM trades WHERE trade_id = ? AND user2_id = ? AND status = 'pending'", (trade_id, user2_id))
                trade = await cursor.fetchone()

                if not trade:
                    await ctx.reply("Trade not found or you're not part of this trade.")
                    return

                await cursor.execute("UPDATE trades SET status = 'rejected' WHERE trade_id = ?", (trade_id,))

        embed = discord.Embed(
            title="Trade Rejected",
            description="The trade has been rejected.",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="cancel_trade")
    async def cancel_trade(self, ctx, trade_id: int):
        user_id = ctx.author.id

        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT * FROM trades WHERE trade_id = ? AND (user1_id = ? OR user2_id = ?) AND status = 'pending'", (trade_id, user_id, user_id))
                trade = await cursor.fetchone()

                if not trade:
                    await ctx.reply("Trade not found or you're not part of this trade.")
                    return

                await cursor.execute("UPDATE trades SET status = 'cancelled' WHERE trade_id = ?", (trade_id,))

        embed = discord.Embed(
            title="Trade Cancelled",
            description="The trade has been cancelled.",
            color=discord.Color.orange()
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Trading(bot))