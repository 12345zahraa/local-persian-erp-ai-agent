"""Streamlit web interface for the local ERP agent."""
# pip install streamlit

import streamlit as st

from agent import LocalERPAgent
from mcp_server import ERPServer


@st.cache_resource
def get_agent() -> LocalERPAgent:
    server = ERPServer()
    return LocalERPAgent(server=server)


st.set_page_config(page_title="ERP AI Agent", page_icon="🧠", layout="wide")

st.title("🧠 عامل ERP محلی")
st.markdown("این اپلیکیشن از مدل Ollama و دیتابیس SQLite برای پاسخ‌گویی به سوالات کسب‌وکار استفاده می‌کند.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("سوال خود را به فارسی وارد کنید...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("در حال تحلیل..."):
            agent = get_agent()
            response = agent.run(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
