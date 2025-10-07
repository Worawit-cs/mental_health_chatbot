'''
This module is main file to build application
'''
import sys
import os
import streamlit as st
from pathlib import Path
import time as t
import json

# **********************************
# # Add project root to path
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))
# from utils.llm_client import LLMClient, get_available_models

# Config PATH

PROJECT_ROOT = Path(__file__).resolve().parent.parent
print(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    print("TRUE")
    sys.path.insert(0, str(PROJECT_ROOT))
for i in sys.path:
    print(i)

from path import get_path
# from .bac import RAG
# from backend.rag_util import RAG   # <- ถ้ามีโมดูลนี้อยู่จริง ให้ใช้บรรทัดนี้แทน
try:
    from backend.rag_util import RAG   # <- ถ้ามีโมดูลนี้อยู่จริง ให้ใช้บรรทัดนี้แทน
except Exception:
    class RAG:
        def test(self, x):
            return {"answer": "ขออภัย ระบบตอบไม่ได้ในตอนนี้.", "severity_level": 0}

BASE_DIR, PATH = get_path()
IMAGE_PATH = os.path.join(BASE_DIR, PATH["IMAGE_PATH"])

st.set_page_config(page_title="AI+ CARE YOU", layout="wide")
# EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2       #our embedding model

APP_DIR = Path(__file__).parent
ASSETS_DIR = APP_DIR
# ---- แก้ path ให้ cross-platform ----
USER_AVATAR_PATH = Path(IMAGE_PATH) / "user_image.png"
BOT_AVATAR_PATH  = Path(IMAGE_PATH) / "bot.png"
# BG_PATH  = Path(rf"{IMAGE_PATH}\BG.png")

# ==================================================================
# Intitialize input
user_prompt = "Topic: "

def load_avatar_bytes(path: Path):
    try:
        return path.read_bytes() if path.exists() else None
    except Exception:
        return None

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

ROLE = [
    {"key": "friend",      "TH": "เพื่อน",    "ENG": "Friend"},
    {"key": "professor",   "TH": "อาจารย์",   "ENG": "Professor"},
    {"key": "oni_chan",    "TH": "รุ่นพี่",    "ENG": "Oni_chan"},
]

LANG_NAME_DISPLAY = {"TH": "ไทย", "ENG": "English"}
advice_message = {"TH": "😁แนะนําคําถาม", "ENG": "😁Suggested Questions"}
QUICK_CHAT = [
    {"key": 1,   "TH": "เครียดเรื่องคะแนนสอบ 😩",    "ENG": "I'm stressed about my exam scores. 😩"},
    {"key": 2,   "TH": "เครียดจนนอนไม่หลับแก้ยังไงดี 🫩",   "ENG": "I'm so stressed that I can't sleep. What can I do? 🫩"},
    {"key": 3,   "TH": "พรุ่งนี้สอบแต่ไม่ได้อ่านหนังสือทำยังไงดี!!!! ☠️",    "ENG": "My exam is tomorrow, but I haven't studied. What should I do? ☠️"},
]

FRIEND_STYLE = """
writing_style:
    Roleplay as a close, caring friend. Use a familiar, candid voice that feels like a long message from someone who truly gets the user. Start with empathy and specific reflection, weave in relatable suggestions, and keep the tone human and sincere—never preachy or overdramatic. Light warmth or a hint of humor is fine if it eases tension, but keep the center on the user. If one line carries the heart of your message, you may place it in quotation marks for gentle emphasis. Aim for natural flow and authenticity.
    """

SENPAI_STYLE = """
writing_style:
    Roleplay as a warm, steady older student mentor (รุ่นพี่). Refer to yourself as “พี่” and address the user as “น้อง” or “เธอ.” Sound calm, protective, and practical. Validate feelings first, reflect back key details to show you listened, then offer small, doable next steps without pressure. Use gentle, non-judgmental language and soft encouragement. You may highlight one memorable line in quotation marks if it helps the message land. Keep the voice grounded, reassuring, and respectful of the user’s pace.
"""

PROFESSOR_STYLE = """
writing_style:
    Roleplay as a gentle, supportive professor (อาจารย์). Refer to yourself as “อาจารย์” and address the user as “นักศึกษา” or “คุณ.” Speak with calm clarity and respect. Acknowledge the student’s effort, summarize what you heard, and offer clear, reasoned guidance with kind, measured phrasing. Encourage autonomy and informed choices; avoid moralizing or diagnosing. You may highlight a single key reassurance or principle in quotation marks. Maintain a composed, caring, and trustworthy presence.
"""


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

def get_quick_key_from_label(label: str, lang: str) -> str:
    for item in QUICK_TOPICS:
        if item[lang] == label:
            return item["key"]
    return QUICK_TOPICS[0]["key"]

def get_role_label(key: str, lang: str) -> str:
    for item in ROLE:
        if item["key"] == key:
            return item[lang]
    return ROLE[0][lang]

def get_role_index_from_key(key: str) -> int:
    for i, item in enumerate(ROLE):
        if item["key"] == key:
            return i
    return 0

def get_role_key_from_label(label: str, lang: str) -> str:
    for item in ROLE:
        if item[lang] == label:
            return item["key"]
    return ROLE[0]["key"]

#setting text
st.markdown("""
    <style>
    div[data-baseweb="select"] { margin-top: -35px; }

    [data-testid="stChatMessage"]{
        padding-top: 0.5rem; padding-bottom: 0.5rem;
    }
    [data-testid="stChatMessageContent"]{
        display:flex; align-items:center; min-height:40px; padding-top:6px; margin-top:-4px;
    }

    div.stButton > button { margin-top: -100px; }

    section[data-testid="stSidebar"] { width: 320px !important; }

    [data-testid="stAppViewContainer"]{
        background: radial-gradient(70% 100% at 10% 0%, #2a0d1f, transparent 60%),
                    linear-gradient(160deg, #0b0f1a 0%, #131327 40%, #1b0f2f 100%);
    }

    div.stMarkdown p,
    [data-testid="stChatMessageContent"] p {
        white-space: pre-wrap; 
    }
    .sidebar-title {
    font-size: 1000px; /* Adjust the font size as needed */
    font-weight: bold; /* Optional: make the title bold */
    color: #333333; /* Optional: set a specific color */
    }

    </style>
""", unsafe_allow_html=True)

st.session_state.setdefault("messages", [])
st.session_state.setdefault("llm_client", None)
st.session_state.setdefault("lang", "TH")
st.session_state.setdefault("quick_key", "general")
st.session_state.setdefault("count", True)
st.session_state.setdefault("role_key", "friend")

TEXT = {
    "TH": {
        "subtitle_cols": [1.4, 0.6],
        "title": "ปรึกษาด้านหัวใจไปกับ AI สุดน่ารัก",
        "subtitle": "ที่ปรึกษาทางด้านอาการทางจิต ก่อนไปพบจิตแพทย์โดยตรง",
        "placeholder": "พิมพ์ข้อความของคุณที่นี่...",
        "language": "ภาษา",
        "consult": "ปรึกษา",
        "first_message": "สวัสดี ผม AI+ CARE YOU มีอะไรให้ผมช่วยไหมครับ ? 👨🏻‍⚕️",
        "role": "บทบาท"
    },
    "ENG": {
        "subtitle_cols": [1.55, 0.6],
        "title": "Heart-to-heart with a cute AI",
        "subtitle": "A mental-health pre-consultation before seeing a psychiatrist",
        "placeholder": "Type your message here...",
        "language": "Language",
        "consult": "Consult",
        "first_message": "Hello! I’m AI+ CARE YOU. What can I do for you today ? 👨🏻‍⚕️",
        "role": "Role"
    }
}

page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: ;
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-position: center;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

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

def updateJson(topic, lang, msg):
    global BASE_DIR, PATH
    INPUT_PATH = os.path.join(BASE_DIR, PATH["INPUT_PATH"])
    os.makedirs(INPUT_PATH, exist_ok=True)
    default_data = {"topic": "", "lang": "", "message": []}
    try:
        with open(f"{INPUT_PATH}/input.json", "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except Exception:
        input_data = default_data

    if lang == "TH":
        for i in QUICK_TOPICS:
            if i["TH"] == topic:
                topic = i["ENG"]
                break

    input_data["topic"] = topic
    input_data["lang"] = lang
    if "message" not in input_data or not isinstance(input_data["message"], list):
        input_data["message"] = []
    if(len(input_data["message"])%2 == 0):
        input_data["message"].append(f"\n{(len(input_data['message'])+2)//2}.USER_INPUT : {msg}\n")
    else:
        input_data["message"].append(f"\n{(len(input_data['message'])+2)//2}.ADVICE_ANSWER : {msg}\n")
    with open(f"{INPUT_PATH}/input.json", "w", encoding="utf-8") as f:
        json.dump(input_data, f, indent=2, ensure_ascii=False)

def suggested_text(response):
    suggested_text_list = response.get("user_suggested_questions", [])
    # print("\n\n\n\n",suggested_text_list)
    if len(suggested_text_list) <= 0:
        return
    st.markdown(advice_message.get(st.session_state.lang,"TH"))
    for i in range(3):
        if not suggested_text_list[i]:
            break
        st.markdown("- " + suggested_text_list[i])

def reset_inputJson():
    global BASE_DIR, PATH
    INPUT_PATH = os.path.join(BASE_DIR, PATH["INPUT_PATH"])
    os.makedirs(INPUT_PATH, exist_ok=True)
    default_data = {"topic": "", "lang": "", "message": []}
    try:
        with open(f"{INPUT_PATH}/input.json", "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except Exception:
        input_data = default_data
    for key in input_data:
        input_data[key] = "" if isinstance(input_data[key], str) else []
    with open(f"{INPUT_PATH}/input.json", "w", encoding="utf-8") as f:
        json.dump(input_data, f, indent=2, ensure_ascii=False)

def reponse_message(message,role):
    if(role == "friend" or role == "เพื่อน"):
        style = FRIEND_STYLE
    elif(role == "oni_chan" or role == "รุ่นพี่"):
        style = SENPAI_STYLE
    elif(role == "professor" or role == "อาจารย์"):
        style = PROFESSOR_STYLE
    temp = RAG().test("USER_INPUT : " + message,style)["answer"]
    print(temp)
    print("=========================================\n")
    print("DBUGGING STYLE:",style)
    print("\n=========================================")
    return temp
def answer_text(message):
    # print("Debugging Answer text:",message)
    for msg in message.split(" "):
        yield msg + " "
        t.sleep(0.07)

def answer_text_first(message):
    for msg in message.split(" "):
        # print(msg)
        yield msg + " "
        t.sleep(0.07)
def test_response():
    return {
        "advice_answer":"kuy",
        "user_suggested_questions":["1","2","3"]
    }

@st.dialog("ติดต่อ")
def popup():
    st.write(f"เบอร์โทรตอดต่อ xxxxxxxxxxxxx")
    st.link_button('เว็ปไซ','https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ&start_radio=1')

def web_page():
    global user_prompt
    lang = st.session_state.lang
    prompt = st.chat_input(TEXT[st.session_state.lang]["placeholder"])
    # Reset json when open new tab
    if "initialized" not in st.session_state:
        reset_inputJson()
        st.session_state.initialized = True

    #head and logo top page
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.image(str(Path(IMAGE_PATH) / 'LOGO.png'), width=200)
    with col2:
        st.title(TEXT[st.session_state.lang]["title"])
        c1, c2 = st.columns(TEXT[lang]["subtitle_cols"])
        with c1:
            st.markdown(TEXT[st.session_state.lang]["subtitle"])
            st.markdown(
                f"{TEXT[st.session_state.lang]['language']}:   {LANG_NAME_DISPLAY.get(st.session_state.lang, st.session_state.lang)}          {TEXT[st.session_state.lang]['consult']}:   {get_quick_label(st.session_state.quick_key, st.session_state.lang)}          {TEXT[st.session_state.lang]['role']}:   {get_role_label(st.session_state.role_key, st.session_state.lang)}"
            )
            

    if st.session_state.count:
        with st.chat_message("assistant", avatar=load_avatar_bytes(BOT_AVATAR_PATH)):
            ans = answer_text_first(TEXT[st.session_state.lang]["first_message"])
            st.write_stream(ans)
            st.session_state.count = False
    else:
        with st.chat_message("assistant", avatar=load_avatar_bytes(BOT_AVATAR_PATH)):
            st.markdown(TEXT[st.session_state.lang]["first_message"])

    # sidebar setting
    with st.sidebar:
        st.title("Config   🛠")
        # change_language
        st.markdown(TEXT[st.session_state.lang]["language"])
        new_lang = st.selectbox(' ', ['TH','ENG'],
                                index=['TH','ENG'].index(st.session_state.lang))

        #**********************************
        #change is funtoin in llm_client file

        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()
        st.write(' ')

        # quick chat
        st.write(TEXT[st.session_state.lang]["consult"])
        quick_labels = [item[st.session_state.lang] for item in QUICK_TOPICS]
        current_quick_idx = get_quick_index_from_key(st.session_state.quick_key)
        selected_topic_label = st.selectbox(' ', quick_labels, index=current_quick_idx)

        #**********************************
        #mode is funtoin in llm_client file

        new_quick_key = get_quick_key_from_label(selected_topic_label, st.session_state.lang)
        if new_quick_key != st.session_state.quick_key:
            st.session_state.quick_key = new_quick_key
            st.rerun()
        st.write(' ')
        

        # role
        st.write(TEXT[st.session_state.lang]["role"])
        role_labels = [item[st.session_state.lang] for item in ROLE]
        current_role_idx = get_role_index_from_key(st.session_state.role_key)
        selected_role_label = st.selectbox('  ',role_labels,index=current_role_idx)
        #**********************************
        #mode is funtoin in llm_client file

        new_role_key = get_role_key_from_label(selected_role_label, st.session_state.lang)
        if new_role_key != st.session_state.role_key:
            st.session_state.role_key = new_role_key
            st.rerun()
    
    init_session_state()
    display_chat_messages()
    c1,c2,c3 = st.columns([1,1,1])
    with c1:
        msg = QUICK_CHAT[0][st.session_state.lang]
        if st.button(msg ,width="stretch"):
            prompt = msg
            # return
    with c2:
        msg = QUICK_CHAT[1][st.session_state.lang]
        if st.button(msg ,width="stretch"):
            prompt = msg
            # return
    with c3:
        msg = QUICK_CHAT[2][st.session_state.lang]
        if st.button(msg ,width="stretch"):
            prompt = msg
            # return

                                
    # chat_input
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar=load_avatar_bytes(USER_AVATAR_PATH)):
            st.write(prompt)
        t.sleep(0.3)

        with st.chat_message("assistant", avatar=load_avatar_bytes(BOT_AVATAR_PATH)):
            with st.spinner("Thinking..."):
                #**********************************
                #chat is funtoin in llm_client file
                # ประกอบ user_prompt แบบอ่านง่าย (ไม่สะสมมั่ว)
                user_prompt_local = (
                    f"topic: {selected_topic_label}\n"
                    f"role: {selected_role_label}\n"
                    f"message: {prompt}"
                )
                print(f"DEBUGGING USER_PROMPT: {user_prompt_local}")

                # inputMessage(selected_topic_label, new_lang, prompt)
                updateJson(selected_topic_label, new_lang, prompt)

                response = reponse_message(prompt,new_role_key)

                # response = test_response()
                advice_text = response.get("advice_answer", "I couldn't find reliable context.")
                updateJson(selected_topic_label, new_lang, advice_text)
                # print("DEBUGGING advice_text:",advice_text)
                severity_level = int(response.get("severity_level", 0))

                if severity_level >= 8:
                    popup()
                ans = answer_text(advice_text)
                st.write_stream(ans)
                if severity_level >= 4:
                    suggested_text(response)
                
                
                st.session_state.messages.append(
                    {"role": "assistant", "content": advice_text})

def test_json():
    global BASE_DIR, PATH
    INPUT_PATH = os.path.join(BASE_DIR, PATH["INPUT_PATH"])
    try:
        with open(f"{INPUT_PATH}/input.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(data)
    except Exception:
        print({"topic": "", "lang": "", "message": []})

def main():
    web_page()
    test_json()

if __name__ == "__main__":
    main()
