import os
import streamlit as st
from agent import ExaminerAgent

st.set_page_config(page_title='AI NLP Examiner', page_icon='🎓')
st.title('🎓 AI NLP Examiner')
st.write('Інтерактивний іспит з NLP. Вкажіть API-ключ, а потім почніть діалог.')
key = st.sidebar.text_input('OpenAI API key', type='password', value=os.getenv('OPENAI_API_KEY', ''))
model = st.sidebar.text_input('Модель', value='gpt-4o-mini')
if st.sidebar.button('Новий іспит'):
    st.session_state.pop('agent', None)
    st.session_state.pop('chat', None)
    st.rerun()
if 'chat' not in st.session_state:
    st.session_state.chat = []
for msg in st.session_state.chat:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
if not key:
    st.info('Введіть OpenAI API key у боковій панелі.')
else:
    if 'agent' not in st.session_state:
        st.session_state.agent = ExaminerAgent(key, model)
    if not st.session_state.chat:
        greeting = 'Вітаю! Я проведу іспит з NLP. Напишіть, будь ласка, ваше ім’я та email.'
        st.session_state.chat.append({'role': 'assistant', 'content': greeting})
        with st.chat_message('assistant'):
            st.markdown(greeting)
    prompt = st.chat_input('Ваша відповідь...', disabled=st.session_state.agent.finished)
    if prompt:
        st.session_state.chat.append({'role': 'user', 'content': prompt})
        with st.chat_message('user'):
            st.markdown(prompt)
        with st.chat_message('assistant'):
            try:
                with st.spinner('Агент думає...'):
                    reply = st.session_state.agent.respond(prompt)
                st.markdown(reply)
                st.session_state.chat.append({'role': 'assistant', 'content': reply})
                if st.session_state.agent.finished:
                    st.success('Іспит завершено, результат збережено.')
            except Exception as exc:
                st.error(f'Помилка: {exc}')
