"""
Torn City API integration module.
Handles all API calls to the Torn City API.
"""

import aiohttp
import asyncio
import logging
from .rate_limiter import RateLimiter
from .utils import safe_get

logger = logging.getLogger(__name__)


class TornAPI:
    """Torn City API client."""

    def __init__(self, config):
        self.config = config
        self.base_url = config.TORN_API_BASE_URL
        self.api_key = config.TORN_API_KEY
        self.rate_limiter = RateLimiter(config.API_RATE_LIMIT,
                                        60)  # per minute
        self.session = None

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
            headers = {'User-Agent': self.config.USER_AGENT}
            self.session = aiohttp.ClientSession(timeout=timeout,
                                                 headers=headers)
        return self.session

    async def _make_request(self, endpoint, params=None):
        """Make a rate-limited API request."""
        if not self.api_key:
            logger.error("No API key configured")
            return None

        await self.rate_limiter.acquire()

        url = f"{self.base_url}/{endpoint}"

        # Add API key to parameters
        if params is None:
            params = {}
        params['key'] = self.api_key

        try:
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Check for API errors
                    if 'error' in data:
                        logger.error(f"API error: {data['error']}")
                        return None

                    return data
                else:
                    logger.error(f"HTTP error {response.status} for {url}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout for API request to {url}")
            return None
        except Exception as e:
            logger.error(f"Error making API request to {url}: {e}")
            return None

    async def get_user_profile(self, user_id):
        """Get user profile information."""
        try:
            data = await self._make_request(f"user/{user_id}",
                                            {'selections': 'basic,profile'})
            return data
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return None

    async def get_faction_info(self, faction_id):
        """Get basic faction information."""
        try:
            data = await self._make_request(f"faction/{faction_id}",
                                            {'selections': 'basic'})
            return data
        except Exception as e:
            logger.error(f"Error getting faction info for {faction_id}: {e}")
            return None

    async def get_faction_members(self, faction_id):
        """Get faction members information."""
        try:
            data = await self._make_request(f"faction/{faction_id}",
                                            {'selections': 'members'})
            return data.get('members', {}) if data else {}
        except Exception as e:
            logger.error(
                f"Error getting faction members for {faction_id}: {e}")
            return {}

    async def get_item_info(self, item_id):
        """Get item information by ID."""
        try:
            data = await self._make_request("torn", {'selections': 'items'})
            return safe_get(data, 'items', {}).get(str(item_id), {})
        except Exception as e:
            logger.error(f"Error getting item info for {item_id}: {e}")
            return None

    async def get_item_market(self, item_id):
        """Get item market information by ID using itemmarket endpoint."""
        try:
            # Use the direct itemmarket endpoint
            data = await self._make_request("itemmarket", {})

            if data and isinstance(data, dict):
                # Handle different response structures for itemmarket
                market_items = data.get('itemmarket', data)
                if isinstance(market_items, list):
                    item_listings = []
                    for item in market_items:
                        if isinstance(item, dict):
                            # Check different possible ID fields
                            item_market_id = (item.get('item_id')
                                              or item.get('ID')
                                              or item.get('itemID'))
                            if item_market_id == item_id:
                                item_listings.append(item)

                    if item_listings:
                        logger.info(
                            f"Found {len(item_listings)} itemmarket listings for item {item_id}"
                        )
                        return item_listings

            # Try bazaar as fallback if itemmarket doesn't work
            data = await self._make_request("market", {'selections': 'bazaar'})

            if data and 'bazaar' in data:
                bazaar_items = data.get('bazaar', [])
                item_listings = []
                for item in bazaar_items:
                    if isinstance(item, dict) and item.get('ID') == item_id:
                        item_listings.append(item)

                if item_listings:
                    logger.info(
                        f"Found {len(item_listings)} bazaar listings for item {item_id}"
                    )
                    return item_listings

            logger.info(f"No market data found for item {item_id}")
            return []

        except Exception as e:
            logger.error(f"Error getting item market for {item_id}: {e}")
            return []

    async def get_player_bazaar(self, player_id):
        """Get bazaar items for a specific player by their ID."""
        try:
            data = await self._make_request(f"user/{player_id}",
                                            {'selections': 'bazaar'})

            if data and 'bazaar' in data:
                bazaar_items = data.get('bazaar', [])
                logger.info(
                    f"Found {len(bazaar_items)} bazaar items for player {player_id}"
                )

                # Debug: Log the structure of the first item to understand the API response (remove after testing)
                # if bazaar_items and len(bazaar_items) > 0:
                #     sample_item = bazaar_items[0]
                #     logger.info(f"Sample bazaar item structure: {sample_item}")
                #     if isinstance(sample_item, dict):
                #         logger.info(f"Available fields: {list(sample_item.keys())}")

                return bazaar_items

            logger.info(f"No bazaar data found for player {player_id}")
            return []

        except Exception as e:
            logger.error(f"Error getting bazaar for player {player_id}: {e}")
            return []

    async def close(self):
        """Close the API client session."""
        if self.session and not self.session.closed:
            await self.session.close()
