'''
This module is main file to build application
'''
import sys
import os
import streamlit as st
from pathlib import Path
import time as t
import json
from backend.rag_util import RAG

# **********************************
# # Add project root to path
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))
# from utils.llm_client import LLMClient, get_available_models

# Config PATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from path import get_path 

BASE_DIR,PATH = get_path()
IMAGE_PATH = os.path.join(BASE_DIR, PATH["IMAGE_PATH"])

st.set_page_config(page_title="AI+ CARE YOU", layout="wide")


APP_DIR = Path(__file__).parent          
ASSETS_DIR = APP_DIR                      
USER_AVATAR_PATH = Path(rf"{IMAGE_PATH}/user_image.png")
BOT_AVATAR_PATH  = Path(rf"{IMAGE_PATH}/bot.png")

# ==================================================================
# Intitialize input
user_prompt = "Topic: "

def load_avatar_bytes(path: Path):
    try:
        return path.read_bytes() if path.exists() else None
    except Exception:
        return None

# ===== Quick Chat mapping =====
QUICK_TOPICS = [
    {"key": "general",        "TH": "ปรึกษาทั่วไป",                  "ENG": "General consult"},
    {"key": "anxiety",        "TH": "ความวิตกกังวล",                 "ENG": "Anxiety"},
    {"key": "depression",     "TH": "ภาวะซึมเศร้า",                   "ENG": "Depression"},
    {"key": "postpartum",     "TH": "ภาวะซึมเศร้าหลังคลอด",           "ENG": "Postpartum depression"},
    {"key": "agoraphobia",    "TH": "กลัวการอยู่ในที่สาธารณะ",         "ENG": "Agoraphobia"},
    {"key": "medications",    "TH": "การใช้ยา/การรักษาทางจิตเวช",      "ENG": "Psych meds / treatment"},
    {"key": "pdd",            "TH": "ความผิดปกติทางอารมณ์แบบยืดเยื้อ", "ENG": "Persistent depressive disorder"},
    {"key": "dep_students",   "TH": "ภาวะซึมเศร้าในนักศึกษา",           "ENG": "Depression in students"},
    {"key": "stress_students","TH": "ความเครียดในนักศึกษา",            "ENG": "Stress in students"},
]

# ===== Conversation Count =====
iConver = 0

def get_quick_label(key: str, lang: str) -> str:
    for item in QUICK_TOPICS:
        if item["key"] == key:
            return item[lang]
    return QUICK_TOPICS[0][lang]

def get_quick_index_from_key(key: str) -> int:
    for i, item in enumerate(QUICK_TOPICS):
        if item["key"] == key:
            return i
    return 0

def get_key_from_label(label: str, lang: str) -> str:
    for item in QUICK_TOPICS:
        if item[lang] == label:
            return item["key"]
    return QUICK_TOPICS[0]["key"]

#setting text
st.markdown("""
    <style>
    div[data-baseweb="select"] {
        margin-top: -35px;
    }
    
    [data-testid="stChatMessage"] {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
    }
            
    [data-testid="stChatMessageContent"] {
    margin-top: -4px;  
    }

    div.stButton > button {
        margin-top: -100px;
    }
            
    [data-testid="stChatMessageContent"] {
    display: flex;
    align-items: center;  
    min-height: 40px;     
    padding-top: 6px;     
    }
    </style>
""", unsafe_allow_html=True)

st.session_state.setdefault("messages", [])
st.session_state.setdefault("llm_client", None)
st.session_state.setdefault("lang", "TH")  
st.session_state.setdefault("quick_key", "general")  

TEXT = {
    "TH": {
        "subtitle_cols": [1.4, 0.6, 1.3, 1], 
        "title": "ปรึกษาด้านหัวใจไปกับ AI สุดน่ารัก",
        "subtitle": "ที่ปรึกษาทางด้านอาการทางจิต ก่อนไปพบจิตแพทย์โดยตรง",
        "placeholder": "พิมพ์ข้อความของคุณที่นี่..."
    },
    "ENG": {
        "subtitle_cols": [1.55, 0.6, 1.3, 1],
        "title": "Heart-to-heart with a cute AI",
        "subtitle": "A mental-health pre-consultation before seeing a psychiatrist",
        "placeholder": "Type your message here..."
    }
}

def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "llm_client" not in st.session_state:
        st.session_state.llm_client = None

def display_chat_messages():
    """Display chat messages"""
    for message in st.session_state.messages:
        avatar = load_avatar_bytes(USER_AVATAR_PATH) if message["role"] == "user" else load_avatar_bytes(BOT_AVATAR_PATH)
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

