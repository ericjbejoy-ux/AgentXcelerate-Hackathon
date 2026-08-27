"""
Supplier Dashboard - Hackathon UI
==================================
Streamlit frontend to view and manage supplier inventory and incoming orders.

Run:
    streamlit run mocks/supplier_dashboard.py --server.port 8502
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Setup Page Configuration
st.set_page_config(
    page_title="Supplier Admin Portal",
    page_icon="🏬",
    layout="wide"
)

# Configuration API Endpoint
API_URL = "http://localhost:8001"

st.title("🏬 External Supplier Portals")
st.markdown("This dashboard represents the **external** supplier interfaces. You can view catalogs, track incoming purchase orders sent by autonomous agents, or manually trigger disruptions (like cancellations) to demonstrate multi-agent fallback logic.")

# Check Server Status
try:
    health_resp = requests.get(f"{API_URL}/health", timeout=2)
    server_online = (health_resp.status_code == 200)
except Exception:
    server_online = False

if not server_online:
    st.error(f"🔴 Supplier API Server is offline. Please start it with: `python -m mocks.supplier_server` at port 8001")
    st.stop()
else:
    st.success("🟢 Connected to Supplier API Server")

# Sidebar: Seller Login / Profile selector
st.sidebar.header("Seller Selection")
supplier_option = st.sidebar.selectbox(
    "Login as Supplier Profile:",
    options=["supplier_a", "supplier_b", "supplier_c"],
    format_func=lambda x: {
        "supplier_a": "Supplier A (Primary - 10d Lead)",
        "supplier_b": "Supplier B (Express - 2d Lead)",
        "supplier_c": "Supplier C (Alt Region - 4d Lead)"
    }[x]
)

# Fetch supplier specific details
@st.fragment
def render_dashboard(supplier_id):
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📦 Live Catalog & Inventory Levels")
        try:
            cat_resp = requests.get(f"{API_URL}/{supplier_id}/catalog").json()
            items = cat_resp["items"]
            
            df = pd.DataFrame(items)
            df.columns = ["SKU", "Description", "Unit Price ($)", "Available Stock Qty"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Simple stock status alerts
            low_stock = df[df["Available Stock Qty"] < 50]
            if not low_stock.empty:
                st.warning(f"⚠️ Low inventory warning: {len(low_stock)} items have less than 50 units in stock.")
                
        except Exception as e:
            st.error(f"Could not load catalog: {e}")

    with col2:
        st.subheader("📑 Incoming Purchase Orders (POs)")
        try:
            orders = requests.get(f"{API_URL}/orders", params={"supplier_id": supplier_id}).json()
            if not orders:
                st.info("No orders received yet from autonomous procurement agents.")
            else:
                for order in reversed(orders):
                    status_color = {
                        "PENDING": "orange",
                        "COMPLETED": "green",
                        "CANCELLED": "red"
                    }.get(order["status"], "gray")
                    
                    with st.expander(f"Order {order['order_id']} — {order['sku']}", expanded=True):
                        st.markdown(f"**Status:** :{status_color}[{order['status']}]")
                        st.markdown(f"**Quantity:** {order['quantity']} units @ ${order['unit_price']} each")
                        st.markdown(f"**Total Cost:** ${order['total_cost']}")
                        st.markdown(f"**Est. Lead Time:** {order['lead_time_days']} days")
                        
                        if order["status"] == "PENDING":
                            if st.button(f"Cancel Order {order['order_id']}", key=order['order_id']):
                                requests.post(f"{API_URL}/orders/{order['order_id']}/cancel")
                                st.rerun()
                                
        except Exception as e:
            st.error(f"Could not load orders: {e}")

# Render active dashboard
render_dashboard(supplier_option)
