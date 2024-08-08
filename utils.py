import asqlite
import aiohttp
import io
from typing import Tuple
from starplot import MapPlot, Projection, Star
from starplot.styles import PlotStyle, extensions
from discord.ext import commands
import pytz
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import discord
import settings
import matplotlib
matplotlib.use("agg")

async def potd(bot: commands.Bot):
    await bot.wait_until_ready()
    
    last_post_date = await get_last_post_date()
    today = datetime.utcnow().date().isoformat()

    if last_post_date == today:
        return "Already posted"

    channels = await get_channels()
    if not channels:
        return

    data = await retrieve("https://api.nasa.gov/planetary/apod")
    title = data["title"]
    explanation = data["explanation"]
    url = data["hdurl"]
    date = data["date"]

    embed = discord.Embed(
        title=title,
        description=explanation,
        url=url,
        color=discord.Color.dark_green()
    )
    embed.set_image(url=url)
    embed.set_footer(text=f"NASA Astronomy Picture of the Day - {date}")

    for channel_id in channels:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)

    await update_last_post_date(today)
    

def generate_star_chart(lat, lon, dt):
    p = MapPlot(
        projection=Projection.ZENITH,
        lat=lat,
        lon=lon,
        dt=dt,
        style=PlotStyle().extend(
            extensions.NORD,
        ),
        resolution=2600,
    )
    p.constellations()
    p.stars(mag=5.6, where_labels=[Star.magnitude < 2.1])
    p.dsos(mag=9, true_size=True, labels=None)
    p.constellation_borders()
    p.ecliptic()
    p.celestial_equator()
    p.milky_way()

    p.marker(
        ra=12.36,
        dec=25.85,
        label="Mel 111",
        style={
            "marker": {
                "size": 28,
                "symbol": "circle",
                "fill": "full",
                "color": "#ed7eed",
                "edge_color": "#e0c1e0",
                "alpha": 0.4,
                "zorder": 100,
            },
            "label": {
                "zorder": 200,
                "font_size": 12,
                "font_weight": "bold",
                "font_color": "ed7eed",
                "font_alpha": 0.8,
            },
        },
    )

    buffer = io.BytesIO()
    p.export(buffer, transparent=True, format="png")
    buffer.seek(0)
    return buffer

async def retrieve(url, params: dict={}, api_key_required: bool=True):
    if api_key_required:
        params["api_key"] = settings.NASA
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                raise ValueError(f"Error fetching data from API: {response.status}")

async def setup_database():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
                                    guild_id INTEGER PRIMARY KEY,
                                    channel_id INTEGER NOT NULL)''')
            await cursor.execute('''CREATE TABLE IF NOT EXISTS potd_last_post (
                                    date TEXT PRIMARY KEY)''')
        await conn.commit()

async def add_channel(guild_id: int, channel_id: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''REPLACE INTO channels (guild_id, channel_id) VALUES (?, ?)''',
                                 (guild_id, channel_id))
        await conn.commit()

async def get_channels():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT channel_id FROM channels')
            channels = await cursor.fetchall()
    return [channel[0] for channel in channels]

async def get_last_post_date():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT date FROM potd_last_post ORDER BY date DESC LIMIT 1')
            date = await cursor.fetchone()
    return date[0] if date else None

async def update_last_post_date(date: str):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM potd_last_post')
            await cursor.execute('INSERT INTO potd_last_post (date) VALUES (?)', (date,))
        await conn.commit()

def plot_map(longitude: float, latitude: float) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(10, 7))
    m = Basemap(projection='cyl', resolution='l', ax=ax)

    m.drawcoastlines(color='grey')
    m.drawcountries(color='grey')
    m.drawmapboundary(fill_color='grey')
    m.fillcontinents(color='black', lake_color='grey')

    x, y = m(longitude, latitude)
    m.plot(x, y, 'ro', markersize=24)

    plt.plot()

    ax.set_title('The location of the ISS', size=36)
    
    buffer: io.BytesIO = io.BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    
    plt.close(fig)
    
    buffer.seek(0)
    return buffer

async def load_cogs(bot: commands.Bot):
    loaded = []
    for cog_file in settings.COGS_DIR.glob("*.py"):
        if cog_file.name != "__init__.py":
            await bot.load_extension(f"cogs.{cog_file.name[:-3]}")
            loaded.append("cogs." + cog_file.name[:-3])
    loaded_str = ""
    for i in loaded:
        loaded_str += f"{i}, "
    print(f"{loaded_str} successfully loaded")

