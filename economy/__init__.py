import asqlite
import json

async def setup_database():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            # Channels table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
                                    guild_id INTEGER PRIMARY KEY,
                                    channel_id INTEGER NOT NULL)''')
            # POTD last post table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS potd_last_post (
                                    date TEXT PRIMARY KEY)''')
            # Users table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                    user_id INTEGER PRIMARY KEY,
                                    balance INTEGER NOT NULL DEFAULT 0,
                                    last_daily TEXT,
                                    job_points INTEGER NOT NULL DEFAULT 0)''')
            # Shop items table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS shop_items (
                                    item_id TEXT PRIMARY KEY,
                                    item_name TEXT NOT NULL,
                                    item_price INTEGER NOT NULL)''')
            # User inventory table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS user_inventory (
                                    user_id INTEGER NOT NULL,
                                    item_id TEXT NOT NULL,
                                    quantity INTEGER NOT NULL,
                                    PRIMARY KEY (user_id, item_id),
                                    FOREIGN KEY (item_id) REFERENCES shop_items(item_id))''')
            # Jobs table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
                                    job_id TEXT PRIMARY KEY,
                                    job_name TEXT NOT NULL,
                                    job_description TEXT,
                                    job_pay INTEGER NOT NULL,
                                    acceptance_chance REAL NOT NULL)''')
            # User jobs table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS user_jobs (
                                    user_id INTEGER PRIMARY KEY,
                                    job_id TEXT NOT NULL,
                                    start_time TEXT NOT NULL,
                                    last_work_time TEXT,
                                    FOREIGN KEY (job_id) REFERENCES jobs(job_id))''')
            # Job applications table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS job_applications (
                                    user_id INTEGER NOT NULL,
                                    job_id TEXT NOT NULL,
                                    application_time TEXT NOT NULL,
                                    PRIMARY KEY (user_id, job_id),
                                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                                    FOREIGN KEY (job_id) REFERENCES jobs(job_id))''')
            # Trades table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
                                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user1_id INTEGER,
                                    user2_id INTEGER,
                                    user1_items TEXT,
                                    user2_items TEXT,
                                    user1_credits INTEGER,
                                    user2_credits INTEGER,
                                    status TEXT DEFAULT 'pending')''')
            # Stocks table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                                    stock_id TEXT PRIMARY KEY,
                                    name TEXT NOT NULL,
                                    price REAL NOT NULL)''')
            # User portfolio table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stocks (
                    user_id INTEGER NOT NULL,
                    stock_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    PRIMARY KEY (user_id, stock_id),
                    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
                )
            ''')
            
            # Historical stock prices table
            await cursor.execute('''CREATE TABLE IF NOT EXISTS stock_price_history (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    stock_id TEXT NOT NULL,
                                    price REAL NOT NULL,
                                    timestamp TEXT NOT NULL,
                                    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id))''')

        await conn.commit()


async def initialize_stocks():
    json_file_path = 'economy/stocks.json'

    try:
        with open(json_file_path, 'r') as file:
            stock_data = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {json_file_path} was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file {json_file_path} is not a valid JSON file.")
        return

    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            for stock in stock_data:
                try:
                    await cursor.execute(
                        'INSERT OR IGNORE INTO stocks (stock_id, name, price) VALUES (?, ?, ?)',
                        (stock['stock_id'], stock['name'], stock['price'])
                    )
                except Exception as e:
                    print(f"Error inserting stock {stock['stock_id']}: {e}")
        await conn.commit()
