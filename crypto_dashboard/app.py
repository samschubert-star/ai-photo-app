"""
Crypto Data Dashboard - Streamlit App
A simple dashboard for crypto data with AI-powered chart generation.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

import database as db
import api_clients as api
import chart_generator as charts

# Try to import anthropic for AI features
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


st.set_page_config(
    page_title="Crypto Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_chart" not in st.session_state:
        st.session_state.current_chart = None


def get_available_data_summary() -> str:
    """Get a summary of available data for the AI."""
    coins = db.get_available_coins()
    protocols = db.get_available_protocols()
    chains = db.get_available_chains()

    summary = "Available data in database:\n"
    summary += f"\nCoins ({len(coins)}): " + ", ".join([f"{c['symbol']} ({c['coin_id']})" for c in coins[:20]])
    if len(coins) > 20:
        summary += f"... and {len(coins) - 20} more"

    summary += f"\n\nProtocols ({len(protocols)}): " + ", ".join([f"{p['name']} ({p['protocol_id']})" for p in protocols[:20]])
    if len(protocols) > 20:
        summary += f"... and {len(protocols) - 20} more"

    summary += f"\n\nChains ({len(chains)}): " + ", ".join(chains[:20])
    if len(chains) > 20:
        summary += f"... and {len(chains) - 20} more"

    return summary


def generate_chart_from_prompt(prompt: str) -> dict:
    """
    Use Claude to interpret the prompt and generate chart parameters.
    Returns a dict with chart_type and parameters.
    """
    if not ANTHROPIC_AVAILABLE:
        return {"error": "Anthropic library not installed. Please install it with: pip install anthropic"}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY environment variable not set"}

    client = anthropic.Anthropic(api_key=api_key)

    data_summary = get_available_data_summary()

    system_prompt = f"""You are a crypto data visualization assistant. Your job is to interpret user requests and generate chart specifications.

{data_summary}

Available chart types and their parameters:

1. price_chart: Compare coin prices
   - coin_ids: list of CoinGecko coin IDs (e.g., ["bitcoin", "ethereum"])
   - days: number of days (default 365)
   - normalize: boolean - if true, index all to start at 100 for comparison

2. tvl_chart: Compare protocol or chain TVL
   - protocol_ids: list of DeFiLlama protocol slugs (e.g., ["aave", "uniswap"])
   - chains: list of chain names (e.g., ["Ethereum", "Solana"])
   - days: number of days
   - normalize: boolean

3. dual_axis_chart: Compare different metrics on two Y-axes
   - left_data: list of [id, type, label] where type is "price", "tvl", or "chain_tvl"
   - right_data: list of [id, type, label]
   - days: number of days
   - normalize: boolean (recommended true for different scales)

4. correlation_chart: Show correlation between coin prices
   - coin_ids: list of CoinGecko coin IDs
   - days: number of days

5. drawdown_chart: Show drawdown from peak
   - coin_ids: list of CoinGecko coin IDs
   - days: number of days

6. volatility_chart: Show rolling volatility
   - coin_ids: list of CoinGecko coin IDs
   - days: number of days
   - window: rolling window in days (default 30)

7. area_chart: Stacked or overlapping area chart
   - items: list of [id, type] where type is "price", "tvl", or "chain_tvl"
   - days: number of days
   - stacked: boolean

Respond with a JSON object containing:
- chart_type: one of the above chart types
- params: object with the parameters for that chart type
- title: a descriptive title for the chart
- explanation: brief explanation of what the chart shows

If the user asks for data you don't have, suggest fetching it first.
If the request is unclear, ask for clarification.

IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Try to parse JSON from response
        try:
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"error": f"Failed to parse AI response: {response_text[:200]}"}

    except Exception as e:
        return {"error": f"AI error: {str(e)}"}


