import asqlite
import aiohttp
import io
from starplot import MapPlot, Projection, Star
from starplot.styles import PlotStyle, extensions
from discord.ext import commands
import pytz
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

def make_embed(title=None, description=None, color=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed