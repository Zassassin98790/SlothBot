"""
Configuration module for Torn City Discord Bot.
Handles environment variables and bot settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Bot configuration class."""
    
    def __init__(self):
        # Discord Bot Configuration
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        self.COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
        
        # Torn City API Configuration
        self.TORN_API_KEY = os.getenv("TORN_API_KEY")
        self.TORN_API_BASE_URL = "https://api.torn.com"
        
        # Rate Limiting Configuration
        self.API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "100"))  # requests per minute
        self.SCRAPE_RATE_LIMIT = int(os.getenv("SCRAPE_RATE_LIMIT", "30"))  # requests per minute
        
        # Bot Settings
        self.MAX_MESSAGE_LENGTH = 2000  # Discord message limit
        self.EMBED_COLOR = 0x00ff00  # Green color for embeds
        self.ERROR_COLOR = 0xff0000  # Red color for error embeds
        
        # Web Scraping Settings
        self.USER_AGENT = "TornCityBot/1.0 (Discord Bot)"
        self.REQUEST_TIMEOUT = 30
        
    def validate(self):
        """Validate required configuration."""
        if not self.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required")
        return True
