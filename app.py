import streamlit as st
import google.generativeai as genai

# 1. 页面标题
st.set_page_config(page_title="我的私人 AI", page_icon="🚀")
st.title("🚀 我的私人 AI 助手")

# 2. 获取密钥
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # -------------------------------------------------------
    # 关键修改：使用了你查到的专用模型名字
    # -------------------------------------------------------
    model = genai.GenerativeModel('models/gemini-3-pro-preview') 

except Exception as e:
    st.error("API Key 配置有误，请检查 Secrets 设置。")
    st.stop()

# 3. 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 展示历史聊天
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 接收用户输入
if prompt := st.chat_input("你好，请问有什么可以帮你的？"):
    # 显示用户问题
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用模型回答
    try:
        # 创建一个空的占位符，准备显示正在生成的文字
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # 使用流式传输 (Stream) 让回复像打字机一样出来
            response = model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌") # 加个光标效果
            
            message_placeholder.markdown(full_response) # 显示最终完整内容
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"生成回复时出错: {e}")
