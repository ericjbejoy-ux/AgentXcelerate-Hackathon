"""
Supplier Admin Portal & Logistics Dashboard
============================================
Streamlit frontend to view and manage supplier inventory, commits, and carrier transits.

Run:
    streamlit run mocks/supplier_dashboard.py --server.port 8502
"""

import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Supplier Admin Portal",
    page_icon="🏬",
    layout="wide"
)

API_URL = "http://localhost:8001"

st.title("🏬 Digital Nexus Supplier & Logistics Portals")
st.markdown("Monitor supplier catalogs, manage incoming purchase orders, audit automated stock reallocations, and track profit margins.")

# Check Server Status
try:
    health_resp = requests.get(f"{API_URL}/health", timeout=2)
    server_online = (health_resp.status_code == 200)
except Exception:
    server_online = False

if not server_online:
    st.error("🔴 Supplier API Server is offline. Please start it with: `python -m mocks.supplier_server` at port 8001")
    st.stop()
else:
    st.success("🟢 Connected to Supplier & Logistics Gateways")

# Sidebar: Seller Selection
st.sidebar.header("Seller Profile View")
supplier_option = st.sidebar.selectbox(
    "Log in as Supplier Profile:",
    options=["supplier_a", "supplier_b", "supplier_c"],
    format_func=lambda x: {
        "supplier_a": "Supplier A (Primary - 10d Lead)",
        "supplier_b": "Supplier B (Express - 2d Lead)",
        "supplier_c": "Supplier C (Alt Region - 4d Lead)"
    }[x]
)

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📦 Live Stock Levels & Catalog")
    try:
        cat_resp = requests.get(f"{API_URL}/{supplier_option}/catalog").json()
        items = cat_resp["items"]
        
        df = pd.DataFrame(items)
        df.columns = ["SKU", "Description", "Unit Price ($)", "Available Stock Qty"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Could not load catalog: {e}")

with col2:
    st.subheader("📑 Incoming Purchase Orders (POs)")
    try:
        orders = requests.get(f"{API_URL}/seller/orders", params={"supplier_id": supplier_option}).json()
        if not orders:
            st.info("No incoming orders recorded for this supplier.")
        else:
            for order in reversed(orders):
                # Map priority colors
                priority_color = {
                    "HIGH": "red",
                    "MEDIUM": "blue",
                    "LOW": "gray"
                }.get(order["priority"], "gray")
                
                with st.expander(f"Order: {order['incoming_order_id']} ({order['part_id']})", expanded=True):
                    # Category: Demand Signal
                    st.markdown(f"**Buyer ID:** `{order['buyer_id']}` | **Priority:** :{priority_color}[{order['priority']}]")
                    st.markdown(f"**Requested Qty:** {order['requested_qty']} | **Allocated Qty:** {order['allocated_stock']}")
                    st.markdown(f"**Warehouse Loc:** `{order['warehouse_loc']}`")
                    
                    # Fulfillment Route
                    st.markdown(f"**Fulfillment Type:** `{order['fulfillment_type']}`")
                    
                    # Reallocation visibility
                    if order.get("deprioritized_order_id"):
                        st.error(f"⚠️ **Stock Reallocated from:** `{order['deprioritized_order_id']}` (Customer: `{order['affected_customer']}`)")
                        st.error(f"💸 **SLA Penalty Fee:** ${order['sla_penalty']}")
                        
                    # Financial Margins
                    st.markdown("---")
                    st.markdown(f"**Gross Revenue:** ${order['gross_revenue']} | **Fulfillment Cost:** ${order['fulfillment_cost']}")
                    if order.get("expedited_freight_cost", 0) > 0:
                        st.markdown(f"✈️ **Expedited Freight Cost:** ${order['expedited_freight_cost']}")
                    st.markdown(f"**Net Margin:** `${order['net_margin']}`")
                    
                    # Operational Directives
                    st.info(f"📋 **Action Recommendation:** {order['recommended_action']}")
                    st.markdown(f"**Approval Status:** `{order['automated_approval_status']}`")
                    
                    # Action button
                    if st.button(f"Cancel / Restock PO {order['incoming_order_id']}", key=order['incoming_order_id']):
                        requests.post(f"{API_URL}/seller/orders/{order['incoming_order_id']}/cancel")
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Could not retrieve orders: {e}")
