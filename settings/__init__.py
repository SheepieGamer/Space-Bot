from dotenv import load_dotenv
load_dotenv()
import os
import pathlib
import discord
from discord.ext import commands

TOKEN = os.getenv('BOT_TOKEN') # Discord bot token
NASA = os.getenv('NASA_TOKEN') # Nasa API token

COMMAND_PREFIX = commands.when_mentioned_or("s!")
INTENTS = discord.Intents.all()
ACTIVITY = discord.Activity(type=discord.ActivityType.watching, name="over space.")

BASE_DIR = pathlib.Path(__file__).parent.parent
COGS_DIR = BASE_DIR / "cogs"
