import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# --- 1. 页面设置 ---
st.set_page_config(page_title="全能 AI 聚合助手", page_icon="🤖", layout="wide")
st.title("🤖 全能 AI 聚合助手")

# --- 2. 侧边栏：控制中心 ---
with st.sidebar:
    st.header("🎮 模型控制台")
    
    # 选择厂商
    provider = st.selectbox(
        "1. 选择厂商",
        ["Google Gemini", "DeepSeek (深度求索)", "阿里通义千问", "字节豆包 (火山引擎)"]
    )

    # -------------------------------------------------------
    # 逻辑 A: Google Gemini (独立逻辑)
    # -------------------------------------------------------
    if provider == "Google Gemini":
        # 尝试从 Secrets 获取 Key，如果没有则显示输入框
        default_key = st.secrets.get("GOOGLE_API_KEY", "")
        api_key = st.text_input("输入 Gemini API Key", value=default_key, type="password")
        
        # 简单的模型列表 (因为自动检索需要先验证Key，为了不报错，我们预设常用列表)
        model_list = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-3-pro-preview"]
        selected_model = st.selectbox("2. 选择模型", model_list)
        
        # 深度思考开关
        is_deep_think = st.toggle("🧠 开启深度思考模式", value=False)

    # -------------------------------------------------------
    # 逻辑 B: 国产模型 (统用 OpenAI 格式连接)
    # -------------------------------------------------------
    else:
        # 根据厂商预设 Base URL 和 模型列表
        if provider == "DeepSeek (深度求索)":
            base_url = "https://api.deepseek.com"
            default_key = st.secrets.get("DEEPSEEK_API_KEY", "")
            # DeepSeek 只有这两个主要模型
            model_options = ["deepseek-chat", "deepseek-coder"]
            help_text = "Key 获取地址: platform.deepseek.com"
            
        elif provider == "阿里通义千问":
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            default_key = st.secrets.get("DASHSCOPE_API_KEY", "")
            # 阿里常用模型
            model_options = ["qwen-plus", "qwen-max", "qwen-turbo"]
            help_text = "Key 获取地址: bailian.console.aliyun.com"
            
        elif provider == "字节豆包 (火山引擎)":
            base_url = "https://ark.cn-beijing.volces.com/api/v3"
            default_key = st.secrets.get("VOLC_API_KEY", "")
            # 豆包比较特殊，这里不列名字，用户必须填 Endpoint ID
            model_options = ["手动输入 Endpoint ID"] 
            help_text = "⚠️ 豆包必须填写 'ep-xxx' 开头的接入点 ID，而非模型名。"

        # 显示 Key 输入框
        api_key = st.text_input(f"输入 {provider} API Key", value=default_key, type="password", help=help_text)
        
        # 显示模型选择
        if provider == "字节豆包 (火山引擎)":
            selected_model = st.text_input("输入豆包 Endpoint ID (ep-xxxx...)", value=st.secrets.get("DOUBAO_ENDPOINT_ID", ""))
        else:
            selected_model = st.selectbox("2. 选择模型", model_options)

    # 清空按钮
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.rerun()

# --- 3. 聊天界面 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. 处理输入 ---
if prompt := st.chat_input("请输入你的问题..."):
    if not api_key:
        st.error("🚫 请先在左侧填写 API Key！")
        st.stop()

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # --- 5. 核心生成逻辑 (双轨制) ---
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # === 分支一：Gemini 处理 ===
            if provider == "Google Gemini":
                genai.configure(api_key=api_key)
                
                sys_prompt = "你是一个智能助手。"
                if is_deep_think:
                    sys_prompt = "你是一个深度思考专家。回答前请先在 <thinking> 标签中进行详细推演。"
                
                model = genai.GenerativeModel(selected_model, system_instruction=sys_prompt)
                response = model.generate_content(prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        placeholder.markdown(full_response + "▌")

            # === 分支二：国产模型 (OpenAI 兼容模式) ===
            else:
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                # 构造消息历史
                messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                stream = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"请求失败: {e}")
            st.warning("如果连接国产模型超时，可能是因为云端服务器网络波动。")
