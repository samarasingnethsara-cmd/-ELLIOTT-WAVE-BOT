import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import socket
from shheets_db import fetch_data, update_sheet # අපේ අලුත් ශීට් කනෙක්ටරය

# --- App එකෙහි මූලික සැකසුම් ---
st.set_page_config(page_title="Advanced Elliott Wave AI Bot", layout="wide", initial_sidebar_state="expanded")
st.title("🦅 Advanced Elliott Wave AI Bot (Global Cloud Pro)")
st.write("Multi-User Professional Market Analysis & Centralized Risk Management Platform")

# --- Google Sheet Link එක මෙතනට දාන්න ---
# ⚠️ වැදගත්: ඔයා කොපි කරගත්ත Google Sheet ලින්ක් එක පහත දරපුවට ඇතුලත් කරන්න.
GOOGLE_SHEET_URL = "ඔයාගේ_GOOGLE_SHEET_LINK_එක_මෙතනට_දාන්න"

today_str = str(datetime.date.today())

try:
    current_device_id = socket.gethostname()
except:
    current_device_id = "Unknown_Device"

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0
if "allowed_devices" not in st.session_state:
    st.session_state.allowed_devices = []
if "active_code" not in st.session_state:
    st.session_state.active_code = ""

# --- Centralized Database Cloud Checking ---
# ඇප් එක ලෝඩ් වෙද්දීම කලින් කේතයක් ගහලද බලන්න ශීට් එක චෙක් කරයි
if st.session_state.active_code and GOOGLE_SHEET_URL != "ඔයාගේ_GOOGLE_SHEET_LINK_එක_මෙතනට_දාන්න":
    db = fetch_data(GOOGLE_SHEET_URL)
    if not db.empty and st.session_state.active_code in db['code'].values:
        row = db[db['code'] == st.session_state.active_code].iloc[0]
        devices_list = str(row['devices']).split(',') if pd.notna(row['devices']) and row['devices'] != "" else []
        st.session_state.allowed_devices = [d for d in devices_list if d]
        
        if current_device_id in st.session_state.allowed_devices:
            st.session_state.is_premium = True

# --- Sidebar Settings ---
st.sidebar.header("🛠️ Bot Control Panel")

if st.session_state.is_premium:
    st.sidebar.success(f"👑 Premium Account (Code: {st.session_state.active_code})")
else:
    st.sidebar.warning("Free Account Enabled")

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

# --- MONEY MANAGEMENT INPUTS ---
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
        if GOOGLE_SHEET_URL == "ඔයාගේ_GOOGLE_SHEET_LINK_එක_මෙතනට_දාන්න":
            st.sidebar.error("Developer Note: Please set GOOGLE_SHEET_URL first!")
        else:
            db = fetch_data(GOOGLE_SHEET_URL)
            if not db.empty and input_code in db['code'].values:
                row = db[db['code'] == input_code].iloc[0]
                devices_list = str(row['devices']).split(',') if pd.notna(row['devices']) and row['devices'] != "" else []
                devices_list = [d for d in devices_list if d]
                
                if len(devices_list) >= 2 and current_device_id not in devices_list:
                    st.sidebar.error("❌ Maximum Device Limit Reached! (1 PC & 1 Phone only)")
                else:
                    if current_device_id not in devices_list:
                        devices_list.append(current_device_id)
                    new_devices_str = ",".join(devices_list)
                    
                    # Update Central Google Sheet
                    update_sheet(GOOGLE_SHEET_URL, input_code, new_devices_str)
                    
                    st.session_state.is_premium = True
                    st.session_state.active_code = input_code
                    st.session_state.allowed_devices = devices_list
                    st.sidebar.success("Activated Successfully via Cloud! Rerunning...")
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

            # Core Trading Logic
            df['Swing_High'] = df['High'].rolling(window=5, center=True).max()
            df['Swing_Low'] = df['Low'].rolling(window=5, center=True).min()

            last_close = float(df['Close'].values[-1])
            last_low = float(df['Low'].iloc[-5:-1].min())
            
            entry_price = round(last_close, 2)
            stop_loss = round(last_low, 2)
            risk = entry_price - stop_loss
            take_profit = round(entry_price + (risk * 2), 2) if risk > 0 else round(entry_price - (abs(risk) * 2), 2)
            signal_text = "🟢 BUY (Wave 3 Start)" if risk > 0 else "🔴 SELL (Wave 3 Correction)"

            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("📡 Bot Signal Output")
                st.info(f"**Signal:** {signal_text}")
                st.metric(label="Entry Price", value=f"${entry_price:,}")
                st.metric(label="Stop Loss (SL)", value=f"${stop_loss:,}")
                st.metric(label="Take Profit (TP)", value=f"${take_profit:,}")

                if st.session_state.is_premium:
                    st.markdown("---")
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
                    st.markdown("---")
                    st.info("🔒 **Money Management Plan locked.** Upgrade to Premium.")

            with col2:
                st.subheader("📊 Elliott Wave Live Chart")
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")