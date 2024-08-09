import discord
from discord.ext import commands
import math
import random
import asyncio
from economy import *
from economy.inventory import *
from economy.job import *
from economy.other import *
from economy.pay import *
from economy.store import *
from utils import *

class Economy(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='balance', description='Check your balance.', aliases=["bal"])
    @commands.cooldown(1,3,  commands.BucketType.user)
    async def balance(self, ctx: commands.Context, user: discord.Member = commands.Author):
        """Check the user's balance."""
        user_id = user.id
        balance = await get_balance(user_id)
        embed = discord.Embed(
            title=f"{user.display_name}'s Balance",
            description=f"{user.mention} has **{balance:.2f} space credits**.",
            color=discord.Color.blue()
        )
        await ctx.reply(embed=embed)

    @balance.error
    async def balance_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='daily', description='Claim your daily reward.')
    @commands.cooldown(1,3, commands.BucketType.user)
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
    
    @daily.error
    async def daily_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='pay', description='Pay space credits to another user.')
    @commands.cooldown(1,3, commands.BucketType.user)
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
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

    @pay.error
    async def pay_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='shop', description='Show available items in the shop.')
    @commands.cooldown(1,3, commands.BucketType.user)
    async def shop(self, ctx: commands.Context, page: int = 1):
        """Show available items in the shop."""
        items = await get_shop_items()
        if not items:
            embed=discord.Embed(
                description="The shop is currently empty.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
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

    @shop.error
    async def shop_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='buy', description='Buy an item from the shop.')
    @commands.cooldown(1,3, commands.BucketType.user)
    async def buy(self, ctx: commands.Context, item_id: str):
        """Buy an item from the shop."""
        user_id = ctx.author.id
        success, message = await buy_item(user_id, item_id)
        
        embed = discord.Embed(
            description=message,
            color=discord.Color.green() if success else discord.Color.red()
        )
        await ctx.reply(embed=embed)

    @buy.error
    async def buy_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='inventory', description='Show your inventory.', aliases=["inv"])
    @commands.cooldown(1,3, commands.BucketType.user)
    async def inventory(self, ctx: commands.Context, user: discord.Member = commands.Author, page: int = 1):
        """Show your inventory."""
        user_id = ctx.author.id
        inventory = await get_inventory(user_id)
        if not inventory:
            embed=discord.Embed(
                description="You don't have any items in your inventory.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
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

    @inventory.error
    async def inventory_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)


    @commands.hybrid_command(name='sell', description='Sell an item from your inventory.')
    @commands.cooldown(1,3, commands.BucketType.user)
    async def sell(self, ctx: commands.Context, *, item_id: str):
        """Sell an item from your inventory."""
        user_id = ctx.author.id

        inventory = await get_inventory(user_id)
        item_found = False
        item_price = 0


        for item_name, id, qty in inventory:
            if id.lower() == item_id.lower():
                if qty < 1:
                    embed=discord.Embed(
                        description=f"You don't have any **{item_name}** in your inventory.",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed)
                    return
                item_found = True
                async with asqlite.connect('space.db') as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute('SELECT item_price FROM shop_items WHERE item_id = ?', (item_id,))
                        price = await cursor.fetchone()
                        if price:
                            item_price = price[0]
                        else:
                            embed=discord.Embed(
                                description=f"Item price not found.",
                                color=discord.Color.red()
                            )
                            await ctx.reply(embed=embed)
                            return
                break

        if not item_found:
            embed=discord.Embed(
                description="Item not found in your inventory.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
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

    @sell.error
    async def sell_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='dig', description='Dig for space items.', cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def dig(self, ctx: commands.Context):
        """Dig for space items."""
        user_id = ctx.author.id

        # Fetch all shop items from the database
        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT item_id, item_name, item_price FROM shop_items')
                shop_items = await cursor.fetchall()

        if not shop_items:
            embed = discord.Embed(
                description="There are no items to dig up.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        if random.random() < 0.25:
            item = random.choice(shop_items)
            item_id, item_name, item_price = item

            await add_to_inventory(user_id, item_id, 1)

            credits_amount = random.randint(50,250)

            embed = discord.Embed(
                title="You found an item!",
                description=f"You dug up **{item_name}**! You also found **{credits_amount}** space credits!",
                color=discord.Color.green()
            )
        elif random.random() < 0.5:
            credits_amount = random.randint(50,150)
            embed = discord.Embed(
                title="You found space credits!",
                description=f"You dug and dug, and found **{credits_amount}** space credits!",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="You found nothing!",
                description=f"You dug around, but found nothing interesting.",
                color=discord.Color.red()
            )

        await ctx.reply(embed=embed)


    @dig.error
    async def dig_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can dig again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='rob', description='Attempt to rob another user.')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def rob(self, ctx: commands.Context, member: discord.Member):
        """Attempt to rob another user."""
        if member == ctx.author:
            embed=discord.Embed(
                description="You cannot rob yourself.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        user_id = ctx.author.id
        target_id = member.id

        target_balance = await get_balance(target_id)
        if target_balance < 100:
            embed = discord.Embed(
                description=f"{member.mention} doesn't have enough space credits to rob.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        success_chance = random.randint(1, 100)
        if success_chance <= 40:
            stolen_amount = random.randint(100, int(target_balance * 0.6))
            await transfer_credits(target_id, user_id, stolen_amount)
            embed = discord.Embed(
                title="Robbery Successful!",
                description=f"You successfully robbed {member.mention} and stole **{stolen_amount}** space credits!",
                color=discord.Color.green()
            )
        else:
            fine = random.randint(50, 200)
            await remove_balance(user_id, fine)
            embed = discord.Embed(
                description=f"Your robbery attempt failed, and you were fined **{fine}** space credits.",
                color=discord.Color.red()
            )
        await ctx.reply(embed=embed)

    @rob.error
    async def rob_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Be nice!",
                description=f"Hey! You can rob again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)


    @commands.command(name="job", aliases=["work"])
    @commands.cooldown(1,3, commands.BucketType.user)
    async def job(self, ctx: commands.Context, action: str = "work"):
        """Get a list of jobs (s!job list), or work your job (s!job work)"""
        user_id = ctx.author.id
        if action == "list":
            jobs = await get_jobs()
            embed = discord.Embed(
                title="Available Jobs",
                description="Here are the jobs you can apply for:",
                color=discord.Color.green()
            )
            for job_id, job_name, job_description, job_pay, acceptance_chance in jobs:
                embed.add_field(
                    name=f"{job_name} (ID: {job_id})",
                    value=f"**Description:** {job_description}\n**Pay:** {job_pay} credits/hour\n**Acceptance Chance:** {int(acceptance_chance * 100)}%",
                    inline=False
                )
            await ctx.reply(embed=embed)
            return
        elif action == "work":
            pass
        else:
            embed = discord.Embed(
                description="Invalid action. Use `s!job list` or `s!job work`.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        user_job = await get_user_job(user_id)
        if not user_job:
            embed = discord.Embed(
                description="You don't have a job yet! Use `s!apply` to apply for a job. Use `s!job list` for a list of available jobs.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        job_name, job_description, job_pay = user_job
        
        # Check cooldown
        last_work_time = await get_last_work_time(user_id)
        if last_work_time and datetime.utcnow() - last_work_time < timedelta(hours=1):
            remaining_time = timedelta(hours=1) - (datetime.utcnow() - last_work_time)
            embed = discord.Embed(
                description=f"You can't work right now. You need to wait **{str(remaining_time).split('.')[0]}** before you can work again.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        num1 = random.randint(1, 12)
        num2 = random.randint(1, 12)
        correct_answer = num1 * num2

        await ctx.reply(f"To earn your pay and job points, solve this problem: **{num1} x {num2} = ?**")

        def check(m: discord.Message):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            answer = await self.bot.wait_for('message', timeout=30.0, check=check)
            if int(answer.content) == correct_answer:
                await update_last_work_time(user_id)
                await add_balance(user_id, job_pay)
                job_points = await update_job_points(user_id)
                embed = discord.Embed(
                    description=f"Correct! You have earned {job_pay} credits and {job_points} job points for your work.",
                    color=discord.Color.green()
                )
                await ctx.reply(embed=embed)
            else:
                embed = discord.Embed(
                    description="Incorrect answer. You didn't earn anything this time.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                description="You took too long to respond. Try again later.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)

    @job.error
    async def job_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)


    @commands.command(name="apply")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def apply(self, ctx: commands.Context, job_id: str = "list_available_jobs_if_id_isnt_supplied"):
        """ Apply for a job."""
        user_id = ctx.author.id
        if job_id == "list_available_jobs_if_id_isnt_supplied":
            jobs = await get_jobs()
            embed = make_embed(
                title="Available Jobs",
                description="Here are the jobs you can apply for:",
                color=discord.Color.green()
            )
            for job_id, job_name, job_description, job_pay, acceptance_chance in jobs:
                embed.add_field(
                    name=f"{job_name} (ID: {job_id})",
                    value=f"**Description:** {job_description}\n**Pay:** {job_pay} credits/hour\n**Acceptance Chance:** {int(acceptance_chance * 100)}%",
                    inline=False
                )
            await ctx.reply(embed=embed)
            return

        success, message = await apply_for_job(user_id, job_id)
        if success:
            embed = make_embed(
                title="Job Application Success",
                description=message,
                color=discord.Color.green()
            )
        else:
            embed = make_embed(
                title="Job Application Failed",
                description=message,
                color=discord.Color.red()
            )

        await ctx.reply(embed=embed)

    @apply.error
    async def apply_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.command(name="resign", aliases=["quit"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def resign(self, ctx: commands.Context):
        """Quit your job."""
        user_id = ctx.author.id

        success, message = await resign_from_job(user_id)
        if success:
            embed = make_embed(
                title="Resignation Success",
                description=message,
                color=discord.Color.green()
            )
        else:
            embed = make_embed(
                title="Resignation Failed",
                description=message,
                color=discord.Color.red()
            )

        await ctx.reply(embed=embed)

    @resign.error
    async def resign_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)

    @commands.command(name="leaderboard")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def leaderboard(self, ctx: commands.Context, subject: str = "credits"):
        """Display the top users based on their balance or job."""
        if subject not in ["credits", "job_points"]:
            await ctx.reply("Invalid subject. Use 'credits' or 'job_points'.")
            return
        if subject == "balance":
            async with asqlite.connect('space.db') as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute('''
                        SELECT user_id, balance 
                        FROM users 
                        ORDER BY balance DESC 
                        LIMIT 10
                    ''')
                    top_users = await cursor.fetchall()

            if top_users:
                embed = discord.Embed(
                    title="Leaderboard",
                    description="Top users based on their balance.",
                    color=discord.Color.gold()
                )
                for idx, (user_id, balance) in enumerate(top_users, start=1):
                    user = self.bot.get_user(user_id)
                    username = user.name if user else "Unknown"
                    embed.add_field(
                        name=f"{idx}. {username}",
                        value=f"{balance} credits",
                        inline=False
                    )
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("No users found in the database.")
        else:
            async with asqlite.connect('space.db') as conn:
                async with conn.cursor() as cursor:
                    # Get the top 10 users by job points
                    await cursor.execute('''
                        SELECT user_id, job_points 
                        FROM users 
                        ORDER BY job_points DESC 
                        LIMIT 10
                    ''')
                    top_users = await cursor.fetchall()

            if top_users:
                embed = discord.Embed(
                    title="Job Performance Leaderboard",
                    description="Top users based on their job performance points.",
                    color=discord.Color.blue()
                )
                for idx, (user_id, job_points) in enumerate(top_users, start=1):
                    user = self.bot.get_user(user_id)
                    username = user.name if user else "Unknown"
                    embed.add_field(
                        name=f"{idx}. {username}",
                        value=f"{job_points} points",
                        inline=False
                        )
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("No job performance data found.")

    @leaderboard.error
    async def leaderboard_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}"
            )
            await ctx.reply(embed=embed)



async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