def execute_chart_spec(spec: dict):
    """Execute a chart specification and return a Plotly figure."""
    if "error" in spec:
        return None, spec["error"]

    chart_type = spec.get("chart_type")
    params = spec.get("params", {})
    title = spec.get("title")

    try:
        if chart_type == "price_chart":
            fig = charts.create_price_chart(
                coin_ids=params.get("coin_ids", []),
                days=params.get("days", 365),
                normalize=params.get("normalize", False),
                title=title
            )
        elif chart_type == "tvl_chart":
            fig = charts.create_tvl_chart(
                protocol_ids=params.get("protocol_ids"),
                chains=params.get("chains"),
                days=params.get("days", 365),
                normalize=params.get("normalize", False),
                title=title
            )
        elif chart_type == "dual_axis_chart":
            left_data = [tuple(x) for x in params.get("left_data", [])]
            right_data = [tuple(x) for x in params.get("right_data", [])]
            fig = charts.create_dual_axis_chart(
                left_data=left_data,
                right_data=right_data,
                days=params.get("days", 365),
                normalize=params.get("normalize", True),
                title=title
            )
        elif chart_type == "correlation_chart":
            fig = charts.create_correlation_heatmap(
                coin_ids=params.get("coin_ids", []),
                days=params.get("days", 365)
            )
        elif chart_type == "drawdown_chart":
            fig = charts.create_drawdown_chart(
                coin_ids=params.get("coin_ids", []),
                days=params.get("days", 365),
                title=title
            )
        elif chart_type == "volatility_chart":
            fig = charts.create_volatility_chart(
                coin_ids=params.get("coin_ids", []),
                days=params.get("days", 365),
                window=params.get("window", 30),
                title=title
            )
        elif chart_type == "area_chart":
            items = [tuple(x) for x in params.get("items", [])]
            fig = charts.create_area_chart(
                items=items,
                days=params.get("days", 365),
                stacked=params.get("stacked", True),
                title=title
            )
        else:
            return None, f"Unknown chart type: {chart_type}"

        return fig, spec.get("explanation", "")

    except Exception as e:
        return None, f"Error creating chart: {str(e)}"


def render_sidebar():
    """Render the sidebar with data management options."""
    with st.sidebar:
        st.title("📊 Crypto Dashboard")
        st.markdown("---")

        # Data Management Section
        st.subheader("📥 Data Management")

        # Quick fetch popular data
        if st.button("🚀 Fetch Popular Data", use_container_width=True):
            with st.spinner("Fetching popular crypto data..."):
                api.fetch_popular_data()
            st.success("Done! Popular data fetched.")
            st.rerun()

        st.markdown("---")

        # Fetch specific coin
        st.subheader("Add Coin Data")
        coin_search = st.text_input("Search coin (e.g., bitcoin, eth)")
        if coin_search:
            with st.spinner("Searching..."):
                results = api.coingecko.search_coins(coin_search)
            if results:
                selected = st.selectbox(
                    "Select coin",
                    options=results[:10],
                    format_func=lambda x: f"{x['name']} ({x['symbol'].upper()})"
                )
                days = st.slider("Days of history", 30, 365, 365)
                if st.button("Fetch Coin Data"):
                    with st.spinner(f"Fetching {selected['name']}..."):
                        api.coingecko.fetch_and_store_prices(selected["id"], days)
                    st.success(f"Fetched {selected['name']}")
                    st.rerun()

        st.markdown("---")

        # Fetch specific protocol
        st.subheader("Add Protocol TVL")
        protocol_search = st.text_input("Search protocol (e.g., aave, uniswap)")
        if protocol_search:
            with st.spinner("Searching..."):
                results = api.defillama.search_protocols(protocol_search)
            if results:
                selected = st.selectbox(
                    "Select protocol",
                    options=results[:10],
                    format_func=lambda x: f"{x['name']} (TVL: ${x.get('tvl', 0):,.0f})"
                )
                if st.button("Fetch Protocol TVL"):
                    with st.spinner(f"Fetching {selected['name']} TVL..."):
                        api.defillama.fetch_and_store_protocol_tvl(selected["slug"])
                    st.success(f"Fetched {selected['name']} TVL")
                    st.rerun()

        st.markdown("---")

        # Fetch chain TVL
        st.subheader("Add Chain TVL")
        chain_input = st.text_input("Chain name (e.g., Ethereum, Solana)")
        if chain_input and st.button("Fetch Chain TVL"):
            with st.spinner(f"Fetching {chain_input} TVL..."):
                api.defillama.fetch_and_store_chain_tvl(chain_input)
            st.success(f"Fetched {chain_input} TVL")
            st.rerun()

        st.markdown("---")

        # Show available data
        st.subheader("📦 Available Data")
        coins = db.get_available_coins()
        protocols = db.get_available_protocols()
        chains = db.get_available_chains()

        st.metric("Coins", len(coins))
        st.metric("Protocols", len(protocols))
        st.metric("Chains", len(chains))

        with st.expander("View coins"):
            for c in coins:
                st.write(f"• {c['symbol']} - {c['name']}")

        with st.expander("View protocols"):
            for p in protocols:
                st.write(f"• {p['name']}")

        with st.expander("View chains"):
            for c in chains:
                st.write(f"• {c}")


