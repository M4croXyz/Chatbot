import os
import re
import fitz  # PyMuPDF
import google.generativeai as genai
import streamlit as st
from prompt import PROMPT_WORKAW
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import dotenv

# โหลด Config
dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# --- Config (Temperature 0 = แม่นยำที่สุด) ---
generation_config = {
    "temperature": 0.0,
    "top_p": 1.0, 
    "top_k": 32,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}

# --- 🔥 [ADDED] CSS ธีมอนิเมะสีน้ำเงิน & ตัวการ์ตูนลอย 🔥 ---
anime_theme_css = """
<style>
/* พื้นหลังหลักสีน้ำเงินเข้มแบบ Deep Ocean Anime */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #020c1b 0%, #0a192f 50%, #112240 100%);
    color: #e6f1ff;
}

/* ปรับแต่ง Sidebar */
[data-testid="stSidebar"] {
    background-color: rgba(2, 12, 27, 0.9);
    border-right: 1px solid #64ffda;
}

/* เอฟเฟกต์ตัวการ์ตูนลอย (Anime Floating) */
@keyframes float {
    0% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(5deg); }
    100% { transform: translateY(0px) rotate(0deg); }
}

.anime-char {
    position: fixed;
    z-index: 0;
    pointer-events: none;
    opacity: 0.6;
    animation: float 6s ease-in-out infinite;
}

/* Chat Bubbles สไตล์ Sci-fi Anime */
.stChatMessage {
    background-color: rgba(17, 34, 64, 0.7) !important;
    border: 1px solid rgba(100, 255, 218, 0.2);
    border-radius: 15px !important;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(5px);
}

/* ปรับสีหัวข้อ */
h1 {
    color: #64ffda !important;
    text-shadow: 0 0 10px rgba(100, 255, 218, 0.4);
    font-family: 'Courier New', Courier, monospace;
}

/* ปรับแต่งปุ่ม Sidebar */
.stButton>button {
    background-color: transparent;
    color: #64ffda;
    border: 1px solid #64ffda;
    border-radius: 10px;
    transition: 0.3s;
}
.stButton>button:hover {
    background-color: rgba(100, 255, 218, 0.1);
    box-shadow: 0 0 15px #64ffda;
}
</style>

<img src="https://www.pngarts.com/files/12/Anime-Girl-PNG-Photo.png" class="anime-char" style="bottom: 10%; right: 5%; width: 200px;">
<img src="https://www.pngarts.com/files/12/Anime-Girl-Free-PNG-Image.png" class="anime-char" style="top: 15%; left: 2%; width: 150px; filter: blur(1px);">
"""
st.markdown(anime_theme_css, unsafe_allow_html=True)

# --- ระบบอ่านไฟล์แบบ Hybrid ---
@st.cache_resource
def load_pdf_data_hybrid(file_path):
    text_content = ""
    page_images_map = {} 
    
    if os.path.exists(file_path):
        try:
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                page_num = i + 1
                text = page.get_text()
                text_content += f"\n[--- Page {page_num} START ---]\n{text}\n[--- Page {page_num} END ---]\n"
                
                image_blocks = [b for b in page.get_text("blocks") if b[6] == 1]
                saved_images = []
                
                if image_blocks:
                    for img_block in image_blocks:
                        rect = fitz.Rect(img_block[:4])
                        if rect.width > 50 and rect.height > 50: 
                            rect.x0 -= 5; rect.y0 -= 5; rect.x1 += 5; rect.y1 += 5
                            try:
                                pix_crop = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=rect)
                                saved_images.append(pix_crop.tobytes("png"))
                            except:
                                pass
                
                if not saved_images:
                    pix_full = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    saved_images.append(pix_full.tobytes("png"))

                if saved_images:
                    page_images_map[page_num] = saved_images
            return text_content, page_images_map
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return "", {}
    else:
        st.error(f"ไม่พบไฟล์ {file_path}")
        return "", {}

# --- เรียกใช้งาน ---
pdf_filename = "Graphic.pdf"
pdf_text, pdf_hybrid_images = load_pdf_data_hybrid(pdf_filename)

# --- System Prompt ---
FULL_SYSTEM_PROMPT = f"""
{PROMPT_WORKAW}
**CRITICAL INSTRUCTIONS FOR ACCURACY:**
1. Use ONLY information from the CONTEXT.
2. Identify page numbers from `[--- Page X START ---]`.
3. Citation Format: [PAGE: number] at the end.
{pdf_text}
"""

model = genai.GenerativeModel(
    model_name="gemini-flash-latest", 
    safety_settings=SAFETY_SETTINGS,
    generation_config=generation_config,
    system_instruction=FULL_SYSTEM_PROMPT
)

# --- UI Streamlit ---
def clear_history():
    st.session_state["messages"] = [{"role": "model", "content": "สวัสดีค่ะ น้อง Graphic Bot พร้อมให้บริการแล้วค่ะ 🎨✨"}]
    st.rerun()

with st.sidebar:
    if st.button("🗑️ ล้างประวัติการคุย"):
        clear_history()

st.title("✨ น้อง Shiro69 Bot 🎨")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "model", "content": "สวัสดีค่ะ น้อง Shiro69 Bot พร้อมให้บริการแล้วค่ะ 🎨✨"}]

for msg in st.session_state["messages"]:
    avatar_icon = "🐰" if msg["role"] == "user" else "🦄"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.write(msg["content"])
        if "image_list" in msg:
            for img_data in msg["image_list"]:
                st.image(img_data, caption=f"🖼️ ภาพประกอบจากหน้า {msg.get('page_num_ref')}", use_container_width=True)

if prompt := st.chat_input():
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="🐰").write(prompt)

    def generate_response():
        history_api = [{"role": msg["role"], "parts": [{"text": msg["content"]}]} for msg in st.session_state["messages"] if "content" in msg]
        try:
            strict_prompt = f"{prompt}\n(คำสั่ง: ค้นหาจาก Context เท่านั้น และระบุเลขหน้า [PAGE: x])"
            chat_session = model.start_chat(history=history_api)
            response = chat_session.send_message(strict_prompt)
            response_text = response.text
            
            page_match = re.search(r"\[PAGE:\s*(\d+)\]", response_text)
            images_to_show = []
            ref_page_num = None
            
            if page_match:
                ref_page_num = int(page_match.group(1))
                images_to_show = pdf_hybrid_images.get(ref_page_num, [])

            with st.chat_message("model", avatar="🦄"):
                st.write(response_text)
                for img_data in images_to_show:
                    st.image(img_data, caption=f"🖼️ ภาพประกอบจากหน้า {ref_page_num}", use_container_width=True)
            
            msg_data = {"role": "model", "content": response_text}
            if images_to_show:
                msg_data["image_list"] = images_to_show 
                msg_data["page_num_ref"] = ref_page_num
            st.session_state["messages"].append(msg_data)
        except Exception as e:
            st.error(f"ระบบขัดข้อง: {e}")

    generate_response()