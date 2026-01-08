# Crypto Data Dashboard

A Python dashboard for storing crypto data, generating charts on demand, and fetching new data via APIs (CoinGecko & DeFiLlama).

## Features

- **Data Storage**: SQLite database for storing historical crypto prices and TVL data
- **API Integration**:
  - CoinGecko for price data
  - DeFiLlama for TVL (Total Value Locked) data
- **Chart Types**:
  - Price comparison (single or multiple coins)
  - TVL comparison (protocols and chains)
  - Dual-axis charts (compare different metrics)
  - Correlation heatmaps
  - Drawdown charts
  - Volatility charts
  - Area charts (stacked or overlapping)
- **Normalized Charts**: Index multiple series to start at 100 for fair comparison
- **AI-Powered**: Ask Claude to generate charts using natural language

## Installation

```bash
cd crypto_dashboard
pip install -r requirements.txt
```

## Quick Start

1. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```

2. **Fetch some data:**
   - Click "Fetch Popular Data" in the sidebar to get data for popular coins/protocols
   - Or search and add specific coins/protocols

3. **Create charts:**
   - Use the Quick Charts tab for point-and-click chart creation
   - Or use the AI Assistant to describe what you want in natural language

## AI Features (Optional)

To enable AI-powered chart generation:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
streamlit run app.py
```

Then you can ask things like:
- "Compare Bitcoin and Ethereum prices over the last year, normalized"
- "Show me the TVL of Aave vs Uniswap"
- "Create a dual-axis chart with ETH price and Ethereum chain TVL"
- "Show correlation between BTC, ETH, and SOL"

## Project Structure

```
crypto_dashboard/
├── app.py              # Streamlit web interface
├── database.py         # SQLite database layer
├── api_clients.py      # CoinGecko & DeFiLlama API clients
├── chart_generator.py  # Plotly chart generation
├── requirements.txt    # Python dependencies
├── data/              # SQLite database storage
│   └── crypto_data.db
└── README.md
```

## API Usage

### Fetching Data Programmatically

```python
from api_clients import coingecko, defillama

# Fetch Bitcoin price history (365 days)
coingecko.fetch_and_store_prices("bitcoin", days=365)

# Fetch Aave TVL history
defillama.fetch_and_store_protocol_tvl("aave")

# Fetch Ethereum chain TVL
defillama.fetch_and_store_chain_tvl("Ethereum")
```

### Creating Charts Programmatically

```python
import chart_generator as charts

# Price comparison chart
fig = charts.create_price_chart(
    coin_ids=["bitcoin", "ethereum"],
    days=365,
    normalize=True
)
fig.show()

# Dual-axis chart (price vs TVL)
fig = charts.create_dual_axis_chart(
    left_data=[("bitcoin", "price", "BTC Price")],
    right_data=[("Ethereum", "chain_tvl", "ETH Chain TVL")],
    days=365,
    normalize=True
)
fig.show()

# Correlation heatmap
fig = charts.create_correlation_heatmap(
    coin_ids=["bitcoin", "ethereum", "solana"],
    days=365
)
fig.show()
```

### Querying Stored Data

```python
import database as db
from datetime import datetime, timedelta

# Get available data
coins = db.get_available_coins()
protocols = db.get_available_protocols()
chains = db.get_available_chains()

# Query price data
df = db.get_prices("bitcoin",
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now()
)

# Query TVL data
df = db.get_tvl("aave")
df = db.get_chain_tvl("Ethereum")
```

## Chart Types Explained

### Normalized/Indexed Charts
When comparing assets with different price scales (e.g., BTC at $40,000 vs SOL at $100), normalizing indexes all series to start at 100. This shows relative performance clearly.

### Dual-Axis Charts
Compare metrics with different scales (e.g., ETH price vs Ethereum TVL) using two Y-axes. Enable normalization for best results.

### Correlation Heatmap
Shows how daily returns of different coins move together. Values range from -1 (inverse) to +1 (perfectly correlated).

### Drawdown Chart
Shows the decline from the all-time high. Useful for understanding risk and recovery patterns.

### Volatility Chart
Shows rolling annualized volatility (standard deviation of returns). Higher values mean more price swings.

## API Rate Limits

- **CoinGecko** (free tier): ~30 requests/minute - the client handles rate limiting automatically
- **DeFiLlama**: No rate limits on their free API

## Notes

- Data is cached in SQLite, so subsequent runs don't need to re-fetch
- Use `db.needs_refresh()` to check if data is stale (default: 24 hours)
- The dashboard auto-refreshes data display when you fetch new data
