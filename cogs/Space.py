import discord
from discord.ext import commands
import settings
import pytz
from datetime import datetime, timedelta

import random
import asyncio
import settings.command_info as cmd_info
from utils import *

class Space(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
    
    @commands.hybrid_command(name=cmd_info.PHOTO_OTD_NAME, description=cmd_info.PHOTO_OTD_DESC, aliases=cmd_info.PHOTO_OTD_ALIASES)
    @commands.cooldown(1,5, commands.BucketType.user)
    async def photo_otd(self, ctx: commands.Context):
        """
        Displays the NASA Astronomy Picture of the Day.

        Parameters:
        None

        Returns:
        It sends a message to the Discord channel with the Astronomy Picture of the Day.
        """
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

        await msg.edit(content=None, embed=embed)

    @photo_otd.error
    async def potd_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name=cmd_info.ROVER_PHOTO_NAME, description=cmd_info.ROVER_PHOTO_DESC, aliases=cmd_info.ROVER_PHOTO_ALIASES)
    @commands.cooldown(1,5, commands.BucketType.user)
    async def rover_photo(self, ctx: commands.Context):
        """
        Displays a random image from the Mars Rover Curiosity's photos.
        If no images are found, it sends a message indicating that no images were found.

        Parameters:
        None.

        Returns:
        It sends a message to the Discord channel with an image taken from the Mars Rover Curiosity.
        """
        msg = await ctx.reply("Working on it...")
        data = await retrieve(f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos", params={"sol": "4000"})
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
            await msg.edit(content=None, embed=embed)
        else:
            await msg.edit(content="No images found.")

    @rover_photo.error
    async def rover_photo_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name=cmd_info.NEXT_LAUNCH_NAME, description=cmd_info.NEXT_LAUNCH_DESC, aliases=cmd_info.NEXT_LAUNCH_ALIASES)
    @commands.cooldown(1,5, commands.BucketType.user)
    async def next_launch(self, ctx: commands.Context):
        """
        Displays information about the next SpaceX launch.

        Parameters:
        None.
        
        Returns:
        It sends a message to the Discord channel with information about the next SpaceX launch.
        """
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
        await msg.edit(content=None, embed=embed)

    @next_launch.error
    async def next_launch_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name=cmd_info.ASTROS_NAME, description=cmd_info.ASTROS_DESC, aliases=cmd_info.ASTROS_ALIASES)
    @commands.cooldown(1,5, commands.BucketType.user)
    async def astronauts(self, ctx: commands.Context, max=commands.parameter(default=30, description="Maximum number of people to list. Caps at 30")):
        """
        Displays information about the current astronauts in space.

        Parameters:
        max (int, optional): The maximum number of astronauts to display. Defaults to 30.

        Returns:
        It sends a message to the Discord channel with information about the current astronauts in space.
        """
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

        await msg.edit(content=None, embed=embed)

    @astronauts.error
    async def astronauts_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name=cmd_info.ISS_NAME, description=cmd_info.ISS_DESC, aliases=cmd_info.ISS_ALIASES)
    @commands.cooldown(1,5, commands.BucketType.user)
    async def iss_location(self, ctx: commands.Context):
        """
        Shows the current location of the International Space Station.

        Parameters:
        None.

        Returns:
        It sends a message to the Discord channel with the current ISS location, represented by latitude and longitude.
        Additionally, it generates a map image of the ISS location and attaches it to the message.
        """
        msg = await ctx.reply("Working on it...")
        data = await retrieve("http://api.open-notify.org/iss-now.json", api_key_required=False)
        iss_position = data['iss_position']
        latitude = iss_position['latitude']
        longitude = iss_position['longitude']

        buffer = await asyncio.to_thread(plot_map, float(longitude), float(latitude))

        if str(latitude).startswith('-'):
            new_latitude = f"{str(latitude).strip('-')}° S"
        else:
            new_latitude = f"{str(latitude).strip('+')}° N"

        if str(longitude).startswith('-'):
            new_longitude = f"{str(longitude).strip('-')}° W"
        else:
            new_longitude = f"{str(longitude).strip('+')}° E"


        file = discord.File(buffer, filename="iss-location.png")
        embed = discord.Embed(
            title="The International Space Station is currently at:",
            description=f"**Latitude:** {new_latitude}\n"
                        f"**Longitude:** {new_longitude}",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://iss-location.png")

        await msg.edit(content=None, embed=embed, attachments=[file])

    @iss_location.error
    async def iss_location_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='moon-phase')
    @commands.cooldown(1,5, commands.BucketType.user)
    async def moon_phase(self, ctx: commands.Context, timezone: str = "EST", *, location: str = "New York, USA"):
        """
        Displays the current moon phase image for the specified timezone and location.

        Parameters:
        timezone (str, optional): The timezone for the moon phase. Defaults to "EST".
        location (str, optional): The location for which the moon phase is to be displayed. Defaults to "New York, USA".

        Returns:
        If the moon phase image is successfully fetched, it sends a message to the Discord channel with the image.
        """
        msg = await ctx.reply("Working on it...")
        image_bytes = await fetch_moon_phase(timezone, location)
        
        if isinstance(image_bytes, str):
            await msg.edit(content=image_bytes)
        else:
            file = discord.File(io.BytesIO(image_bytes), filename="moon_phase_image.png")
            embed = discord.Embed(color=discord.Color.random())
            embed.set_image(url="attachment://moon_phase_image.png")
            await msg.edit(content=None, embed=embed, attachments=[file])

    @moon_phase.error
    async def moon_phase_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name="star-chart", description="Generates a star chart for the specified date and location.")
    @commands.cooldown(1,5, commands.BucketType.user)
    async def star_chart(self, ctx: commands.Context, timezone: str = commands.parameter(default="EST", description="The timezone you want the star chart to appear in."), *, location: str = commands.parameter(default="New York, USA", description="Search query for location. Doesn't need to be exact.")):
        """
        Generates a star chart for the specified date and location.

        Parameters:
        timezone (str, optional): The timezone for the date and location. Defaults to "EST".
        location (str, optional): The location for which the star chart is generated. Defaults to "New York, USA".

        Returns:
        It sends a message to the Discord channel with the generated star chart image.
        """
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
        
        try:
            tz = pytz.timezone(timezone)
            dt = datetime.now(tz)
        except pytz.UnknownTimeZoneError:
            await msg.edit("Unknown timezone. Please specify a valid timezone.")
            return
        
        buffer = await asyncio.to_thread(generate_star_chart, latitude, longitude, dt)

        file = discord.File(buffer, filename="star_chart_detail.png")
        embed = discord.Embed(
            title=f"Star Chart for {location} at {dt.strftime('%Y-%m-%d %H:%M:%S')} {timezone}",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://star_chart_detail.png")

        await msg.edit(content=None, embed=embed, attachments=[file])

    @star_chart.error
    async def star_chart_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name="space-fact", description="Shares a random space fact.")
    @commands.cooldown(1,5, commands.BucketType.user)
    async def space_fact(self, ctx: commands.Context):
        """
        This command sends a random space fact.

        Parameters:
        None.

        Returns:
        An image with a random space fact.
        """
        msg = await ctx.reply("Working on it...")
        number = random.randint(1, 62)
        url = f"https://www.spacecentre.nz/resources/facts/random/{number}.jpg"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    embed=discord.Embed(
                        title="Failed to retrieve image.",
                        color=discord.Color.red()
                    )
                    await ctx.reply(embed=embed)
                    return

                image_data = await response.read()

        image_bytes = io.BytesIO(image_data)

        embed = discord.Embed(
            title="Random Space Fact",
            color=discord.Color.random(),
            url=url
        )
        embed.set_image(url=f"attachment://space_fact{number}.jpg")

        # Send the image as an attachment
        await msg.edit(content=None, embed=embed, attachments=[discord.File(fp=image_bytes, filename=f"space_fact{number}.jpg")])

    @space_fact.error
    async def space_fact_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='weather', description='Provides current weather information for a specified city.')
    @commands.cooldown(1,5, commands.BucketType.user)
    async def weather(self, ctx: commands.Context, units: str="imperial", *, location: str = "New York, USA"):
        """Fetches and displays current weather information for a specified city or coordinates."""
        
        msg = await ctx.reply("Working on it...")

        if units not in ['imperial','metric']:
            embed=discord.Embed(
                description="Invalid unit. Please use either 'imperial' or 'metric'.",
                color=discord.Color.red()
            )
            await msg.edit(content=None, embed=embed)
            return

        geocode_data = await retrieve("https://nominatim.openstreetmap.org/search", params={"q": location, "format": "json"}, api_key_required=False)
        try:
            if not geocode_data or not geocode_data[0].get("place_id"):
                embed = discord.Embed(
                    description="Unable to retrieve location data. Please try again with a different location. Maybe it was a typo?",
                    color=discord.Color.red()
                )
                return await msg.edit(content=None, embed=embed)
        except IndexError:
            embed=discord.Embed(
                description="Unable to retrieve location data. Please try again with a different location. Maybe it was a typo?",
                color=discord.Color.red()
            )
            return await msg.edit(content=None, embed=embed)
        
        first_result = geocode_data[0]
        latitude = float(first_result["lat"])
        longitude = float(first_result["lon"])

        api_key = settings.OPEN_WEATHER
        base_url = 'http://api.openweathermap.org/data/2.5/weather'
        params = {
            'appid': api_key,
            'units': units,
            'lat': latitude,
            'lon': longitude
        }

        data: dict = await retrieve(base_url, params=params, api_key_required=False)

        if data.get('cod') != 200:
            await msg.edit(content="Unable to retrieve weather information. Please check the location.")
            return

        embed = discord.Embed(
            title=f"Weather in {data['name']}, {data['sys']['country']}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Temperature", value=f"{data['main']['temp']}°{'C' if units == 'metric' else 'F'}", inline=True)
        embed.add_field(name="Weather", value=data['weather'][0]['description'].capitalize(), inline=True)
        embed.add_field(name="Humidity", value=f"{data['main']['humidity']}%", inline=True)
        embed.add_field(name="Wind Speed", value=f"{data['wind']['speed']} {'m/s' if units == 'metric' else 'mph'}", inline=True)
        await msg.edit(content=None, embed=embed)

    @weather.error
    async def weather_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after_seconds = error.retry_after
            cooldown_end_time = discord.utils.utcnow() + timedelta(seconds=retry_after_seconds)

            formatted_timestamp = discord.utils.format_dt(cooldown_end_time, style='R')

            embed = discord.Embed(
                title="Slow it down!",
                description=f"Hey! You can do that again {formatted_timestamp}."
            )
            await ctx.reply(embed=embed)



async def setup(bot: commands.Bot):
    await bot.add_cog(Space(bot))