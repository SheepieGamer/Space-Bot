import asqlite

async def buy_item(user_id: int, item_id: str):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT item_price FROM shop_items WHERE item_id = ?', (item_id,))
            item_price = await cursor.fetchone()
            if not item_price:
                return False, "Item not found."
            item_price = item_price[0]

            await cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            balance = await cursor.fetchone()
            if not balance or balance[0] < item_price:
                return False, "Insufficient balance."

            await cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (item_price, user_id))
            await add_to_inventory(user_id, item_id, 1)
        await conn.commit()
    return True, "Purchase successful."

async def add_to_inventory(user_id: int, item_id: str, quantity: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''INSERT INTO user_inventory (user_id, item_id, quantity)
                                   VALUES (?, ?, ?)
                                   ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + ?''',
                                 (user_id, item_id, quantity, quantity))
        await conn.commit()


async def add_shop_item(item_id: str, item_name: str, item_price: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('INSERT INTO shop_items (item_id, item_name, item_price) VALUES (?, ?, ?)',
                                 (item_id, item_name, item_price))
        await conn.commit()

async def get_shop_items():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT item_id, item_name, item_price FROM shop_items')
            items = await cursor.fetchall()
    return items
