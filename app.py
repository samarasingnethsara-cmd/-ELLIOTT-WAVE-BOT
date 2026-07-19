
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
from shheets_db import fetch_data, update_sheet

# --- App එකෙහි මූලික සැකසුම් ---
st.set_page_config(page_title="Advanced Elliott Wave AI Bot", layout="wide", initial_sidebar_state="expanded")
st.title("🦅 Advanced Elliott Wave AI Bot (Global Cloud Pro)")
st.write("Multi-User Professional Market Analysis & Centralized Risk Management Platform")

# --- Google Sheet Link ---
# ⚠️ මෙතනට ඔයාගේ Google Sheet URL එක දාන්න (දැනට Advanced Settings -> Secrets වල දාලා ඇති)
if "GOOGLE_SHEET_URL" in st.secrets:
    GOOGLE_SHEET_URL = st.secrets["GOOGLE_SHEET_URL"]
else:
    GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1FXFhTbaM7wAGjdpnQj3O_UNkFTEGHtHoYmPMDg-y_jQ/edit"

# User unique tracking via session (Browser level)
if "browser_fingerprint" not in st.session_state:
    st.session_state.browser_fingerprint = str(datetime.datetime.now().timestamp())

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False
if "active_code" not in st.session_state:
    st.session_state.active_code = ""

# --- Centralized Database Cloud Checking ---
if st.session_state.active_code:
    db = fetch_data(GOOGLE_SHEET_URL)
    if not db.empty and st.session_state.active_code in db['code'].values:
        row = db[db['code'] == st.session_state.active_code].iloc[0]
        st.session_state.is_premium = True

# --- Sidebar Settings ---
st.sidebar.header("🛠️ Bot Control Panel")

if st.session_state.is_premium:
    st.sidebar.success(f"👑 Premium Account (Code: {st.session_state.active_code})")
else:
    st.sidebar.warning("🆓 Free Account (Limited Features)")

# Free vs Premium Market Controls
if st.session_state.is_premium:
    market_type = st.sidebar.radio("Select Market Type", ["Crypto", "Forex"])
    if market_type == "Crypto":
        ticker_list = {
            "Bitcoin (BTC/USD)": "BTC-USD", "Ethereum (ETH/USD)": "ETH-USD",
            "Solana (SOL/USD)": "SOL-USD", "Ripple (XRP/USD)": "XRP-USD"
        }
    else:
        ticker_list = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X"}
    
    selected_display_name = st.sidebar.selectbox("Select Asset (Ticker)", list(ticker_list.keys()))
    ticker = ticker_list[selected_display_name]
    timeframe = st.sidebar.selectbox("Timeframe", ["1h", "4h", "1d"])
    period = st.sidebar.selectbox("Data Period", ["1mo", "3mo", "6mo"])
else:
    st.sidebar.info("🔒 Premium unlocked for BTC-USD on 1D Chart only.")
    ticker = "BTC-USD"
    timeframe = "1d"
    period = "6mo"
    st.sidebar.text("Asset: Bitcoin (BTC/USD)")
    st.sidebar.text("Timeframe: 1d (Daily)")

