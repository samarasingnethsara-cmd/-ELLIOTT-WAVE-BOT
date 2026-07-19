
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import hashlib
from shheets_db import fetch_data

# --- App එකෙහි මූලික සැකසුම් ---
st.set_page_config(page_title="EagleEye AI Advanced Trading Bot", layout="wide", initial_sidebar_state="expanded")
st.title("🦅 EagleEye AI Institutional Bot (SMC + ICT + Elliott Wave + RSI)")
st.write("Professional Algorithmic Signal Engine with Advanced Smart Money Concept Logic")

# --- Google Sheet Link ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1FXFhTbaM7wAGJdpnQj3O_UNkFTEGHtHoYmPMDg-x4OA/edit?usp=sharing"

# Browser Security Fingerprint
if "user_device_token" not in st.session_state:
    ua_string = str(st.context.headers.get("User-Agent", "UnknownBrowser"))
    ip_approx = str(st.context.headers.get("X-Forwarded-For", "Local"))
    secret_hash = hashlib.sha256((ua_string + ip_approx).encode()).hexdigest()[:12]
    st.session_state.user_device_token = secret_hash

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False
if "active_code" not in st.session_state:
    st.session_state.active_code = ""

@st.cache_resource
def get_cloud_device_registry():
    return {}

device_registry = get_cloud_device_registry()

if st.session_state.active_code:
    st.session_state.is_premium = True

# --- Sidebar Controls ---
st.sidebar.header("🛠️ Strategy Control Panel")

if st.session_state.is_premium:
    st.sidebar.success(f"👑 Premium Account (SMC Subscribed)")
else:
    st.sidebar.warning("🆓 Free Account (BTC 1D Only)")

# Free vs Premium Controls
if st.session_state.is_premium:
    market_type = st.sidebar.radio("Market Type", ["Crypto", "Forex"])
    if market_type == "Crypto":
        ticker_list = {
            "Bitcoin (BTC/USD)": "BTC-USD", "Ethereum (ETH/USD)": "ETH-USD",
            "Solana (SOL/USD)": "SOL-USD", "Ripple (XRP/USD)": "XRP-USD"
        }
    else:
        ticker_list = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X"}
    
    selected_display_name = st.sidebar.selectbox("Asset Ticker", list(ticker_list.keys()))
    ticker = ticker_list[selected_display_name]
    timeframe = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h", "1d"])
    period = st.sidebar.selectbox("Data Period", ["1mo", "3mo", "6mo"])
else:
    ticker = "BTC-USD"
    timeframe = "1d"
    period = "6mo"
    st.sidebar.info("🔒 Premium unlocked for BTC-USD on 1D Chart only.")

