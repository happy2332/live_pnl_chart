import streamlit as st
from streamlit_autorefresh import st_autorefresh
from kiteconnect import KiteConnect
import datetime
import pandas as pd
import plotly.graph_objects as go
import pytz
import datetime

# Define the IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Auto-refresh every 1 minute (60,000 ms)
st_autorefresh(interval=60000, key="refresh")

st.title('Trading Analyzer')

api_key = st.secrets["api_key"]
api_secret = st.secrets["api_secret"]

# Initialize PnL tracking
if 'pnl_history' not in st.session_state:
    st.session_state.pnl_history = []
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = []

st.write("Click on this [link](https://kite.trade/connect/login?api_key=" + api_key + "&v=3) for kite login.")
resulting_url = st.text_input('Enter resulting URL:', '')

if st.button("Next") or ('access_token' in st.session_state and resulting_url):
    try:
        if 'access_token' not in st.session_state:
            request_token = resulting_url.split('request_token=')[1].split('&')[0]
            kite = KiteConnect(api_key=api_key)
            data = kite.generate_session(request_token, api_secret=api_secret)
            st.session_state.access_token = data["access_token"]
            st.success("✅ Successfully authorized")
        else:
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(st.session_state.access_token)

        kite.set_access_token(st.session_state.access_token)

        positions = kite.positions()
        net_positions = positions['net']
        total_pnl = sum(pos['pnl'] for pos in net_positions)

        # Save PnL and time
        # Get the current time in GMT and convert it to IST
        now = datetime.datetime.now(pytz.utc)  # Get time in UTC
        now_ist = now.astimezone(IST)  # Convert to IST
        # Save PnL and time
        st.session_state.pnl_history.append(total_pnl)
        st.session_state.timestamps.append(now_ist)

        df = pd.DataFrame({
            'Timestamp': [ts.astimezone(IST) for ts in st.session_state.timestamps],  # Convert all timestamps to IST
            'PnL': st.session_state.pnl_history
        })

        st.subheader("📈 Current Net P&L: ₹{:.2f}".format(total_pnl))

        # Plotly interactive chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['PnL'],
            mode='lines+markers',
            name='PnL',
            hovertemplate='Time: %{x}<br>PnL: ₹%{y:.2f}<extra></extra>',
            line=dict(color='royalblue')
        ))

        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='PnL (₹)',
            title='PnL Over Time',
            xaxis=dict(
                tickmode='auto',
                nticks=5,
                showgrid=True
            ),
            yaxis=dict(showgrid=True),
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Optional: Position Details
        if st.checkbox("Show Position Details"):
            for pos in net_positions:
                st.write(
                    f"Symbol: {pos['tradingsymbol']}, "
                    f"P&L: ₹{pos['pnl']:.2f}, "
                    f"Qty: {pos['quantity']}, "
                    f"Avg Price: ₹{pos['average_price']:.2f}"
                )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
