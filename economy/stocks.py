import asqlite
import asyncio
import matplotlib.pyplot as plt
import datetime
import io
import discord
import random


def generate_stock_graph(history, stock_id):
    timestamps = [datetime.datetime.fromisoformat(row[1]) for row in history]
    prices = [row[0] for row in history]
    
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, prices, marker='o', linestyle='-', color='b')
    plt.xlabel('Timestamp')
    plt.ylabel('Price (Space Credits)')
    plt.title(f'Stock Price History for {stock_id}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    
    return buffer

async def fetch_stock_history(stock_id):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT price, timestamp FROM stock_price_history WHERE stock_id = ? ORDER BY timestamp DESC', (stock_id,))
            history = await cursor.fetchall()
    return history

async def update_stock_price(stock_id: str, amount: float):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT price FROM stocks WHERE stock_id = ?', (stock_id,))
            current_price = await cursor.fetchone()
            
            if current_price:
                new_price = max(0, current_price[0] + amount)
                await cursor.execute('UPDATE stocks SET price = ? WHERE stock_id = ?', (new_price, stock_id))
                
                await log_stock_price(stock_id, new_price)
        await conn.commit()

async def clean_stock_price_history():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT COUNT(*) FROM stock_price_history')
            count = await cursor.fetchone()
            
            if count[0] > 2000:
                await cursor.execute('''
                    DELETE FROM stock_price_history
                    WHERE timestamp IN (
                        SELECT timestamp
                        FROM stock_price_history
                        ORDER BY timestamp ASC
                        LIMIT 1000
                    )
                ''')
        await conn.commit()

async def random_price_fluctuation():
    while True:
        await clean_stock_price_history()
        async with asqlite.connect('space.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT stock_id FROM stocks')
                stock_ids = [row[0] for row in await cursor.fetchall()]
                
                for stock_id in stock_ids:
                    fluctuation = random.uniform(-5.0, 5.0)
                    await update_stock_price(stock_id, fluctuation)
                    
        await asyncio.sleep(30)




async def check_user_balance(user_id: int, amount: int) -> bool:
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            balance = await cursor.fetchone()
            return balance[0] >= amount if balance else False

async def update_user_balance(user_id: int, amount: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        await conn.commit()

async def update_user_portfolio(user_id: int, stock_id: str, quantity: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            if quantity > 0:
                await cursor.execute('INSERT INTO user_stocks (user_id, stock_id, quantity) VALUES (?, ?, ?) ON CONFLICT(user_id, stock_id) DO UPDATE SET quantity = quantity + ?', (user_id, stock_id, quantity, quantity))
            else:
                await cursor.execute('UPDATE user_stocks SET quantity = quantity + ? WHERE user_id = ? AND stock_id = ?', (quantity, user_id, stock_id))
            if quantity == 0:
                await cursor.execute('DELETE FROM user_stocks WHERE user_id = ? AND stock_id = ?', (user_id, stock_id))
        await conn.commit()

async def get_user_stock_quantity(user_id: int, stock_id: str) -> int:
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT quantity FROM user_stocks WHERE user_id = ? AND stock_id = ?', (user_id, stock_id))
            result = await cursor.fetchone()
            return result[0] if result else 0

async def log_stock_price(stock_id: str, price: float):
    timestamp = datetime.datetime.utcnow().isoformat()
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO stock_price_history (stock_id, price, timestamp) VALUES (?, ?, ?)',
                (stock_id, price, timestamp)
            )
        await conn.commit()