def render_quick_charts():
    """Render quick chart generation options."""
    st.subheader("⚡ Quick Charts")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Price Comparison**")
        coins = db.get_available_coins()
        if coins:
            selected_coins = st.multiselect(
                "Select coins",
                options=[c["coin_id"] for c in coins],
                format_func=lambda x: next((c["symbol"] for c in coins if c["coin_id"] == x), x),
                key="quick_price_coins"
            )
            normalize = st.checkbox("Normalize (index to 100)", value=True, key="quick_price_norm")
            days = st.selectbox("Time period", [30, 90, 180, 365], index=3, key="quick_price_days")

            if st.button("Generate Price Chart", key="quick_price_btn") and selected_coins:
                fig = charts.create_price_chart(selected_coins, days, normalize)
                st.session_state.current_chart = fig

    with col2:
        st.markdown("**TVL Comparison**")
        protocols = db.get_available_protocols()
        chains = db.get_available_chains()

        selected_protocols = st.multiselect(
            "Select protocols",
            options=[p["protocol_id"] for p in protocols],
            format_func=lambda x: next((p["name"] for p in protocols if p["protocol_id"] == x), x),
            key="quick_tvl_protocols"
        )
        selected_chains = st.multiselect(
            "Select chains",
            options=chains,
            key="quick_tvl_chains"
        )
        normalize_tvl = st.checkbox("Normalize", value=True, key="quick_tvl_norm")
        days_tvl = st.selectbox("Time period", [30, 90, 180, 365], index=3, key="quick_tvl_days")

        if st.button("Generate TVL Chart", key="quick_tvl_btn") and (selected_protocols or selected_chains):
            fig = charts.create_tvl_chart(
                protocol_ids=selected_protocols if selected_protocols else None,
                chains=selected_chains if selected_chains else None,
                days=days_tvl,
                normalize=normalize_tvl
            )
            st.session_state.current_chart = fig

    with col3:
        st.markdown("**Analysis Charts**")
        coins_analysis = db.get_available_coins()
        if coins_analysis:
            analysis_coins = st.multiselect(
                "Select coins for analysis",
                options=[c["coin_id"] for c in coins_analysis],
                format_func=lambda x: next((c["symbol"] for c in coins_analysis if c["coin_id"] == x), x),
                key="analysis_coins"
            )
            chart_type = st.selectbox(
                "Chart type",
                ["Correlation Heatmap", "Drawdown", "Volatility"],
                key="analysis_type"
            )
            days_analysis = st.selectbox("Time period", [30, 90, 180, 365], index=3, key="analysis_days")

            if st.button("Generate Analysis", key="analysis_btn") and analysis_coins:
                if chart_type == "Correlation Heatmap":
                    fig = charts.create_correlation_heatmap(analysis_coins, days_analysis)
                elif chart_type == "Drawdown":
                    fig = charts.create_drawdown_chart(analysis_coins, days_analysis)
                else:
                    fig = charts.create_volatility_chart(analysis_coins, days_analysis)
                st.session_state.current_chart = fig


def render_ai_chat():
    """Render the AI chat interface for chart generation."""
    st.subheader("🤖 AI Chart Assistant")

    if not ANTHROPIC_AVAILABLE:
        st.warning("Install `anthropic` package to enable AI features: `pip install anthropic`")
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("Set `ANTHROPIC_API_KEY` environment variable to enable AI features")
        return

    st.markdown("""
    Ask me to create any chart! Examples:
    - "Compare Bitcoin and Ethereum prices over the last year, normalized"
    - "Show me the TVL of Aave vs Uniswap"
    - "Create a dual-axis chart with ETH price and Ethereum chain TVL"
    - "Show correlation between BTC, ETH, and SOL"
    - "What's the drawdown for Bitcoin this year?"
    """)

    # Chat input
    prompt = st.text_input("What chart would you like?", key="ai_prompt")

    if st.button("Generate Chart", key="ai_generate") and prompt:
        with st.spinner("🤔 Thinking..."):
            spec = generate_chart_from_prompt(prompt)

        if "error" in spec:
            st.error(spec["error"])
        else:
            st.json(spec)  # Show what the AI understood

            fig, explanation = execute_chart_spec(spec)
            if fig:
                st.session_state.current_chart = fig
                if explanation:
                    st.info(explanation)
            else:
                st.error(explanation)


def render_chart_display():
    """Render the current chart."""
    st.subheader("📈 Chart")

    if st.session_state.current_chart:
        st.plotly_chart(st.session_state.current_chart, use_container_width=True)
    else:
        st.info("Generate a chart using the options above or ask the AI assistant!")


def main():
    """Main application."""
    init_session_state()

    render_sidebar()

    # Main content
    st.title("Crypto Data Dashboard")
    st.markdown("Visualize crypto prices, TVL, and more with AI-powered chart generation.")

    # Check if we have any data
    coins = db.get_available_coins()
    protocols = db.get_available_protocols()

    if not coins and not protocols:
        st.warning("👋 Welcome! You don't have any data yet. Click **Fetch Popular Data** in the sidebar to get started!")

    # Tabs for different features
    tab1, tab2, tab3 = st.tabs(["⚡ Quick Charts", "🤖 AI Assistant", "📈 Current Chart"])

    with tab1:
        render_quick_charts()

    with tab2:
        render_ai_chat()

    with tab3:
        render_chart_display()


if __name__ == "__main__":
    main()