# Money Management Setup
balance = 1000.0
risk_pct = 1.0
if st.session_state.is_premium:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Smart Risk Planner")
    balance = st.sidebar.number_input("Account Balance ($)", min_value=1.0, value=1000.0)
    risk_pct = st.sidebar.slider("Risk Per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

st.sidebar.markdown("---")

# Premium Activation System
if not st.session_state.is_premium:
    st.sidebar.subheader("🔑 Unlock SMC/ICT Premium")
    input_code = st.sidebar.text_input("Enter Activation Code", type="password")
    if st.sidebar.button("Verify Code"):
        db = fetch_data(GOOGLE_SHEET_URL)
        if not db.empty and input_code in db['code'].values:
            current_token = st.session_state.user_device_token
            if input_code not in device_registry:
                device_registry[input_code] = []
            
            if len(device_registry[input_code]) >= 2 and current_token not in device_registry[input_code]:
                st.sidebar.error("❌ Max Limit Reached! (2 Devices Limit)")
            else:
                if current_token not in device_registry[input_code]:
                    device_registry[input_code].append(current_token)
                st.session_state.is_premium = True
                st.session_state.active_code = input_code
                st.rerun()
        else:
            st.sidebar.error("❌ Invalid Cloud Code!")

start_bot = st.sidebar.button("🚀 Run Advanced AI Engine", use_container_width=True)

@st.cache_data(ttl=60)
def load_market_data(symbol, tf, pd_val):
    return yf.download(symbol, period=pd_val, interval=tf, group_by='column')

if start_bot:
    with st.spinner("Analyzing SMC Blocks & Elliott Waves..."):
        try:
            df = load_market_data(ticker, timeframe, period)
            df.columns = df.columns.get_level_values(0) if isinstance(df.columns, pd.MultiIndex) else df.columns
            df.reset_index(inplace=True)

            # 1. RSI Indicator Logic (Period 14)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            current_rsi = float(df['RSI'].values[-1])

            # 2. SMC/ICT Order Block Logic
            df['Bullish_OB'] = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Volume'] > df['Volume'].rolling(20).mean())
            df['Bearish_OB'] = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Volume'] > df['Volume'].rolling(20).mean())

            # 3. Enhanced Elliott Wave Engine
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

            last_close = float(df['Close'].values[-1])
            last_low = float(df['Low'].iloc[-10:-1].min())
            last_high = float(df['High'].iloc[-10:-1].max())

            # Mathematical Logic Fusion (SMC + RSI + Wave 3 Confirmation)
            is_bullish_ob = df['Bullish_OB'].iloc[-5:].any()
            is_bearish_ob = df['Bearish_OB'].iloc[-5:].any()

            if last_close > df['EMA_50'].values[-1] and current_rsi < 65 and is_bullish_ob:
                signal_text = "🟢 STRONG BUY (SMC Order Block + Wave 3 Confirmation)"
                entry_price = round(last_close, 2)
                stop_loss = round(last_low, 2)
                risk = entry_price - stop_loss
                take_profit = round(entry_price + (risk * 2.5), 2) # Risk to Reward 1:2.5
            elif last_close < df['EMA_50'].values[-1] and current_rsi > 35 and is_bearish_ob:
                signal_text = "🔴 STRONG SELL (SMC Mitigation + Wave C Breakdown)"
                entry_price = round(last_close, 2)
                stop_loss = round(last_high, 2)
                risk = stop_loss - entry_price
                take_profit = round(entry_price - (risk * 2.5), 2)
            else:
                # Fallback Strategy if SMC is not forming
                if current_rsi < 30:
                    signal_text = "🟡 WEAK BUY (Oversold RSI Reversal)"
                    entry_price = round(last_close, 2)
                    stop_loss = round(last_low * 0.99, 2)
                    take_profit = round(entry_price * 1.02, 2)
                elif current_rsi > 70:
                    signal_text = "🟡 WEAK SELL (Overbought RSI Correction)"
                    entry_price = round(last_close, 2)
                    stop_loss = round(last_high * 1.01, 2)
                    take_profit = round(entry_price * 0.98, 2)
                else:
                    signal_text = "⚪ HOLD (Market Consolidation - No SMC Setup)"
                    entry_price, stop_loss, take_profit = last_close, last_close, last_close

            # Past Performance Engine
            past_close = float(df['Close'].values[-7])
            past_rsi = float(df['RSI'].values[-7])
            past_signal = "BUY" if past_rsi < 50 else "SELL"
            
            highest_since = float(df['High'].iloc[-6:].max())
            lowest_since = float(df['Low'].iloc[-6:].min())

            if past_signal == "BUY":
                status = "🏆 WIN" if highest_since >= (past_close * 1.02) else ("❌ LOSS" if lowest_since <= (past_close * 0.99) else "⏳ PENDING")
            else:
                status = "🏆 WIN" if lowest_since <= (past_close * 0.98) else ("❌ LOSS" if highest_since >= (past_close * 1.01) else "⏳ PENDING")

            # Dashboard View Layout
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("📡 Smart Signal Matrix")
                st.info(f"**Engine Result:** {signal_text}")
                st.metric(label="Current RSI (14)", value=f"{current_rsi:.2f}")
                
                if "HOLD" not in signal_text:
                    st.metric(label="Entry Target", value=f"${entry_price:,}")
                    st.metric(label="Stop Loss (SL)", value=f"${stop_loss:,}")
                    st.metric(label="Take Profit (TP)", value=f"${take_profit:,}")

                # Performance Panel
                st.markdown("---")
                st.subheader("📜 System Backtest Tracker")
                if "WIN" in status: st.success(f"Last Tracked Setup: {status}")
                elif "LOSS" in status: st.error(f"Last Tracked Setup: {status}")
                else: st.warning(f"Last Tracked Setup: {status}")

                # Money Management Calculation
                if st.session_state.is_premium and "HOLD" not in signal_text:
                    st.markdown("---")
                    st.subheader("🛡️ Lot Size / Position Calibrator")
                    risk_dollars = balance * (risk_pct / 100)
                    price_risk = abs(entry_price - stop_loss)
                    if price_risk > 0:
                        pos_size = risk_dollars / price_risk
                        st.success(f"**Optimal Trade Size:** {pos_size:.4f} Units")
                        st.write(f"💼 Risk Allocation: ${risk_dollars:.2f} | Target Reward: ${risk_dollars * 2.5:.2f}")

            with col2:
                st.subheader("📊 SMC Order Block & Multi-EMA Chart")
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price")])
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='cyan', width=1.5), name="EMA 50 (Trend)"))
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='magenta', width=1.5), name="EMA 200 (Baseline)"))
                
                if "HOLD" not in signal_text:
                    fig.add_hline(y=entry_price, line_dash="dash", line_color="green", annotation_text="Entry")
                    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", annotation_text="SL")
                    fig.add_hline(y=take_profit, line_dash="dash", line_color="gold", annotation_text="TP")
                
                fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Data Fetching Error: {e}")
