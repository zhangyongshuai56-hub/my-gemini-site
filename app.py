import streamlit as st
import google.generativeai as genai

# --- 1. 页面配置 ---
st.set_page_config(page_title="我的 AI 助手", page_icon="✨", layout="wide")

# --- 2. 侧边栏：模式切换 (类似官方 Gemini) ---
with st.sidebar:
    st.header("✨ 模型设置")
    
    # 创建一个二选一的单选按钮
    mode = st.radio(
        "选择模式：",
        ["🚀 极速响应 (Flash)", "🧠 深度思考 (Pro)"],
        captions=["速度最快，适合日常问答", "逻辑更强，会自动进行深度推理"]
    )

    st.divider()
    
    # 清空按钮
    if st.button("🗑️ 开启新对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 3. 核心逻辑配置 ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)

    # 根据选择的模式，自动分配 模型 和 指令
    if mode == "🚀 极速响应 (Flash)":
        # 这里用 Flash 模型，追求速度
        # 如果你的账号不支持 flash，可以改回 'models/gemini-3-pro-preview'
        target_model = "models/gemini-1.5-flash" 
        sys_instruction = "你是一个简洁高效的助手。回答要快，直接切入重点。"
        
    else: # 深度思考模式
        # 这里用你之前测通的那个高级模型
        target_model = "models/gemini-3-pro-preview"
        # 注入“思维链”指令，让它模仿 o1 模型进行思考
        sys_instruction = """
        你是一个深度思考专家。
        在回答用户之前，你必须先在一个 <thinking> 标签块中进行详细的逻辑推演、步骤规划和自我纠错。
        思考过程要全面，然后再给出最终的回答。
        """

    # 初始化模型
    model = genai.GenerativeModel(
        target_model,
        system_instruction=sys_instruction
    )

except Exception as e:
    # 如果模型名字不对，这里会提示
    st.error(f"模型加载失败: {e}")
    st.info("提示：如果 Flash 报错 404，请去代码里把 'gemini-1.5-flash' 改成你能用的模型名。")
    st.stop()

# --- 4. 聊天界面 ---
st.title("✨ Gemini AI 助手")

# 初始化历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理输入
if prompt := st.chat_input("想问点什么？"):
    # 1. 显示用户问题
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 生成回答
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 开启流式传输 (stream=True) 保证速度感
            response_stream = model.generate_content(prompt, stream=True)
            
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"生成出错: {e}")
            if "404" in str(e) and "flash" in target_model:
                st.warning("你的账号可能暂不支持 Flash 模型，请切换到 '深度思考' 模式使用。")