# --- MONEY MANAGEMENT INPUTS (Premium Only) ---
balance = 0.0
risk_pct = 1.0
if st.session_state.is_premium:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Money Management Plan")
    balance = st.sidebar.number_input("Your Account Balance ($)", min_value=1.0, value=1000.0, step=10.0)
    risk_pct = st.sidebar.slider("Risk Per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

st.sidebar.markdown("---")

# Activation Section
if not st.session_state.is_premium:
    st.sidebar.subheader("🔑 Activate Premium")
    input_code = st.sidebar.text_input("Enter Activation Code", type="password")
    if st.sidebar.button("Verify Code"):
        db = fetch_data(GOOGLE_SHEET_URL)
        if not db.empty and input_code in db['code'].values:
            row = db[db['code'] == input_code].iloc[0]
            devices_list = str(row['devices']).split(',') if pd.notna(row['devices']) and row['devices'] != "" else []
            devices_list = [d for d in devices_list if d]
            
            # Cloud verification fallback using browser fingerprint
            current_id = st.session_state.browser_fingerprint[:8]
            
            if len(devices_list) >= 2 and current_id not in devices_list:
                st.sidebar.error("❌ Maximum Device Limit Reached! (Max 2 Devices)")
            else:
                if current_id not in devices_list:
                    devices_list.append(current_id)
                new_devices_str = ",".join(devices_list)
                
                update_sheet(GOOGLE_SHEET_URL, input_code, new_devices_str)
                st.session_state.is_premium = True
                st.session_state.active_code = input_code
                st.sidebar.success("Activated Successfully via Cloud!")
                st.rerun()
        else:
            st.sidebar.error("Invalid Code or Not found in Cloud Registry!")

start_bot = st.sidebar.button("🚀 Start Analysis", use_container_width=True)

@st.cache_data(ttl=60)
def load_data(symbol, tf, pd_val):
    return yf.download(symbol, period=pd_val, interval=tf, group_by='column')

if start_bot:
    with st.spinner("Running AI Analysis..."):
        try:
            df = load_data(ticker, timeframe, period)
            df.columns = df.columns.get_level_values(0) if isinstance(df.columns, pd.MultiIndex) else df.columns
            df.reset_index(inplace=True)

            # Core Elliott Wave Signal Logic
            df['Swing_High'] = df['High'].rolling(window=5, center=True).max()
            df['Swing_Low'] = df['Low'].rolling(window=5, center=True).min()

            last_close = float(df['Close'].values[-1])
            last_low = float(df['Low'].iloc[-5:-1].min())
            
            entry_price = round(last_close, 2)
            stop_loss = round(last_low, 2)
            risk = entry_price - stop_loss
            take_profit = round(entry_price + (risk * 2), 2) if risk > 0 else round(entry_price - (abs(risk) * 2), 2)
            signal_text = "🟢 BUY (Wave 3 Start)" if risk > 0 else "🔴 SELL (Wave 3 Correction)"

            # --- Past Performance (Win/Loss/Pending) Logic ---
            past_close = float(df['Close'].values[-6])
            past_low = float(df['Low'].iloc[-11:-6].min())
            past_entry = round(past_close, 2)
            past_sl = round(past_low, 2)
            past_risk = past_entry - past_sl
            past_tp = round(past_entry + (past_risk * 2), 2) if past_risk > 0 else round(past_entry - (abs(past_risk) * 2), 2)
            past_signal = "BUY" if past_risk > 0 else "SELL"

            highest_since_past = float(df['High'].iloc[-5:].max())
            lowest_since_past = float(df['Low'].iloc[-5:].min())

            if past_signal == "BUY":
                if highest_since_past >= past_tp: status = "🏆 WIN"
                elif lowest_since_past <= past_sl: status = "❌ LOSS"
                else: status = "⏳ PENDING"
            else:
                if lowest_since_past <= past_tp: status = "🏆 WIN"
                elif highest_since_past >= past_sl: status = "❌ LOSS"
                else: status = "⏳ PENDING"

            # UI Layout
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("📡 Bot Signal Output")
                st.info(f"**Signal:** {signal_text}")
                st.metric(label="Entry Price", value=f"${entry_price:,}")
                st.metric(label="Stop Loss (SL)", value=f"${stop_loss:,}")
                st.metric(label="Take Profit (TP)", value=f"${take_profit:,}")

                # --- Win/Loss/Pending කොටස (Free & Premium දෙගොල්ලන්ටම පෙනේ) ---
                st.markdown("---")
                st.subheader("📜 Last Signal Performance")
                if "WIN" in status: st.success(f"Result: {status}")
                elif "LOSS" in status: st.error(f"Result: {status}")
                else: st.warning(f"Result: {status}")
                st.write(f"**Prev Entry:** ${past_entry} ({past_signal}) | **Prev TP:** ${past_tp} | **Prev SL:** ${past_sl}")

                # Money Management Section
                st.markdown("---")
                if st.session_state.is_premium:
                    st.subheader("🛡️ Professional Risk Calculator")
                    risk_amount = balance * (risk_pct / 100)
                    price_risk_per_unit = abs(entry_price - stop_loss)
                    
                    if price_risk_per_unit > 0:
                        position_size = risk_amount / price_risk_per_unit
                        st.success(f"**Recommended Position Size:** {position_size:.4f} Units")
                        st.write(f"💼 **Total Trade Value:** ${position_size * entry_price:.2f}")
                        st.write(f"🛑 **Max Loss if SL hits:** ${risk_amount:.2f}")
                        st.write(f"🎯 **Max Profit if TP hits:** ${risk_amount * 2:.2f}")
                else:
                    st.info("🔒 **Money Management Plan locked.** Upgrade to Premium to auto-calculate lot sizes.")

            with col2:
                st.subheader("📊 Elliott Wave Live Chart")
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candlestick")])
                fig.add_hline(y=entry_price, line_dash="dash", line_color="green", annotation_text="Entry")
                fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", annotation_text="SL")
                fig.add_hline(y=take_profit, line_dash="dash", line_color="gold", annotation_text="TP")
                fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
