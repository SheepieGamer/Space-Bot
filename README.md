# Space Enthusiast

**Space Enthusiast** is a Discord bot designed to provide a range of space-related features and interactive commands. It integrates with NASA's APIs, astronomy data, and more to offer users interesting content about space, including Astronomy Picture of the Day, star charts, and moon phases. Additionally, it supports a trading system and various economy-related commands.

## Features

- **NASA's Astronomy Picture of the Day (POTD)**: Automatically posts the latest Astronomy Picture of the Day in specified channels.
- **Star Charts**: Generates and displays star charts based on user-specified locations and dates.
- **Moon Phases**: Provides current moon phase information for a given location and timezone.
- **Trading System**: Allows users to trade items with each other.
- **Economy Commands**: Includes various commands for managing in-game economy, such as balance, buy, sell, and jobs.
- **Space Information**: Retrieves information about SpaceX launches, ISS location, and more.

## Installation

### Prerequisites

1. **Python 3.8+**: Ensure you have Python 3.8 or later installed.
2. **API Keys**: Obtain API keys for [NASA](https://api.nasa.gov), [Discord](https://discord.com/developers/applications), [AstronomyAPI](https://docs.astronomyapi.com), and [OpenWeatherMap](https://home.openweathermap.org/api_keys)

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/SheepieGamer/Space-Bot.git
   cd space-bot
   ```

2. **Create a Virtual Environment (optional but recommended)**

   ```bash
   pip install virtualenv
   virtualenv .venv
   .venv/scripts/activate
   ```

3. **Install Dependencies**

   Install the required Python packages listed in `requirements.txt`.

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the root directory and add the following variables:

   ```
   BOT_TOKEN = "your_discord_bot_token"
   NASA_TOKEN = "your_nasa_api_key"
   MAP_TOKEN = "your_openweathermap_token"
   ```

ASTRO_API_SECRET = "your_astronomyapi_secret"
ASTRO_API_ID = "your_astronomyapi_id"

````

5. **Set Up the Database**

The bot uses an SQLite database (`space.db`) to store information. Ensure the database file is present in the root directory, or the bot will create it as needed.

6. **Run the Bot**

Start the bot using the following command:

```bash
python main.py
````

## Usage

- **Commands**: The bot supports various commands including `!photo_otd`, `!rover_photo`, `!next_launch`, `!astronauts`, `!iss_location`, `!moon_phase`, `!star_chart`, and more.
- **Economy Commands**: Use commands like `!apply`, `!balance`, `!buy`, `!sell`, `!job`, and `!trade` for in-game economy management.

## Contributing

Feel free to contribute by opening issues or pull requests. Please ensure you follow the coding style and conventions used in the project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
