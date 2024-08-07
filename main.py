import discord
from utils import *
from discord.ext import commands, tasks
import settings
import settings.command_info as cmd_info
from pytz import timezone
import tempfile
import os
from starplot import MapPlot, Projection, Star
from starplot.styles import PlotStyle, extensions
import asyncio
import pytz
import random
from datetime import datetime


bot = commands.Bot(command_prefix=settings.COMMAND_PREFIX, intents=settings.INTENTS, activity=settings.ACTIVITY)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await setup_database()
    post_potd.start()


@bot.command(name=cmd_info.PHOTO_OTD_NAME, description=cmd_info.PHOTO_OTD_DESC, aliases=cmd_info.PHOTO_OTD_ALIASES)
async def photo_otd(ctx: commands.Context):
    msg = await ctx.reply("Working on it...")
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

    await msg.edit(content="", embed=embed)

@bot.command(name=cmd_info.ROVER_PHOTO_NAME, description=cmd_info.ROVER_PHOTO_DESC, aliases=cmd_info.ROVER_PHOTO_ALIASES)
async def rover_photo(ctx: commands.Context):
    msg = await ctx.reply("Working on it...")
    data = await retrieve(f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos", params={"sol": "1000"})
    img_src_list = []
    for photo in data.get('photos', []):
        img_src = photo.get('img_src')
        if img_src:
            img_src_list.append(img_src)
        if len(img_src_list) >= 1000:
            break

    if img_src_list:
        img = random.choice(img_src_list)
        embed = discord.Embed(
            color=discord.Color.dark_green()
        )
        embed.set_footer(text="Photo taken from Curiosity on Mars.")
        embed.set_image(url=img)
        await msg.edit(content="", embed=embed)
    else:
        await msg.edit(content="No images found.")

@bot.command(name=cmd_info.SETUP_POTD_NAME, description=cmd_info.SETUP_POTD_DESC, aliases=cmd_info.SETUP_POTD_ALIASES)
@commands.has_permissions(administrator=True)
async def setup_potd(ctx: commands.Context, channel: discord.TextChannel):
    msg = await ctx.reply("Working on it...")
    await add_channel(ctx.guild.id, channel.id)
    await msg.edit(content=f"Channel {channel.mention} has been set up for Space Photo Of The Day!")

@tasks.loop(hours=24)
async def post_potd():
    await bot.wait_until_ready()
    

    last_post_date = await get_last_post_date()
    today = datetime.utcnow().date().isoformat()

    if last_post_date == today:
        return

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

@bot.command(name=cmd_info.NEXT_LAUNCH_NAME, description=cmd_info.NEXT_LAUNCH_DESC, aliases=cmd_info.NEXT_LAUNCH_ALIASES)
async def next_launch(ctx: commands.Context):
    msg = await ctx.reply("Working on it...")
    data = await retrieve("https://api.spacexdata.com/v4/launches/next", api_key_required=False)
    launch_name = data['name']
    launch_date = data['date_utc']
    rocket = data['rocket']
    mission = data.get('details', 'No details available')
    launch_pad = data['launchpad']

    embed = discord.Embed(
        title="Next SpaceX Launch",
        description=f"**Mission Name:** {launch_name}\n"
                    f"**Launch Date:** {launch_date}\n"
                    f"**Rocket:** {rocket}\n"
                    f"**Details:** {mission}\n"
                    f"**Launch Pad:** {launch_pad}",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Information may be outdated if a next launch is not scheduled.")
    await msg.edit(content="", embed=embed)

@bot.command(name=cmd_info.ASTROS_NAME, description=cmd_info.ASTROS_DESC, aliases=cmd_info.ASTROS_ALIASES)
async def astronauts(ctx: commands.Context, max=30):
    msg = await ctx.reply("Working on it...")
    if max > 30:
        max = 30
    data = await retrieve("http://api.open-notify.org/astros.json", api_key_required=False)
    people = data["people"]
    embed = discord.Embed(
        title="Every current astronaut.",
        color=discord.Color.dark_green()
    )
    amount = 0
    for person in people:
        name = person["name"]
        craft = person["craft"]
        amount += 1
        if amount > max:
            break
        embed.add_field(name=name, value=craft, inline=True)
    
    embed.set_footer(text=f"{amount} people are in space right now")

    await msg.edit(content="", embed=embed)

@bot.command(name=cmd_info.ISS_NAME, description=cmd_info.ISS_DESC, aliases=cmd_info.ISS_ALIASES)
async def iss_location(ctx: commands.Context):
    msg = await ctx.reply("Working on it...")
    data = await retrieve("http://api.open-notify.org/iss-now.json", api_key_required=False)
    iss_position = data['iss_position']
    latitude = iss_position['latitude']
    longitude = iss_position['longitude']

    buffer = await asyncio.to_thread(plot_map, float(longitude), float(latitude))

    file = discord.File(buffer, filename="iss-location.png")
    embed = discord.Embed(
        title="The International Space Station is currently at:",
        description=f"**Latitude:** {latitude}\n"
                    f"**Longitude:** {longitude}",
        color=discord.Color.green()
    )
    embed.set_image(url="attachment://iss-location.png")

    await msg.edit(content="", embed=embed, attachments=[file])

@bot.command(name="star-chart", description="Generates a star chart for the specified date and location.")
async def star_chart(ctx: commands.Context, timezone: str = "EST", *, location: str = "New York, USA"):
    msg = await ctx.reply("Working on it...")
    
    geocode_data = await retrieve("https://nominatim.openstreetmap.org/search", params={"q": location, "format": "json"}, api_key_required=False)
    try:
        if not geocode_data or not geocode_data[0].get("place_id"):
            await msg.edit(content="Unable to retrieve location data. Please try again with a different location. Maybe it was a typo?")
            return
    except IndexError:
        await msg.edit(content="Unable to retrieve location data. Please try again with a different location. Maybe it was a typo?")
        return
    
    first_result = geocode_data[0]
    latitude = float(first_result["lat"])
    longitude = float(first_result["lon"])
    
    # Get current time in the specified timezone
    try:
        tz = pytz.timezone(timezone)
        dt = datetime.now(tz)
    except pytz.UnknownTimeZoneError:
        await msg.edit("Unknown timezone. Please specify a valid timezone.")
        return
    
    # Generate the star chart asynchronously
    buffer = await asyncio.to_thread(generate_star_chart, latitude, longitude, dt)

    file = discord.File(buffer, filename="star_chart_detail.png")
    embed = discord.Embed(
        title=f"Star Chart for {location} at {dt.strftime('%Y-%m-%d %H:%M:%S')} {timezone}",
        color=discord.Color.blue()
    )
    embed.set_image(url="attachment://star_chart_detail.png")

    await msg.edit(content="", embed=embed, attachments=[file])

@bot.command()
async def edit(ctx: commands.Context):
    msg = await ctx.reply("HGello!")

    await asyncio.sleep(2)

    embed=discord.Embed(title="jfnksdjf")

    await msg.edit(content="HIII", embed=embed)


bot.run(settings.TOKEN)
