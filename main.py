#!/usr/bin/env python3
"""
Torn City Discord Bot
A Discord bot for Torn City game integration with API calls and web scraping capabilities.
"""

import asyncio
import logging
import os
import sys
from bot.client import TornCityBot
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('torn_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the bot."""
    try:
        # Initialize configuration
        config = Config()
        
        # Validate required environment variables
        if not config.DISCORD_TOKEN:
            logger.error("DISCORD_TOKEN not found in environment variables")
            return
            
        if not config.TORN_API_KEY:
            logger.warning("TORN_API_KEY not found - some commands may not work")
        
        # Initialize and run the bot
        bot = TornCityBot(config)
        logger.info("Starting Torn City Discord Bot...")
        await bot.start(config.DISCORD_TOKEN)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
