"""Display the conversation and the latest order."""
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agent import resolve

load_dotenv(Path(__file__).with_name(".env"))
st.set_option("client.toolbarMode", "viewer")
st.set_page_config(page_title="AI Support Resolution Agent", page_icon="📦")
st.title("AI Support Resolution Agent")
st.write("Ask about your delivery and find your next step.")
st.caption("Workshop Orders API · Historical records, not live tracking")
st.caption("Step 2: choose AlmaBetter inference (coming later) or your own Gemini key.")
st.caption("Example order ID: ee64d42b8cf066f35eac1cf57de1aa85")
with st.expander("How it works"):
    st.write("Your message → Understand → Check Orders API → Apply policy → Respond")

# Keep chat history in this browser session and send it with each new request.
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.reply = None

if message := st.chat_input("Ask about your order…", max_chars=2000):
    with st.spinner("Checking your request…"):
        reply = resolve(message, st.session_state.messages)
    st.session_state.messages.extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply.message},
    ])
    st.session_state.reply = reply

if not st.session_state.messages:
    st.info("Try: Where is order ee64d42b8cf066f35eac1cf57de1aa85?")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.text(message["content"])

reply = st.session_state.reply
st.caption(f"● {reply.status if reply else 'Ready to help'}")
if reply and reply.order:
    with st.container(border=True):
        st.subheader(f"Order #{reply.order.order_id}")
        st.metric("Status", reply.order.status.title())
        st.write("Recorded delivery estimate:", str(reply.order.expected_delivery or "Not available"))
        st.text(reply.order.latest_update)
        st.caption("Source: workshop Orders API · Historical delivery record.")

st.caption("You can ask follow-up questions about your order. This app cannot change orders or issue refunds.")
if st.session_state.messages and st.button("Start a new conversation"):
    st.session_state.messages = []
    st.session_state.reply = None
    st.rerun()
