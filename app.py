import streamlit as st
import google.generativeai as genai

st.title("🔍 账号诊断模式")
st.write("正在连接 Google 服务器查询可用模型...")

try:
    # 1. 获取 Key
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)

    # 2. 列出所有可用模型
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)

    # 3. 显示结果
    if available_models:
        st.success(f"恭喜！成功连接。你的账号支持以下模型：")
        for model_name in available_models:
            st.code(model_name) # 把这些名字显示出来
        st.info("请把上面显示的任何一个名字（例如 models/gemini-pro）复制下来告诉我！")
    else:
        st.error("连接成功，但没有发现可用模型。这通常意味着 API Key 权限受限。")

except Exception as e:
    st.error(f"严重错误: {e}")
    st.warning("请检查 Streamlit 的 Secrets 里是否正确填写了 GOOGLE_API_KEY")
