from dotenv import load_dotenv
load_dotenv()
import os
import pathlib
import discord
import base64

from discord.ext import commands

TOKEN = os.getenv('BOT_TOKEN') # Discord bot token
NASA = os.getenv('NASA_TOKEN') # Nasa API token
OPEN_WEATHER = os.getenv('MAP_TOKEN') # https://home.openweathermap.org/api_keys


ASTRO_ID = os.getenv('ASTRO_API_ID')
ASTRO_SECRET = os.getenv('ASTRO_API_SECRET')
userpass = f"{ASTRO_ID}:{ASTRO_SECRET}"
ASTRO_API = base64.b64encode(userpass.encode()).decode() # https://docs.astronomyapi.com


COMMAND_PREFIX = commands.when_mentioned_or("s!")
INTENTS = discord.Intents.all()
ACTIVITY = discord.Activity(type=discord.ActivityType.watching, name="over space. | s!help")
STATUS = discord.Status.idle

BASE_DIR = pathlib.Path(__file__).parent.parent
COGS_DIR = BASE_DIR / "cogs"
