import streamlit as st
import google.generativeai as genai

# 页面标题
st.title("我的私人 AI 助手")

# 获取密钥 (会自动从云端设置里读取)
api_key = st.secrets["GOOGLE_API_KEY"]

# 配置模型
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史聊天
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 接收用户输入
if prompt := st.chat_input("问我任何问题..."):
    # 显示你的问题
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用 Gemini 回答
    try:
        response = model.generate_content(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"出错啦: {e}")
