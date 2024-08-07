import asqlite
import aiohttp
import io
from starplot import MapPlot, Projection, Star
from starplot.styles import PlotStyle, extensions
import tempfile
import os
from discord.ext import commands
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from datetime import datetime
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
    async with asqlite.connect('channels.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
                                    guild_id INTEGER PRIMARY KEY,
                                    channel_id INTEGER NOT NULL)''')
            await cursor.execute('''CREATE TABLE IF NOT EXISTS potd_last_post (
                                    date TEXT PRIMARY KEY)''')
        await conn.commit()

async def add_channel(guild_id: int, channel_id: int):
    async with asqlite.connect('channels.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''REPLACE INTO channels (guild_id, channel_id) VALUES (?, ?)''',
                                 (guild_id, channel_id))
        await conn.commit()

async def get_channels():
    async with asqlite.connect('channels.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT channel_id FROM channels')
            channels = await cursor.fetchall()
    return [channel[0] for channel in channels]

async def get_last_post_date():
    async with asqlite.connect('channels.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT date FROM potd_last_post')
            date = await cursor.fetchone()
    return date[0] if date else None

async def update_last_post_date(date: str):
    async with asqlite.connect('channels.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('REPLACE INTO potd_last_post (date) VALUES (?)', (date,))
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