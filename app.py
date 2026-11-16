
import os
import streamlit as st
from agent import ExaminerAgent

st.set_page_config(page_title="NLP Екзаменатор", page_icon="🎓")
st.title("🎓 NLP Екзаменатор")
st.write("Інтерактивний іспит з NLP. Введіть API-ключ і почніть діалог.")

key = st.sidebar.text_input("Groq API key", type="password", value=os.getenv("GROQ_API_KEY", ""))
model = st.sidebar.text_input("Модель", value="openai/gpt-oss-120b")

if st.sidebar.button("Новий іспит"):
    st.session_state.pop("agent", None)
    st.session_state.pop("chat", None)
    st.rerun()

if "chat" not in st.session_state:
    st.session_state.chat = []

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not key:
    st.info("Введіть Groq API key у боковій панелі.")
else:
    if "agent" not in st.session_state:
        st.session_state.agent = ExaminerAgent(key, model)

    if not st.session_state.chat:
        greeting = "Вітаю! Я проведу іспит з NLP. Напишіть ваше ім'я та email."
        st.session_state.chat.append({"role": "assistant", "content": greeting})
        with st.chat_message("assistant"):
            st.markdown(greeting)

    prompt = st.chat_input("Ваша відповідь...", disabled=st.session_state.agent.finished)

    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Агент думає..."):
                    reply = st.session_state.agent.respond(prompt)
                st.markdown(reply)
                st.session_state.chat.append({"role": "assistant", "content": reply})

                if st.session_state.agent.finished:
                    st.success("Іспит завершено, результат збережено.")
            except Exception as exc:
                st.error(f"Помилка: {exc}")
