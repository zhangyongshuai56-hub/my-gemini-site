import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from PIL import Image
import pypdf
import io
import base64

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="全能 AI 聚合助手", page_icon="📂", layout="wide")
st.title("📂 全能 AI 聚合助手 (支持传图/文档)")

# --- 辅助函数：处理文件 ---
def process_uploaded_file(uploaded_file):
    """解析上传的文件，返回 (文本内容, 图片对象/Base64)"""
    file_type = uploaded_file.type
    
    # 情况 A: 图片
    if "image" in file_type:
        image = Image.open(uploaded_file)
        return None, image
        
    # 情况 B: PDF 文档
    elif "pdf" in file_type:
        try:
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return f"\n【附件文档内容】:\n{text}\n", None
        except Exception:
            return "无法读取 PDF 内容", None
            
    # 情况 C: 纯文本 (TXT/MD/PY)
    else:
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        return f"\n【附件文档内容】:\n{stringio.read()}\n", None

def get_image_base64(image):
    """将 PIL 图片转换为 Base64 字符串 (供 OpenAI 格式使用)"""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 2. 侧边栏配置 ---
with st.sidebar:
    st.header("🎛️ 设置面板")
    
    # 选择厂商
    provider = st.selectbox(
        "1. 选择厂商",
        ["Google Gemini", "DeepSeek (深度求索)", "阿里通义千问", "字节豆包 (火山引擎)"]
    )

    # 动态生成系统指令
    current_identity = provider.split(" ")[0]
    sys_msg = f"你现在的身份是【{current_identity}】的 AI 助手。请忽略之前的身份设定。"

    # === 自动隐藏密钥逻辑 ===
    # 函数：优先从 Secrets 获取，没有才显示输入框
    def get_secure_key(secret_name, label):
        if secret_name in st.secrets:
            st.success(f"✅ {label} 已配置")
            return st.secrets[secret_name]
        else:
            return st.text_input(f"输入 {label}", type="password")

    # === 厂商配置 ===
    api_key = ""
    selected_model = ""
    base_url = ""

    if provider == "Google Gemini":
        api_key = get_secure_key("GOOGLE_API_KEY", "Gemini API Key")
        model_list = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-3-pro-preview"]
        selected_model = st.selectbox("2. 选择模型", model_list)
        if st.toggle("🧠 深度思考", value=False):
            sys_msg += "\n请在回答前进行详细的 <thinking> 逻辑推演。"

    else:
        # 国产模型配置
        if provider == "DeepSeek (深度求索)":
            base_url = "https://api.deepseek.com"
            api_key = get_secure_key("DEEPSEEK_API_KEY", "DeepSeek Key")
            model_options = ["deepseek-chat", "deepseek-coder"]
            
        elif provider == "阿里通义千问":
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            api_key = get_secure_key("DASHSCOPE_API_KEY", "DashScope Key")
            model_options = ["qwen-plus", "qwen-max", "qwen-vl-max"] # VL支持图片
            
        elif provider == "字节豆包 (火山引擎)":
            base_url = "https://ark.cn-beijing.volces.com/api/v3"
            api_key = get_secure_key("VOLC_API_KEY", "Volcengine Key")
            model_options = ["输入 Endpoint ID"]

        # 模型选择框
        if provider == "字节豆包 (火山引擎)":
            default_ep = st.secrets.get("DOUBAO_ENDPOINT_ID", "")
            # 如果后台配了 Endpoint ID，也隐藏显示
            if default_ep:
                st.success("✅ Endpoint ID 已配置")
                selected_model = default_ep
            else:
                selected_model = st.text_input("输入 Endpoint ID (ep-xxx)")
        else:
            selected_model = st.selectbox("2. 选择模型", model_options)

    st.divider()
    if st.button("🗑️ 清空对话"):
        st.session_state.messages = []
        st.rerun()

# --- 3. 聊天界面 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. 文件上传区 (放在输入框上方) ---
uploaded_file = st.file_uploader("📎 上传图片或文档 (支持 PDF/TXT/JPG/PNG)", type=['txt', 'pdf', 'md', 'py', 'png', 'jpg', 'jpeg'])

# --- 5. 处理输入 ---
if prompt := st.chat_input("输入你的问题..."):
    if not api_key:
        st.warning("请先配置 API Key")
        st.stop()

    # === 处理附件 ===
    file_text = ""
    file_image = None
    
    if uploaded_file:
        with st.spinner("正在解析文件..."):
            extracted_text, extracted_image = process_uploaded_file(uploaded_file)
            if extracted_text:
                file_text = extracted_text
                st.info(f"📄 已加载文档：{uploaded_file.name}")
            if extracted_image:
                file_image = extracted_image
                st.image(file_image, caption="已上传图片", width=200)

    # 组合用户输入：问题 + 文档内容
    final_prompt = prompt + file_text

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
        if file_image:
            st.image(file_image, width=200)
    
    # 存入历史 (注意：为了简单，历史记录只存文本描述，不存大图片对象)
    history_content = prompt + (" [已发送一张图片]" if file_image else "") + (" [已发送文档]" if file_text else "")
    st.session_state.messages.append({"role": "user", "content": history_content})

    # === 生成回答 ===
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # --- Google Gemini 通道 ---
            if provider == "Google Gemini":
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model, system_instruction=sys_msg)
                
                # 构建输入：如果有图片，Gemini 接受 [文本, 图片] 列表
                content_parts = [final_prompt]
                if file_image:
                    content_parts.append(file_image)
                
                # 历史记录转换 (Gemini 暂不支持多轮带图，所以带图只发单次，或者仅文本历史)
                # 这里采用策略：带图时暂不带历史，防止格式报错；纯文本时带历史
                if file_image:
                    response = model.generate_content(content_parts, stream=True)
                else:
                    gemini_history = [{"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                    chat = model.start_chat(history=gemini_history)
                    response = chat.send_message(final_prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        placeholder.markdown(full_response + "▌")

            # --- 国产模型 (OpenAI 格式) 通道 ---
            else:
                client = OpenAI(api_key=api_key, base_url=base_url)
                messages = [{"role": "system", "content": sys_msg}]
                
                # 构建当前消息
                current_user_msg = {"role": "user", "content": []}
                
                # 1. 如果有文本
                current_user_msg["content"].append({"type": "text", "text": final_prompt})
                
                # 2. 如果有图片 (转换为 Base64 URL)
                if file_image:
                    # 警告：DeepSeek 目前不收图，Qwen/豆包视觉版可以
                    if "deepseek" in selected_model:
                        st.warning("⚠️ DeepSeek 可能不支持图片，若报错请仅传文档。")
                    
                    base64_image = get_image_base64(file_image)
                    current_user_msg["content"].append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    })

                # 拼接历史 (为了简化，带图时我们只发本次，防止历史格式太复杂)
                # 如果没有图，就正常拼接历史
                if not file_image:
                    for m in st.session_state.messages[:-1]:
                        messages.append({"role": m["role"], "content": m["content"]})
                
                messages.append(current_user_msg)

                stream = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    stream=True
                )
                
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_response += delta.content
                        placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"请求出错: {e}")
            if "400" in str(e) and file_image:
                st.warning("👉 当前选择的模型可能不支持图片识别，请尝试切换到 Google Gemini 或 阿里通义(VL) 版。")
