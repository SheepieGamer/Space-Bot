import asqlite 

async def remove_balance(user_id: int, amount: int) -> None:
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
            await cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?', (amount, user_id, amount))
            await conn.commit()

async def add_balance(user_id: int, amount: int) -> None:
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
            await cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            await conn.commit()

async def transfer_credits(sender_id: int, receiver_id: int, amount: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, sender_id))
            await cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?', (receiver_id, amount, amount))
            await conn.commit()

async def get_balance(user_id: int) -> int:
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()
            if result:
                return result[0]
            else:
                await cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, 0)', (user_id,))
                await conn.commit()
                return 0