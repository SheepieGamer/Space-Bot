import asqlite
from datetime import datetime, timedelta
from typing import Tuple

async def claim_daily(user_id: int) -> int:
    reward = 1000
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?', (reward, datetime.utcnow().isoformat(), user_id))
            await conn.commit()
    return reward

async def can_claim_daily(user_id: int) -> Tuple[bool, str]:
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT last_daily FROM users WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()
            if result and result[0]:
                last_daily = datetime.fromisoformat(result[0])
                next_daily = last_daily + timedelta(days=1)
                now = datetime.utcnow()
                if now >= next_daily:
                    return True, ""
                else:
                    time_left = next_daily - now
                    return False, str(time_left)
            else:
                return True, ""