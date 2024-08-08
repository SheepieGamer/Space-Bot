import asqlite

async def get_inventory(user_id: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''SELECT shop_items.item_name, shop_items.item_id, user_inventory.quantity
                                   FROM user_inventory
                                   JOIN shop_items ON user_inventory.item_id = shop_items.item_id
                                   WHERE user_inventory.user_id = ?''', (user_id,))
            inventory = await cursor.fetchall()
    return inventory





async def remove_item(user_id: int, item_id: str, quantity: int) -> None:
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT quantity FROM user_inventory WHERE user_id = ? AND item_id = ?', (user_id, item_id))
            result = await cursor.fetchone()
            if result and result[0] >= quantity:
                await cursor.execute('UPDATE user_inventory SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?', (quantity, user_id, item_id))
                if result[0] - quantity == 0:
                    await cursor.execute('DELETE FROM user_inventory WHERE user_id = ? AND item_id = ?', (user_id, item_id))
                await conn.commit()