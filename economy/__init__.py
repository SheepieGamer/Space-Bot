import asqlite

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
                                    last_daily TEXT)''')
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
            # Check if the column 'last_work_time' exists, and if not, add it
            await cursor.execute('PRAGMA table_info(user_jobs)')
            columns = [row[1] for row in await cursor.fetchall()]
            if 'last_work_time' not in columns:
                await cursor.execute('ALTER TABLE user_jobs ADD COLUMN last_work_time TEXT')

            # Add job_points column to users table if it doesn't exist
            await cursor.execute('PRAGMA table_info(users)')
            columns = [row[1] for row in await cursor.fetchall()]
            if 'job_points' not in columns:
                await cursor.execute('ALTER TABLE users ADD COLUMN job_points INTEGER NOT NULL DEFAULT 0')

        await conn.commit()