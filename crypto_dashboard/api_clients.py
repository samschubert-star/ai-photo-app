"""
API clients for crypto data sources.
"""
import time
import requests
from datetime import datetime, timedelta
from typing import Optional
import database as db


class CoinGeckoClient:
    """Client for CoinGecko API (free tier)."""

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()
        self.last_request = 0
        self.min_interval = 1.5  # Rate limit: ~30 calls/min for free tier

    def _request(self, endpoint: str, params: dict = None) -> dict:
        """Make a rate-limited request to CoinGecko."""
        # Rate limiting
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params, timeout=30)
        self.last_request = time.time()

        if response.status_code == 429:
            # Rate limited, wait and retry
            time.sleep(60)
            return self._request(endpoint, params)

        response.raise_for_status()
        return response.json()

    def get_coin_list(self) -> list:
        """Get list of all supported coins."""
        return self._request("/coins/list")

    def search_coins(self, query: str) -> list:
        """Search for coins by name or symbol."""
        data = self._request("/search", {"query": query})
        return data.get("coins", [])

    def get_coin_info(self, coin_id: str) -> dict:
        """Get detailed info about a coin."""
        return self._request(f"/coins/{coin_id}", {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        })

    def get_market_chart(self, coin_id: str, days: int = 365, vs_currency: str = "usd") -> dict:
        """
        Get historical market data.
        days: 1, 7, 14, 30, 90, 180, 365, or 'max'
        """
        return self._request(f"/coins/{coin_id}/market_chart", {
            "vs_currency": vs_currency,
            "days": days,
            "interval": "daily" if days > 90 else None
        })

    def get_market_chart_range(self, coin_id: str, from_ts: int, to_ts: int,
                                vs_currency: str = "usd") -> dict:
        """Get historical market data for a specific date range."""
        return self._request(f"/coins/{coin_id}/market_chart/range", {
            "vs_currency": vs_currency,
            "from": from_ts,
            "to": to_ts
        })

    def get_top_coins(self, limit: int = 100, vs_currency: str = "usd") -> list:
        """Get top coins by market cap."""
        return self._request("/coins/markets", {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false"
        })

    def fetch_and_store_prices(self, coin_id: str, days: int = 365) -> bool:
        """Fetch price data and store in database."""
        try:
            # Get coin info first
            info = self.get_coin_info(coin_id)
            symbol = info.get("symbol", "").upper()
            name = info.get("name", coin_id)

            # Get market chart
            chart = self.get_market_chart(coin_id, days)
            prices = chart.get("prices", [])

            if prices:
                db.save_prices(coin_id, symbol, name, prices)
                return True
            return False
        except Exception as e:
            print(f"Error fetching {coin_id}: {e}")
            return False


class DeFiLlamaClient:
    """Client for DeFiLlama API (free, no rate limits)."""

    BASE_URL = "https://api.llama.fi"
    COINS_URL = "https://coins.llama.fi"

    def __init__(self):
        self.session = requests.Session()

    def _request(self, url: str, params: dict = None) -> dict:
        """Make a request to DeFiLlama."""
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_protocols(self) -> list:
        """Get list of all DeFi protocols."""
        return self._request(f"{self.BASE_URL}/protocols")

    def get_protocol(self, protocol_slug: str) -> dict:
        """Get detailed info about a protocol including TVL history."""
        return self._request(f"{self.BASE_URL}/protocol/{protocol_slug}")

    def get_tvl_history(self, protocol_slug: str) -> list:
        """Get TVL history for a protocol."""
        data = self.get_protocol(protocol_slug)
        return data.get("tvl", [])

    def get_chains(self) -> list:
        """Get list of all chains with current TVL."""
        return self._request(f"{self.BASE_URL}/v2/chains")

    def get_chain_tvl(self, chain: str) -> list:
        """Get historical TVL for a chain."""
        return self._request(f"{self.BASE_URL}/v2/historicalChainTvl/{chain}")

    def get_total_tvl(self) -> list:
        """Get total DeFi TVL history across all chains."""
        return self._request(f"{self.BASE_URL}/v2/historicalChainTvl")

    def get_stablecoins(self) -> list:
        """Get list of stablecoins with market cap data."""
        data = self._request(f"{self.BASE_URL}/stablecoins")
        return data.get("peggedAssets", [])

    def get_stablecoin_history(self, stablecoin_id: int) -> dict:
        """Get historical data for a stablecoin."""
        return self._request(f"{self.BASE_URL}/stablecoin/{stablecoin_id}")

    def get_yields(self) -> dict:
        """Get yield/APY data for DeFi pools."""
        return self._request(f"{self.BASE_URL}/pools")

    def get_dex_volumes(self) -> dict:
        """Get DEX trading volumes."""
        return self._request(f"{self.BASE_URL}/overview/dexs")

    def search_protocols(self, query: str) -> list:
        """Search protocols by name."""
        protocols = self.get_protocols()
        query_lower = query.lower()
        return [p for p in protocols if query_lower in p.get("name", "").lower()
                or query_lower in p.get("slug", "").lower()]

    def fetch_and_store_protocol_tvl(self, protocol_slug: str) -> bool:
        """Fetch protocol TVL and store in database."""
        try:
            data = self.get_protocol(protocol_slug)
            tvl_history = data.get("tvl", [])
            name = data.get("name", protocol_slug)

            if tvl_history:
                db.save_tvl(protocol_slug, name, tvl_history)
                return True
            return False
        except Exception as e:
            print(f"Error fetching protocol {protocol_slug}: {e}")
            return False

    def fetch_and_store_chain_tvl(self, chain: str) -> bool:
        """Fetch chain TVL and store in database."""
        try:
            tvl_history = self.get_chain_tvl(chain)

            if tvl_history:
                db.save_chain_tvl(chain, tvl_history)
                return True
            return False
        except Exception as e:
            print(f"Error fetching chain {chain}: {e}")
            return False


# Convenience instances
coingecko = CoinGeckoClient()
defillama = DeFiLlamaClient()


def fetch_popular_data():
    """Fetch data for popular coins and protocols."""
    print("Fetching popular crypto data...")

    # Popular coins
    popular_coins = ["bitcoin", "ethereum", "solana", "cardano", "polkadot",
                     "avalanche-2", "chainlink", "uniswap", "aave", "maker"]

    for coin in popular_coins:
        print(f"  Fetching {coin}...")
        coingecko.fetch_and_store_prices(coin, days=365)

    # Popular protocols
    popular_protocols = ["lido", "aave", "uniswap", "makerdao", "curve-dex",
                         "compound", "eigenlayer", "rocket-pool"]

    for protocol in popular_protocols:
        print(f"  Fetching {protocol} TVL...")
        defillama.fetch_and_store_protocol_tvl(protocol)

    # Popular chains
    popular_chains = ["Ethereum", "Solana", "Arbitrum", "Optimism", "Base", "Polygon"]

    for chain in popular_chains:
        print(f"  Fetching {chain} chain TVL...")
        defillama.fetch_and_store_chain_tvl(chain)

    print("Done fetching popular data!")


if __name__ == "__main__":
    fetch_popular_data()