def reponse_message(message):
    STATUS = False

    if STATUS:
        return "You should contact CMU CARE\n Here is our contac:\nFacebook:CMU Care\nPhone:xxx-xxx-xxxx"
    else:
        temp = RAG().test("USER_INPUT : " + message)["answer"]
        print(temp)
        return temp.get("advice_answer", "I couldn't find reliable context.")
def answer_text(message):
    for msg in message.split(" "):
        yield msg + " "
        t.sleep(0.07)

def updateJson(topic, lang, msg):
    global BASE_DIR,PATH
    INPUT_PATH = os.path.join(BASE_DIR, PATH["INPUT_PATH"])
    with open(f"{INPUT_PATH}/input.json", "r", encoding="utf-8") as f:
        input = json.load(f)

    # change topic to eng
    if lang == "TH":
        for i in QUICK_TOPICS:
            if i["TH"] == topic:
                topic = i["ENG"]
                break

    # update
    input["count"] += 1
    input["topic"] = topic
    input["lang"] = lang
    input["message"] +=  f"Conversation {input['count']}: {msg}\n"

    with open(f"{INPUT_PATH}/input.json", "w", encoding="utf-8") as f:
        json.dump(input, f, indent=2, ensure_ascii=False)

def reset_inputJson():
    global BASE_DIR,PATH
    INPUT_PATH = os.path.join(BASE_DIR, PATH["INPUT_PATH"])
    with open(f"{INPUT_PATH}/input.json", "r", encoding="utf-8") as f:
        input = json.load(f)

    for key in input:
        input[key] = "" if isinstance(input[key],str) else 0
    
    with open(f"{INPUT_PATH}/input.json", "w", encoding="utf-8") as f:
        json.dump(input, f, indent=2, ensure_ascii=False)


def web_page():
    global user_prompt
    lang = st.session_state.lang
    quick_key = st.session_state.quick_key

    if "initialized" not in st.session_state:
        reset_inputJson()
        st.session_state.initialized = True

    #head and logo top page
    col1, col2= st.columns([0.1, 0.9])
    with col1:
        st.image(f'{IMAGE_PATH}/LOGO.png', width=1000)  
    with col2:
        st.title(TEXT[st.session_state.lang]["title"])
        c1, c2, c3, c4 = st.columns(TEXT[lang]["subtitle_cols"])
        with c1:
            st.markdown(TEXT[st.session_state.lang]["subtitle"])
        with c2:
            new_lang = st.selectbox('', ['TH','ENG'],
                                    index=['TH','ENG'].index(st.session_state.lang)) 
            # st.session_state.llm_client.change(new_lang)
                #**********************************
                #change is funtoin in llm_client file

            if new_lang != st.session_state.lang:
                st.session_state.lang = new_lang
                st.rerun()
        with c3:
            quick_labels = [item[st.session_state.lang] for item in QUICK_TOPICS]
            current_idx = get_quick_index_from_key(st.session_state.quick_key)
            selected_label = st.selectbox('', quick_labels, index=current_idx)
            
            user_prompt += selected_label + " \nmesage: "
            
            # st.session_state.llm_client.mode(selected_label)
                #**********************************
                #mode is funtoin in llm_client file

            new_key = get_key_from_label(selected_label, st.session_state.lang)
            if new_key != st.session_state.quick_key:
                st.session_state.quick_key = new_key
                st.rerun()
                
    init_session_state()
    display_chat_messages()

    #chat_input
    if prompt := st.chat_input(TEXT[st.session_state.lang]["placeholder"]):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar=load_avatar_bytes(USER_AVATAR_PATH)):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=load_avatar_bytes(BOT_AVATAR_PATH)):
            with st.spinner("Thinking..."):
                # response = st.session_state.llm_client.chat(messages)
                    #**********************************
                    #chat is funtoin in llm_client file
                user_prompt += prompt
                print(f"DEBUGGING UER_PROMPT: {user_prompt}")
                response = reponse_message(prompt)

                updateJson(selected_label, new_lang ,prompt)
                # Display response
                ans = answer_text(response)
                st.write_stream(ans)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response})
def test_json():
    global BASE_DIR,PATH
    INPUT_PATH = os.path.join(BASE_DIR, PATH["INPUT_PATH"])
    with open(f"{INPUT_PATH}/input.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print(data)

def main():
    web_page()
    test_json()

if __name__ == "__main__":
    main()

