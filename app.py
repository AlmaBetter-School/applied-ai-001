"""The screen: collect a question and show the answer and order details."""
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agent import resolve

load_dotenv(Path(__file__).with_name(".env"))
st.set_page_config(page_title="Order Support", page_icon="📦")
st.set_option("client.toolbarMode", "viewer")
st.title("Where is my order?")
st.write("Ask about a parcel, then ask a follow-up without repeating its number.")
st.caption("Workshop example · Historical order records, not live tracking")

# Streamlit reruns this file after each interaction. Session state remembers the chat.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "order" not in st.session_state:
    st.session_state.order = None

if st.button("Start a new conversation"):
    st.session_state.messages = []
    st.session_state.order = None

if not st.session_state.messages:
    st.info("Try: Where is order ee64d42b8cf066f35eac1cf57de1aa85?")

message = st.chat_input("Ask about your order…", max_chars=2000)
if message:
    with st.spinner("Checking the order and preparing a reply…"):
        answer, order = resolve(message, st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": message})
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.order = order

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.text(message["content"])

order = st.session_state.order
if order:
    st.subheader("Order details")
    st.write("Order number:", order["order_id"])
    st.write("Recorded status:", order["status"])
    st.write("Estimated delivery:", order["expected_delivery"] or "Not recorded")
    st.write("Delivered on:", order["delivered_on"] or "Not recorded")

st.caption("This app can read records and suggest a next step. It cannot change an order or issue a refund.")
