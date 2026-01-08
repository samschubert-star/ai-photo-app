"""
Chart generation for crypto data visualization.
Uses Plotly for interactive charts.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import database as db


# Color palette for charts
COLORS = [
    "#636EFA",  # Blue
    "#EF553B",  # Red
    "#00CC96",  # Green
    "#AB63FA",  # Purple
    "#FFA15A",  # Orange
    "#19D3F3",  # Cyan
    "#FF6692",  # Pink
    "#B6E880",  # Light Green
    "#FF97FF",  # Magenta
    "#FECB52",  # Yellow
]

# Chart theme
CHART_TEMPLATE = "plotly_dark"


def normalize_series(df: pd.DataFrame, value_col: str, date_col: str = "date") -> pd.DataFrame:
    """
    Normalize a series so it starts at 100 (indexed).
    This allows comparing assets with different price scales.
    """
    df = df.copy()
    df = df.sort_values(date_col)
    first_value = df[value_col].iloc[0]
    if first_value != 0:
        df[f"{value_col}_indexed"] = (df[value_col] / first_value) * 100
    else:
        df[f"{value_col}_indexed"] = 0
    return df


def align_dataframes(dfs: List[pd.DataFrame], date_col: str = "date") -> List[pd.DataFrame]:
    """
    Align multiple dataframes to start from the same date.
    Returns dataframes trimmed to their common date range.
    """
    if not dfs:
        return dfs

    # Find common date range
    min_dates = [df[date_col].min() for df in dfs if not df.empty]
    max_dates = [df[date_col].max() for df in dfs if not df.empty]

    if not min_dates:
        return dfs

    common_start = max(min_dates)
    common_end = min(max_dates)

    # Filter each dataframe
    aligned = []
    for df in dfs:
        filtered = df[(df[date_col] >= common_start) & (df[date_col] <= common_end)]
        aligned.append(filtered)

    return aligned


def create_price_chart(
    coin_ids: List[str],
    days: int = 365,
    normalize: bool = False,
    title: str = None
) -> go.Figure:
    """
    Create a price chart for one or more coins.

    Args:
        coin_ids: List of CoinGecko coin IDs
        days: Number of days of history
        normalize: If True, index all series to start at 100
        title: Custom chart title
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    fig = go.Figure()

    dfs = []
    labels = []

    for coin_id in coin_ids:
        df = db.get_prices(coin_id, start_date, end_date)
        if not df.empty:
            dfs.append(df)
            labels.append(f"{df['name'].iloc[0]} ({df['symbol'].iloc[0]})")

    if normalize and len(dfs) > 1:
        dfs = align_dataframes(dfs)
        for i, df in enumerate(dfs):
            dfs[i] = normalize_series(df, "price_usd")

    for i, (df, label) in enumerate(zip(dfs, labels)):
        value_col = "price_usd_indexed" if normalize else "price_usd"
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df[value_col],
            name=label,
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            hovertemplate=f"{label}<br>%{{x|%Y-%m-%d}}<br>%{{y:,.2f}}<extra></extra>"
        ))

    y_title = "Indexed (Start = 100)" if normalize else "Price (USD)"
    chart_title = title or f"{'Indexed ' if normalize else ''}Price Comparison"

    fig.update_layout(
        title=chart_title,
        xaxis_title="Date",
        yaxis_title=y_title,
        template=CHART_TEMPLATE,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_tvl_chart(
    protocol_ids: List[str] = None,
    chains: List[str] = None,
    days: int = 365,
    normalize: bool = False,
    title: str = None
) -> go.Figure:
    """
    Create a TVL chart for protocols or chains.

    Args:
        protocol_ids: List of DeFiLlama protocol slugs
        chains: List of chain names
        days: Number of days of history
        normalize: If True, index all series to start at 100
        title: Custom chart title
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    fig = go.Figure()

    dfs = []
    labels = []

    # Get protocol TVL data
    if protocol_ids:
        for protocol_id in protocol_ids:
            df = db.get_tvl(protocol_id, start_date, end_date)
            if not df.empty:
                dfs.append(df)
                labels.append(df["protocol_name"].iloc[0])

    # Get chain TVL data
    if chains:
        for chain in chains:
            df = db.get_chain_tvl(chain, start_date, end_date)
            if not df.empty:
                # Rename column to match protocol structure
                df["tvl_usd"] = df["tvl_usd"]
                dfs.append(df)
                labels.append(chain)

    if normalize and len(dfs) > 1:
        dfs = align_dataframes(dfs)
        for i, df in enumerate(dfs):
            dfs[i] = normalize_series(df, "tvl_usd")

    for i, (df, label) in enumerate(zip(dfs, labels)):
        value_col = "tvl_usd_indexed" if normalize else "tvl_usd"
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df[value_col],
            name=label,
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            fill="tonexty" if i > 0 else None,
            hovertemplate=f"{label}<br>%{{x|%Y-%m-%d}}<br>${{y:,.0f}}<extra></extra>"
        ))

    y_title = "Indexed (Start = 100)" if normalize else "TVL (USD)"
    chart_title = title or f"{'Indexed ' if normalize else ''}TVL Comparison"

    fig.update_layout(
        title=chart_title,
        xaxis_title="Date",
        yaxis_title=y_title,
        template=CHART_TEMPLATE,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_dual_axis_chart(
    left_data: List[Tuple[str, str, str]],  # [(id, type, label), ...]
    right_data: List[Tuple[str, str, str]],
    days: int = 365,
    normalize: bool = True,
    title: str = None
) -> go.Figure:
    """
    Create a chart with two Y-axes.
    type can be: 'price', 'tvl', 'chain_tvl'

    Args:
        left_data: Data for left Y-axis [(id, type, label), ...]
        right_data: Data for right Y-axis
        days: Number of days of history
        normalize: If True, index all series to start at 100 (recommended for dual axis)
        title: Custom chart title
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    def get_data(item):
        id_, type_, label = item
        if type_ == "price":
            df = db.get_prices(id_, start_date, end_date)
            value_col = "price_usd"
        elif type_ == "tvl":
            df = db.get_tvl(id_, start_date, end_date)
            value_col = "tvl_usd"
        else:  # chain_tvl
            df = db.get_chain_tvl(id_, start_date, end_date)
            value_col = "tvl_usd"
        return df, value_col, label

    all_dfs = []

    # Process left axis data
    left_processed = []
    for i, item in enumerate(left_data):
        df, value_col, label = get_data(item)
        if not df.empty:
            left_processed.append((df, value_col, label, i))
            all_dfs.append(df)

    # Process right axis data
    right_processed = []
    for i, item in enumerate(right_data):
        df, value_col, label = get_data(item)
        if not df.empty:
            right_processed.append((df, value_col, label, i + len(left_data)))
            all_dfs.append(df)

    # Align all dataframes if normalizing
    if normalize and all_dfs:
        all_dfs = align_dataframes(all_dfs)

        # Re-assign aligned dataframes
        idx = 0
        for i in range(len(left_processed)):
            df, value_col, label, color_idx = left_processed[i]
            left_processed[i] = (normalize_series(all_dfs[idx], value_col), value_col + "_indexed", label, color_idx)
            idx += 1
        for i in range(len(right_processed)):
            df, value_col, label, color_idx = right_processed[i]
            right_processed[i] = (normalize_series(all_dfs[idx], value_col), value_col + "_indexed", label, color_idx)
            idx += 1

    # Add left axis traces
    for df, value_col, label, color_idx in left_processed:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[value_col],
                name=f"{label} (L)",
                line=dict(color=COLORS[color_idx % len(COLORS)], width=2),
            ),
            secondary_y=False
        )

    # Add right axis traces
    for df, value_col, label, color_idx in right_processed:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[value_col],
                name=f"{label} (R)",
                line=dict(color=COLORS[color_idx % len(COLORS)], width=2, dash="dash"),
            ),
            secondary_y=True
        )

    y_title = "Indexed (Start = 100)" if normalize else ""
    chart_title = title or "Dual Axis Comparison"

    fig.update_layout(
        title=chart_title,
        xaxis_title="Date",
        template=CHART_TEMPLATE,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_yaxes(title_text=y_title or "Left Axis", secondary_y=False)
    fig.update_yaxes(title_text=y_title or "Right Axis", secondary_y=True)

    return fig


def create_correlation_heatmap(
    coin_ids: List[str],
    days: int = 365
) -> go.Figure:
    """
    Create a correlation heatmap between coin prices.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Get all price data
    price_data = {}
    for coin_id in coin_ids:
        df = db.get_prices(coin_id, start_date, end_date)
        if not df.empty:
            # Use daily returns for correlation
            df = df.set_index("date")
            df["returns"] = df["price_usd"].pct_change()
            label = f"{df['symbol'].iloc[0]}"
            price_data[label] = df["returns"]

    if len(price_data) < 2:
        return go.Figure().add_annotation(text="Not enough data for correlation", showarrow=False)

    # Create correlation matrix
    combined = pd.DataFrame(price_data).dropna()
    corr_matrix = combined.corr()

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale="RdBu",
        zmid=0,
        text=corr_matrix.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 12},
        hovertemplate="%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>"
    ))

    fig.update_layout(
        title="Price Return Correlation Matrix",
        template=CHART_TEMPLATE,
    )

    return fig


def create_drawdown_chart(
    coin_ids: List[str],
    days: int = 365,
    title: str = None
) -> go.Figure:
    """
    Create a drawdown chart showing decline from peak prices.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    fig = go.Figure()

    for i, coin_id in enumerate(coin_ids):
        df = db.get_prices(coin_id, start_date, end_date)
        if df.empty:
            continue

        df = df.sort_values("date")
        df["peak"] = df["price_usd"].cummax()
        df["drawdown"] = (df["price_usd"] - df["peak"]) / df["peak"] * 100

        label = f"{df['name'].iloc[0]} ({df['symbol'].iloc[0]})"

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["drawdown"],
            name=label,
            fill="tozeroy",
            line=dict(color=COLORS[i % len(COLORS)], width=1),
            hovertemplate=f"{label}<br>%{{x|%Y-%m-%d}}<br>Drawdown: %{{y:.1f}}%<extra></extra>"
        ))

    chart_title = title or "Drawdown from All-Time High"

    fig.update_layout(
        title=chart_title,
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        template=CHART_TEMPLATE,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_volatility_chart(
    coin_ids: List[str],
    days: int = 365,
    window: int = 30,
    title: str = None
) -> go.Figure:
    """
    Create a rolling volatility chart.

    Args:
        coin_ids: List of coin IDs
        days: Number of days of history
        window: Rolling window size for volatility calculation
        title: Custom chart title
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    fig = go.Figure()

    for i, coin_id in enumerate(coin_ids):
        df = db.get_prices(coin_id, start_date, end_date)
        if df.empty:
            continue

        df = df.sort_values("date")
        df["returns"] = df["price_usd"].pct_change()
        df["volatility"] = df["returns"].rolling(window=window).std() * (365 ** 0.5) * 100  # Annualized

        label = f"{df['name'].iloc[0]} ({df['symbol'].iloc[0]})"

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["volatility"],
            name=label,
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            hovertemplate=f"{label}<br>%{{x|%Y-%m-%d}}<br>Volatility: %{{y:.1f}}%<extra></extra>"
        ))

    chart_title = title or f"{window}-Day Rolling Volatility (Annualized)"

    fig.update_layout(
        title=chart_title,
        xaxis_title="Date",
        yaxis_title="Volatility (%)",
        template=CHART_TEMPLATE,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def create_market_cap_pie(limit: int = 10) -> go.Figure:
    """
    Create a pie chart of top coins by latest stored market cap.
    Note: This uses stored data, so it needs recent data fetches.
    """
    coins = db.get_available_coins()

    # Get latest price/market cap for each coin
    data = []
    for coin in coins:
        df = db.get_prices(coin["coin_id"])
        if not df.empty and "market_cap" in df.columns:
            latest = df.iloc[-1]
            if latest.get("market_cap"):
                data.append({
                    "name": coin["name"],
                    "symbol": coin["symbol"],
                    "market_cap": latest["market_cap"]
                })

    if not data:
        return go.Figure().add_annotation(text="No market cap data available", showarrow=False)

    df = pd.DataFrame(data).nlargest(limit, "market_cap")

    fig = go.Figure(data=[go.Pie(
        labels=df["symbol"],
        values=df["market_cap"],
        hole=0.4,
        textinfo="label+percent",
        hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>"
    )])

    fig.update_layout(
        title=f"Top {limit} Cryptocurrencies by Market Cap",
        template=CHART_TEMPLATE,
    )

    return fig


def create_area_chart(
    items: List[Tuple[str, str]],  # [(id, type), ...]  type: 'price', 'tvl', 'chain_tvl'
    days: int = 365,
    stacked: bool = True,
    title: str = None
) -> go.Figure:
    """
    Create a stacked or overlapping area chart.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    fig = go.Figure()

    for i, (item_id, item_type) in enumerate(items):
        if item_type == "price":
            df = db.get_prices(item_id, start_date, end_date)
            value_col = "price_usd"
            label = f"{df['name'].iloc[0]}" if not df.empty else item_id
        elif item_type == "tvl":
            df = db.get_tvl(item_id, start_date, end_date)
            value_col = "tvl_usd"
            label = df["protocol_name"].iloc[0] if not df.empty else item_id
        else:  # chain_tvl
            df = db.get_chain_tvl(item_id, start_date, end_date)
            value_col = "tvl_usd"
            label = item_id

        if df.empty:
            continue

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df[value_col],
            name=label,
            mode="lines",
            line=dict(width=0.5, color=COLORS[i % len(COLORS)]),
            fill="tonexty" if stacked else "tozeroy",
            stackgroup="one" if stacked else None,
            hovertemplate=f"{label}<br>%{{x|%Y-%m-%d}}<br>%{{y:,.0f}}<extra></extra>"
        ))

    chart_title = title or ("Stacked Area Chart" if stacked else "Area Chart")

    fig.update_layout(
        title=chart_title,
        xaxis_title="Date",
        yaxis_title="Value (USD)",
        template=CHART_TEMPLATE,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig
