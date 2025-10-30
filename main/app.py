import os
from dotenv import load_dotenv
import streamlit as st
from datetime import date
from agent import Agent
from model import Model
from vector_store import VectorStore

load_dotenv()

if not os.getenv("LLM_API_KEY"):
    st.error(
        "Missing API Key!\n\n"
        "Create a `.env` file and add your Groq API key like this:\n\n"
        "`LLM_API_KEY = <your-api-key>`"
    )
    st.stop()

st.set_page_config(layout="wide")
st.title("Bank Assistant")

model_map = {
    "Default (Llama 3.3 70b)": "llama-3.3-70b-versatile",
    "Qwen qwq 32b": "qwen-qwq-32b",
    "Mistral Saba 24b": "mistral-saba-24b",
    "Llama 4 Maverick 17b": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "Llama 4 Scout 17b": "meta-llama/llama-4-scout-17b-16e-instruct",
    "Llama 3.1 8b": "llama-3.1-8b-instant"
}

with st.sidebar:
    st.header("Simulated Settings")
    client_id = st.number_input("Enter Client ID", min_value=1, step=1)
    today_date = st.date_input("Select Today's Date", value=date.today())
    model_choice = st.selectbox(
    "Choose Model",
    [model for model in model_map.keys()],
    index=0
)

selected_model = model_map.get(model_choice, "llama-3.3-70b-versatile")

if "agent" not in st.session_state:
    st.session_state.agent = Agent(Model(), VectorStore())

agent = st.session_state.agent

if "messages" not in st.session_state:
    st.session_state.messages = []

if "rendered_messages" not in st.session_state:
    st.session_state.rendered_messages = []  
    
for message in st.session_state.rendered_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("chart") is not None:
            st.plotly_chart(message["chart"], use_container_width=True)
        
if prompt := st.chat_input("What do you want to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.rendered_messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        
        response = agent.chat(prompt, client_id, today_date, st.session_state.messages, model_name=selected_model)
        content = response["content"]
        chart = response["chart"]
    
    with st.chat_message("assistant"):
        st.markdown(content)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
        
    st.session_state.messages.append({"role": "assistant", "content": content})
    st.session_state.rendered_messages.append({"role": "assistant", "content": content, "chart": chart})
        
