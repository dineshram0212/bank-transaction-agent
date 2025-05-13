import os
import streamlit as st
from datetime import date
from agent import Agent
from model import Model
from vector_store import VectorStore

st.set_page_config(layout="wide")
st.title("MoneyLion Bank Assistant")

with st.sidebar:
    st.header("Simulation Settings")
    client_id = st.number_input("Enter Client ID", min_value=1, step=1)
    today_date = st.date_input("Select Today's Date", value=date.today())
    model_choice = st.selectbox(
    "Choose Model",
    ["llama-3.3-70b-versatile(default)", "mistral-saba-24b", "llama3-70b-8192", "qwen-qwq-32b", "deepseek-r1-distill-llama-70b"],
    index=0
)


if "agent" not in st.session_state:
    selected_model = None if model_choice == "llama-3.3-70b-versatile(default)" else model_choice
    st.session_state.agent = Agent(Model(selected_model), VectorStore())
    
agent = st.session_state.agent

if "messages" not in st.session_state:
    st.session_state.messages = []
    
    
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
if prompt := st.chat_input("What do you want to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        
        response = agent.chat(prompt, st.session_state.messages, client_id, today_date)
    
    with st.chat_message("assistant"):
        st.markdown(response)
        
    st.session_state.messages.append({"role": "assistant", "content": response})
        