async def fetch_moon_phase(timezone: str = "EST", location: str = "New York, USA"):
    try:
        tz = pytz.timezone(timezone)
        dt = str(datetime.now(tz)).split(" ")[0]
    except pytz.UnknownTimeZoneError:
        return "Unknown timezone. Please specify a valid timezone."
    
    geocode_data = await retrieve("https://nominatim.openstreetmap.org/search", params={"q": location, "format": "json"}, api_key_required=False)
    try:
        if not geocode_data or not geocode_data[0].get("place_id"):
            return "Unable to retrieve location data. Please try again with a different location. Maybe it was a typo?"
    except IndexError:
        return "Unable to retrieve location data. Please try again with a different location. Maybe it was a typo?"
    
    first_result = geocode_data[0]
    latitude = float(first_result["lat"])
    longitude = float(first_result["lon"])

    url = "https://api.astronomyapi.com/api/v2/studio/moon-phase"
    payload = {
        "style": {
            "moonStyle": "default",
            "backgroundStyle": "stars",
            "backgroundColor": "#000000",
            "headingColor": "#ff2424",
            "textColor": "#ff0000"
        },
        "observer": {
            "latitude": latitude,
            "longitude": longitude,
            "date": dt
        },
        "view": {
            "type": "landscape-simple",
            "parameters": {}
        }
    }
    
    token = settings.ASTRO_API
    headers = {
        'Authorization': f"Basic {token}",
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            data = await response.json()
            image_url = data["data"]["imageUrl"]
            
            async with session.get(image_url) as image_response:
                image_bytes = await image_response.read()
    
    return image_bytes
async def setup_database():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
                                    guild_id INTEGER PRIMARY KEY,
                                    channel_id INTEGER NOT NULL)''')
            await cursor.execute('''CREATE TABLE IF NOT EXISTS potd_last_post (
                                    date TEXT PRIMARY KEY)''')
            await cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                    user_id INTEGER PRIMARY KEY,
                                    balance INTEGER NOT NULL DEFAULT 0,
                                    last_daily TEXT)''')
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

async def claim_daily(user_id: int) -> int:
    reward = 1000
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?', (reward, datetime.utcnow().isoformat(), user_id))
            await conn.commit()
    return reward

async def transfer_credits(sender_id: int, receiver_id: int, amount: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, sender_id))
            await cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?', (receiver_id, amount, amount))
            await conn.commit()


async def setup_database():
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
                                    guild_id INTEGER PRIMARY KEY,
                                    channel_id INTEGER NOT NULL)''')
            await cursor.execute('''CREATE TABLE IF NOT EXISTS potd_last_post (
                                    date TEXT PRIMARY KEY)''')
            await cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                    user_id INTEGER PRIMARY KEY,
                                    balance INTEGER NOT NULL DEFAULT 0,
                                    last_daily TEXT)''')
            await cursor.execute('''CREATE TABLE IF NOT EXISTS shop_items (
                                    item_id TEXT PRIMARY KEY,
                                    item_name TEXT NOT NULL,
                                    item_price INTEGER NOT NULL)''')
            await cursor.execute('''CREATE TABLE IF NOT EXISTS user_inventory (
                                    user_id INTEGER NOT NULL,
                                    item_id TEXT NOT NULL,
                                    quantity INTEGER NOT NULL,
                                    PRIMARY KEY (user_id, item_id),
                                    FOREIGN KEY (item_id) REFERENCES shop_items(item_id))''')
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

async def add_to_inventory(user_id: int, item_id: str, quantity: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''INSERT INTO user_inventory (user_id, item_id, quantity)
                                   VALUES (?, ?, ?)
                                   ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + ?''',
                                 (user_id, item_id, quantity, quantity))
        await conn.commit()

async def get_inventory(user_id: int):
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''SELECT shop_items.item_name, shop_items.item_id, user_inventory.quantity
                                   FROM user_inventory
                                   JOIN shop_items ON user_inventory.item_id = shop_items.item_id
                                   WHERE user_inventory.user_id = ?''', (user_id,))
            inventory = await cursor.fetchall()
    return inventory



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

async def add_balance(user_id: int, amount: int) -> None:
    async with asqlite.connect('space.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
            await cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            await conn.commit()
