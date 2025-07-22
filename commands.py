"""
Discord bot commands for Torn City integration.
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from .torn_api import TornAPI
from .web_scraper import TornScraper
from .utils import create_embed, create_error_embed, format_number

logger = logging.getLogger(__name__)


class TornCommands(commands.Cog):
    """Cog containing all Torn City related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.torn_api = TornAPI(self.config)
        self.scraper = TornScraper(self.config)

    @app_commands.command(
        name="help", description="Display help information about bot commands")
    async def help_command(self, interaction: discord.Interaction):
        """Display help information."""
        embed = create_embed("Torn City Bot Commands",
                             "Available slash commands:")

        # API Commands
        api_commands = [
            "`/profile [user_id]` - Get player profile",
            "`/stats [user_id]` - Get player stats",
            "`/faction [faction_id]` - Get faction info"
        ]
        embed.add_field(name="API Commands",
                        value="\n".join(api_commands),
                        inline=False)

        # Scraping Commands
        scrape_commands = [
            "`/news` - Latest Torn City news", "`/events` - Current events",
            "`/prices [item_id]` - Item market prices by ID"
        ]
        embed.add_field(name="Web Scraping Commands",
                        value="\n".join(scrape_commands),
                        inline=False)

        embed.add_field(
            name="Note",
            value="Some commands require a Torn City API key to be configured.",
            inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="profile",
        description="Get player profile information from Torn City API")
    @app_commands.describe(user_id="The Torn City user ID to look up")
    async def profile(self, interaction: discord.Interaction, user_id: int):
        """Get player profile information from Torn City API."""
        try:
            if not self.config.TORN_API_KEY:
                embed = create_error_embed(
                    "API Key Required",
                    "This command requires a Torn City API key to be configured."
                )
                await interaction.response.send_message(embed=embed)
                return

            profile_data = await self.torn_api.get_user_profile(user_id)

            if not profile_data:
                embed = create_error_embed(
                    "User Not Found",
                    f"Could not find user with ID {user_id}.")
                await interaction.response.send_message(embed=embed)
                return

            embed = create_embed(
                f"Profile: {profile_data.get('name', 'Unknown')}",
                f"Level {profile_data.get('level', 'N/A')}")

            embed.add_field(
                name="Basic Info",
                value=f"**ID:** {profile_data.get('player_id', 'N/A')}\n"
                f"**Rank:** {profile_data.get('rank', 'N/A')}\n"
                f"**Age:** {profile_data.get('age', 'N/A')} days",
                inline=True)

            if 'faction' in profile_data:
                faction = profile_data['faction']
                embed.add_field(
                    name="Faction",
                    value=f"**Name:** {faction.get('faction_name', 'N/A')}\n"
                    f"**Position:** {faction.get('position', 'N/A')}",
                    inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            embed = create_error_embed(
                "Error", "Failed to retrieve profile information.")
            await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="stats", description="Get player battle stats from Torn City API")
    @app_commands.describe(user_id="The Torn City user ID to look up")
    async def stats(self, interaction: discord.Interaction, user_id: int):
        """Get player stats from Torn City API."""
        try:
            if not self.config.TORN_API_KEY:
                embed = create_error_embed(
                    "API Key Required",
                    "This command requires a Torn City API key to be configured."
                )
                await interaction.response.send_message(embed=embed)
                return

            stats_data = await self.torn_api.get_user_stats(user_id)

            if not stats_data:
                embed = create_error_embed(
                    "Stats Not Found",
                    f"Could not find stats for user ID {user_id}.")
                await interaction.response.send_message(embed=embed)
                return

            embed = create_embed(f"Stats for User {user_id}",
                                 "Battle Statistics")

            if 'strength' in stats_data:
                embed.add_field(
                    name="Battle Stats",
                    value=
                    f"**Strength:** {format_number(stats_data.get('strength', 0))}\n"
                    f"**Defense:** {format_number(stats_data.get('defense', 0))}\n"
                    f"**Speed:** {format_number(stats_data.get('speed', 0))}\n"
                    f"**Dexterity:** {format_number(stats_data.get('dexterity', 0))}",
                    inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            embed = create_error_embed(
                "Error", "Failed to retrieve stats information.")
            await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="faction",
        description="Get faction information from Torn City API")
    @app_commands.describe(faction_id="The Torn City faction ID to look up")
    async def faction(self, interaction: discord.Interaction, faction_id: int):
        """Get faction information from Torn City API."""
        try:
            if not self.config.TORN_API_KEY:
                embed = create_error_embed(
                    "API Key Required",
                    "This command requires a Torn City API key to be configured."
                )
                await interaction.response.send_message(embed=embed)
                return

            # Defer response since API calls might take a moment
            await interaction.response.defer()

            # Get both basic faction info and members data
            faction_data = await self.torn_api.get_faction_info(faction_id)
            members_data = await self.torn_api.get_faction_members(faction_id)

            if not faction_data:
                embed = create_error_embed(
                    "Faction Not Found",
                    f"Could not find faction with ID {faction_id}. Please verify the faction ID."
                )
                await interaction.followup.send(embed=embed)
                return

            embed = create_embed(
                f"Faction: {faction_data.get('name', 'Unknown')}",
                f"[{faction_data.get('tag', 'N/A')}]")

            # Basic faction info
            embed.add_field(name="📊 Basic Info",
                            value=f"**ID:** {faction_data.get('ID', 'N/A')}\n"
                            f"**Age:** {faction_data.get('age', 'N/A')} days",
                            inline=True)

            # Members information with hospital status
            if members_data:
                healthy_members = []
                hospitalized_members = []

                for member_id, member_info in members_data.items():
                    if isinstance(member_info, dict):
                        name = member_info.get('name', f'User {member_id}')
                        status = member_info.get('status', {})

                        # Check hospital status
                        if isinstance(status, dict):
                            state = status.get('state', '')
                            if state == 'Hospital':
                                hospitalized_members.append(f"🔴 {name}")
                            else:
                                healthy_members.append(f"🟢 {name}")
                        else:
                            healthy_members.append(f"🟢 {name}")

                # Display healthy members (up to 10)
                if healthy_members:
                    healthy_list = healthy_members[:10]
                    if len(healthy_members) > 10:
                        healthy_list.append(
                            f"... and {len(healthy_members) - 10} more")

                    embed.add_field(name=f"🟢 Healthy ({len(healthy_members)})",
                                    value="\n".join(healthy_list),
                                    inline=True)

                # Display hospitalized members
                if hospitalized_members:
                    hosp_list = hospitalized_members[:10]
                    if len(hospitalized_members) > 10:
                        hosp_list.append(
                            f"... and {len(hospitalized_members) - 10} more")

                    embed.add_field(
                        name=f"🔴 Hospital ({len(hospitalized_members)})",
                        value="\n".join(hosp_list),
                        inline=True)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in faction command: {e}")
            embed = create_error_embed(
                "Error", "Failed to retrieve faction information.")
            try:
                await interaction.followup.send(embed=embed)
            except:
                await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="prices",
        description="Get current market prices for an item by ID")
    @app_commands.describe(
        item_id="The Torn City item ID to look up market prices for")
    async def prices(self, interaction: discord.Interaction, item_id: int):
        """Get current market prices for an item by ID using Torn City API."""
        try:
            if not self.config.TORN_API_KEY:
                embed = create_error_embed(
                    "API Key Required",
                    "This command requires a Torn City API key to be configured."
                )
                await interaction.response.send_message(embed=embed)
                return

            # Defer response since API calls might take a moment
            await interaction.response.defer()

            # Get item information and market data
            item_info = await self.torn_api.get_item_info(item_id)
            market_data = await self.torn_api.get_item_market(item_id)

            if not item_info:
                embed = create_error_embed(
                    "Item Not Found",
                    f"Could not find item with ID {item_id}. Please verify the item ID."
                )
                await interaction.followup.send(embed=embed)
                return

            item_name = item_info.get('name', f'Item {item_id}')
            item_description = item_info.get('description',
                                             'No description available')

            embed = create_embed(f"Market Prices: {item_name}",
                                 f"Item ID: {item_id}")

            # Add item description
            embed.add_field(
                name="Description",
                value=item_description[:200] +
                "..." if len(item_description) > 200 else item_description,
                inline=False)

            # Add market listings
            if market_data and len(market_data) > 0:
                try:
                    # Extract prices safely with better error handling
                    valid_listings = []
                    for listing in market_data:
                        if isinstance(listing, dict):
                            price = listing.get('cost', 0) or listing.get(
                                'price', 0)
                            quantity = listing.get('quantity', 1)
                            if price and price > 0:
                                valid_listings.append({
                                    'price': price,
                                    'quantity': quantity
                                })

                    if valid_listings:
                        # Sort by price (lowest first)
                        valid_listings.sort(key=lambda x: x['price'])

                        # Get top 10 lowest prices
                        lowest_prices = []
                        for listing in valid_listings[:10]:
                            price = listing['price']
                            quantity = listing['quantity']
                            lowest_prices.append(
                                f"${format_number(price)} (qty: {quantity})")

                        embed.add_field(name="🏆 Top 10 Lowest Prices",
                                        value="\n".join(lowest_prices),
                                        inline=False)

                        # Calculate price statistics
                        prices = [
                            listing['price'] for listing in valid_listings
                        ]
                        avg_price = sum(prices) / len(prices)
                        min_price = min(prices)
                        max_price = max(prices)

                        embed.add_field(
                            name="📊 Price Statistics",
                            value=f"**Lowest:** ${format_number(min_price)}\n"
                            f"**Highest:** ${format_number(max_price)}\n"
                            f"**Average:** ${format_number(int(avg_price))}\n"
                            f"**Total Listings:** {len(valid_listings)}",
                            inline=True)
                    else:
                        embed.add_field(
                            name="Market Status",
                            value=
                            "Market data found but no valid prices available.",
                            inline=False)
                except Exception as e:
                    logger.error(f"Error processing market data: {e}")
                    embed.add_field(
                        name="Market Status",
                        value="Error processing market data. Please try again.",
                        inline=False)
            else:
                embed.add_field(
                    name="Market Status",
                    value="No current market listings found for this item.\n"
                    "This item may not be currently listed on the market.",
                    inline=False)

            embed.set_footer(text="Data from Torn City API")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in prices command: {e}")
            embed = create_error_embed("Error",
                                       "Failed to retrieve market prices.")
            try:
                await interaction.followup.send(embed=embed)
            except:
                await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="bazaar",
        description="Get items from a player's bazaar by player ID")
    @app_commands.describe(
        player_id="The Torn City player ID to check bazaar items for")
    async def bazaar(self, interaction: discord.Interaction, player_id: int):
        """Get items from a player's bazaar by player ID using Torn City API."""
        try:
            if not self.config.TORN_API_KEY:
                embed = create_error_embed(
                    "API Key Required",
                    "This command requires a Torn City API key to be configured."
                )
                await interaction.response.send_message(embed=embed)
                return

            # Defer response since API calls might take a moment
            await interaction.response.defer()

            # Get player's basic info and bazaar data
            player_info = await self.torn_api.get_user_profile(player_id)
            bazaar_items = await self.torn_api.get_player_bazaar(player_id)

            if not player_info:
                embed = create_error_embed(
                    "Player Not Found",
                    f"Could not find player with ID {player_id}. Please verify the player ID."
                )
                await interaction.followup.send(embed=embed)
                return

            player_name = player_info.get('name', f'Player {player_id}')

            # Get online status and set appropriate indicator
            last_action = player_info.get('last_action', {})
            status = last_action.get('status', 'Offline')

            # Set status emoji based on online status
            if status == 'Online':
                status_indicator = "🟢 Online"
            elif status == 'Away':
                status_indicator = "🟠 Away"
            else:
                status_indicator = "🔴 Offline"

            embed = create_embed(
                f"Bazaar Items: {player_name}",
                f"Player ID: {player_id} • {status_indicator}\n"
                f"**Profile:** https://www.torn.com/profiles.php?XID={player_id}\n"
                f"**Bazaar:** https://www.torn.com/bazaar.php?userId={player_id}"
            )

            # Add bazaar items
            if bazaar_items and len(bazaar_items) > 0:
                # Sort items by price (lowest first)
                sorted_items = sorted(
                    bazaar_items,
                    key=lambda x: x.get('cost', 0)
                    if x.get('cost', 0) > 0 else float('inf'))

                # Show up to 15 items
                items_to_show = sorted_items[:15]
                item_list = []

                for item in items_to_show:
                    item_name = item.get('name', 'Unknown Item')
                    # Try different possible price fields
                    item_price = (item.get('cost', 0) or item.get('price', 0)
                                  or item.get('bazaar_cost', 0)
                                  or item.get('sell_price', 0))
                    # Try different possible quantity fields
                    item_quantity = (item.get('quantity', 1)
                                     or item.get('amount', 1)
                                     or item.get('qty', 1))

                    # Debug log for first few items (remove after testing)
                    # if len(item_list) < 3:
                    #     logger.info(f"Item debug - name: {item_name}, price: {item_price}, quantity: {item_quantity}, full item: {item}")

                    if item_price and item_price > 0:
                        item_list.append(
                            f"**{item_name}** - ${format_number(item_price)} (qty: {item_quantity})"
                        )
                    else:
                        item_list.append(
                            f"**{item_name}** - Price not set (qty: {item_quantity})"
                        )

                if item_list:
                    # Split into chunks if too many items
                    chunk_size = 10
                    for i in range(0, len(item_list), chunk_size):
                        chunk = item_list[i:i + chunk_size]
                        field_name = "🏪 Bazaar Items" if i == 0 else f"🏪 Bazaar Items (continued)"
                        embed.add_field(name=field_name,
                                        value="\n".join(chunk),
                                        inline=False)

                # Add summary statistics
                priced_items = [
                    item for item in bazaar_items
                    if (item.get('cost', 0) or item.get('price', 0) or item.
                        get('bazaar_cost', 0) or item.get('sell_price', 0)) > 0
                ]
                if priced_items:
                    prices = [(item.get('cost', 0) or item.get('price', 0)
                               or item.get('bazaar_cost', 0)
                               or item.get('sell_price', 0))
                              for item in priced_items]
                    avg_price = sum(prices) / len(prices)
                    min_price = min(prices)
                    max_price = max(prices)

                    # Calculate total bazaar value
                    total_bazaar_value = 0
                    for item in bazaar_items:
                        item_price = (item.get('cost', 0)
                                      or item.get('price', 0)
                                      or item.get('bazaar_cost', 0)
                                      or item.get('sell_price', 0))
                        item_quantity = (item.get('quantity', 1)
                                         or item.get('amount', 1)
                                         or item.get('qty', 1))
                        if item_price > 0:
                            total_bazaar_value += item_price * item_quantity

                    embed.add_field(
                        name="📊 Bazaar Statistics",
                        value=f"**Total Items:** {len(bazaar_items)}\n"
                        f"**Items with Prices:** {len(priced_items)}\n"
                        f"**Total Bazaar Value:** ${format_number(total_bazaar_value)}\n"
                        f"**Lowest Price:** ${format_number(min_price)}\n"
                        f"**Highest Price:** ${format_number(max_price)}\n"
                        f"**Average Price:** ${format_number(int(avg_price))}",
                        inline=True)
                else:
                    embed.add_field(
                        name="📊 Bazaar Statistics",
                        value=f"**Total Items:** {len(bazaar_items)}\n"
                        f"**Items with Prices:** 0\n"
                        f"Most items don't have prices set",
                        inline=True)
            else:
                embed.add_field(
                    name="Bazaar Status",
                    value=
                    "This player doesn't have any items in their bazaar currently.",
                    inline=False)

            embed.set_footer(text="Bazaar data from Torn City API")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in bazaar command: {e}")
            embed = create_error_embed(
                "Error", "Failed to retrieve bazaar information.")
            try:
                await interaction.followup.send(embed=embed)
            except:
                await interaction.response.send_message(embed=embed)
