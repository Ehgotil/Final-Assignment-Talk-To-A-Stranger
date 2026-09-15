import base64
import csv
import os
import random
import re
from datetime import datetime
import streamlit as st

# The file path is defined here. It defines absolute file paths using the directory of the current script. This prevents relative path resolution errors across different execution environments.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "journal.csv")
LOCAL_BG_PATH = os.path.join(BASE_DIR, "background.png")
LOCAL_RAIN_PATH = os.path.join(BASE_DIR, "rain.mp3")

# Here a tuple is used for the different nudges you can encounter during your journaling sessions.
NUDGES = (
    "Anything else?",
    "Mm-hm. What about that made you think the most?",
    "Tell me more.",
    "What else is on your mind?",
    "That needed to be said, right?",
    "Whatever you want to say, I'm right here listening.",
    "It takes a lot to open up, good on you. Do you have some more stuff to talk about?",
    "If you use that as a jumping-off point, where do your thoughts go?",
    "Remember to take a minute for yourself every now and again. You can't think straight if you don't. Come back to me once you're ready.",
    "So, what else happened?",
    "Tell me some unimportant stuff. Some day-to-day banalities need to be aired out every once in a while.",
    "Talk to me, what else is up?",
    "And then?",
    "What will you do now?",
    "What's the plan going forward?",
    "Take a step back and explain the circumstances surrounding this to me.",
    "When did all of this start?",
    "Oh yeah?",
    "Keep talking, I'm hooked.",
    "How did that happen?"
)

@st.cache_data
def get_background_url(file_path: str) -> str:
    target_path = file_path

# Fallback search for alternate image extensions.
    if not os.path.exists(target_path):
        for alt in ["background.jpg", "background.jpeg"]:
            alt_path = os.path.join(BASE_DIR, alt)
            if os.path.exists(alt_path):
                target_path = alt_path
                break

# Encode image file if it is found on disk.
    if os.path.exists(target_path):
        ext = os.path.splitext(target_path)[1].lower().replace(".", "")
        mime_type = "jpeg" if ext in ["jpg", "jpeg"] else ext
        with open(target_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/{mime_type};base64,{encoded}"

# Default web background fallback if no local files are found. Chosen in order to have a contingency if the user fails to replace the default background after replacing it.
    return "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?auto=format&fit=crop&w=1920&q=80"

@st.cache_data
def get_audio_source(file_path: str) -> str:
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:audio/mp3;base64,{encoded}"

# This is the contingency ambient rain sound URL. I opted not to use a local file, since the web version worked better in my testing and the rain sound did not seem as important to be customisable as the background.
    return "https://actions.google.com/sounds/v1/weather/rain_heavy_loud.ogg"

@st.cache_data
def load_journal_history() -> list:
    """Reads and caches past journal entries to prevent disk I/O on every Streamlit rerun."""
    if not os.path.isfile(CSV_PATH):
        return []
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            return [row for row in reader if len(row) == 2]
    except Exception as e:
        st.error(f"Error loading journal history: {e}")
        return []

# Here the application browser tab title and layout width are set up.
st.set_page_config(
    page_title="My Journal | A place for the thoughts that haunt us",
    layout="centered"
)

# Here the  cached background and audio resources are fetched.
BG_SOURCE = get_background_url(LOCAL_BG_PATH)
RAIN_SOURCE = get_audio_source(LOCAL_RAIN_PATH)

# Injects a custom CSS to apply dark glassmorphism effects, inspired by Apple's new Liquid Glass design language. This also interacts with streamlit and serves to create the layout of the website.
st.markdown(f"""
<style>
    /* Clean up default Streamlit top header bar */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* Global page layout background overlay and image wallpaper */
    .stApp {{
        background: linear-gradient(rgba(12, 10, 8, 0.50), rgba(12, 10, 8, 0.60)), 
                    url('{BG_SOURCE}') no-repeat center center fixed;
        background-size: cover;
        color: #F3EFE0;
    }}

    /* Serified typography across headers, labels, and text elements */
    h1, h2, h3, h4, label, p, span, .stMarkdown {{
        color: #F8F5EE !important;
        font-family: 'Georgia', serif;
    }}

    /* Reusable glassmorphic cards for instructions and page headers */
    .header-card, .info-card {{
        background: rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        padding: 1.5rem;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
        margin-bottom: 1.25rem;
    }}

    /* Glass style for Streamlit forms and text inputs */
    div[data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(16px);
        border-radius: 18px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        padding: 1.5rem !important;
    }}

    div[data-baseweb="input"], div[data-baseweb="base-input"] {{
        background: rgba(0, 0, 0, 0.25) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #FFFFFF !important;
    }}

    input, textarea {{
        color: #F8F5EE !important;
    }}

    /* Custom hoverable glass buttons */
    .stButton > button {{
        background: rgba(255, 255, 255, 0.1) !important;
        color: #F8F5EE !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }}

    .stButton > button:hover {{
        background: rgba(255, 255, 255, 0.22) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
    }}

    /* Chat bubble container and chat input styling */
    [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        padding: 1rem !important;
        margin-bottom: 0.8rem !important;
    }}

    [data-testid="stChatInput"] {{
        background: rgba(20, 16, 12, 0.45) !important;
        backdrop-filter: blur(18px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    /* Sidebar glass effect */
    [data-testid="stSidebar"] {{
        background: rgba(14, 12, 10, 0.65) !important;
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        border-right: 1px solid rgba(255, 255, 255, 0.12);
    }}

    /* Navigation tabs and archive expander cards */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background-color: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: rgba(255, 255, 255, 0.06);
        border-radius: 12px 12px 0px 0px;
        padding: 8px 16px;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }}

    .stTabs [aria-selected="true"] {{
        background: rgba(255, 255, 255, 0.18) !important;
        border-bottom: 2px solid #D4B28C !important;
    }}

    [data-testid="stExpander"] {{
        background: rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(12px);
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
    }}

    .journal-entry-text {{
        font-size: 1.05rem;
        line-height: 1.5;
        white-space: pre-wrap;
        color: #EAE5D9;
    }}

    /* Lockdown emergency screen box */
    .lock-box {{
        background: rgba(16, 12, 10, 0.85);
        backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        margin-top: 2rem;
    }}
</style>
""", unsafe_allow_html=True)

# The following section helps to initialise the session state. Streamlit clears local variable values on every rerun and the session state maintains, while the state persists across user interactions during a session.

if "session_id" not in st.session_state:
# This creates the timestamp that is used as a key for the current journaling session.
    st.session_state.session_id = datetime.now().strftime("%B %d, %Y at %I:%M %p")
if "user_entries" not in st.session_state:
# Stores raw text entries typed by user in the current session.
    st.session_state.user_entries = []
if "messages" not in st.session_state:
# The chat message list storing dictionary objects.
    st.session_state.messages = []
if "user_name" not in st.session_state:
# The user's preferred display name.
    st.session_state.user_name = "Friend"
if "safeword" not in st.session_state:
# The session trigger phrase that immediately locks down the interface.
    st.session_state.safeword = None
if "is_locked" not in st.session_state:
# The toggle flag for displaying emergency lockdown mode when the safe word is triggered.
    st.session_state.is_locked = False

# These are all application helper functions.
def save_amalgamated_session() -> None:
    if not st.session_state.user_entries:
        return

# Combines all session user text inputs separated by newlines.
    full_journal_text = "\n".join(st.session_state.user_entries)
    current_time = st.session_state.session_id

    rows = []

# Reads existing CSV rows into memory to preserve the exact chronological order.
    if os.path.isfile(CSV_PATH):
        try:
            with open(CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
# Filters out the current session row to avoid duplicating it.
                rows = [row for row in reader if len(row) == 2 and row[0] != current_time]
        except Exception as e:
            st.error(f"Error reading journal history: {e}")

# Appends current session.
    rows.append([current_time, full_journal_text])

# Writes a full updated dataset back to the local file using bulk write.
    try:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date/Time", "Journal Entry"])
            writer.writerows(rows)
# Clears the memory cache so the Archive tab updates instantly.
        load_journal_history.clear()
    except Exception as e:
        st.error(f"Error saving journal session: {e}")
def generate_response() -> str:
    return random.choice(NUDGES)


# This handles the Emergency Lockdown Screen that is rendered when `is_locked` is True (which is triggered by entering the session safeword).
if st.session_state.is_locked:
    st.markdown("""
        <div class="lock-box">
            <h2>Enough for now</h2>
            <p>That's okay. Come back whenever you feel ready.</p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")

# The reset button clears the session state values and restores the initial setup screen.
    if st.button("Ready to start over"):
        st.session_state.is_locked = False
        st.session_state.messages = []
        st.session_state.user_entries = []
        st.session_state.safeword = None
        st.session_state.session_id = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        st.rerun()

# Stops the execution of the remaining script blocks.
    st.stop()

# This section of the code is responsible for the initial setup and the configuration of the safe word. The screen is rendered on the first launch when no safeword has been registered for the session.
if not st.session_state.safeword:
    st.title("Talk to a stranger.")

    st.markdown("""
    <div class="info-card">
        <h3 style="margin-top:0;">Here's how we do things 'round here.</h3>
        <ul>
            <li>This is not a chatbot. No reply will be directly tailored to your entry. You can write whatever you want. When you need a nudge, send the message and the program will give you an idea on what to reflect on.</li>
            <li>No data leaves your machine. Nothing goes to the cloud and previous entries are accessible in the Archive tab.</li>
            <li>The first step is to pick a safe word. Type this word and the journal locks down, instantly ending the journaling session.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Let's get you all set before you get journaling.")

# The form input prevents the intermediate script execution until user clicks the submit button.
    with st.form("setup_form"):
        name_input = st.text_input("What do I call you, traveler?", value=st.session_state.get("user_name", "Friend"))
        safe_word_input = st.text_input(
            "What should be your safe word today, my friend?",
            type="password",
            help="Type this word anytime during journaling to end the journaling session."
        )
        submit_setup = st.form_submit_button("I'm ready to talk")

        if submit_setup:
            if not safe_word_input.strip():
                st.error("What should your safe word be today, my friend?")
            else:
# Saves the configuration details into the session state.
                st.session_state.user_name = name_input.strip() or "Friend"
                st.session_state.safeword = safe_word_input.strip().lower()
                st.success("Good choice.")
                st.rerun()

    st.stop()

# The following section is responsible for the main application area.
# This handles the sidebar.
with st.sidebar:
    st.header("Sanctuary Settings")
    st.write(f"**Journaler:** {st.session_state.user_name}")

    st.markdown("---")
    st.subheader("Background noise")

# This is the native Streamlit audio component to prevent state reset on reruns.
    st.audio(RAIN_SOURCE, format="audio/mp3", loop=True)

    st.markdown("---")
# Manual session reset option.
    if st.button("Start over"):
        st.session_state.messages = []
        st.session_state.user_entries = []
        st.session_state.session_id = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        st.rerun()


# This part of the main application area handles tab navigation.
tab_chat, tab_history = st.tabs(["Active Journal", "Past Entries"])

# This is the tab on which the user does the actual journaling.
with tab_chat:
    st.markdown(f"""
    <div class="header-card">
        <h2 style="margin:0;">Howdy, {st.session_state.user_name}</h2>
        <p style="margin:0; opacity: 0.85;">Session started: {st.session_state.session_id}</p>
    </div>
    """, unsafe_allow_html=True)

# Below you can see the first conversation prompt you see in a blank sessions.
    if not st.session_state.messages:
        st.session_state.messages.append(
            {"role": "assistant", "content": "How was your day? Anything you want to share?"}
        )

# Scrollable chat message container with fixed height.
    chat_container = st.container(height=420)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar=None):
                st.markdown(msg["content"])

# This handles text input submission from the user.
    if user_input := st.chat_input("Write your entry..."):
        # Record user entry in history and state
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.user_entries.append(user_input)

# Checks if user input contains the session safeword as a distinct word.
        if st.session_state.safeword and re.search(
            r'\b' + re.escape(st.session_state.safeword) + r'\b',
            user_input,
            re.IGNORECASE
        ):
            save_amalgamated_session()
            st.session_state.is_locked = True
            st.rerun()

# Generates the universal reflection prompt.
        reply = generate_response()
        st.session_state.messages.append({"role": "assistant", "content": reply})

# Persists the entry to the disk and refreshes the interface.
        save_amalgamated_session()
        st.rerun()

# This is the second tab on which you can review past journal entries.
with tab_history:
    st.header("Archive")
    st.write("Cheers to all the memories that have yet to be made.")
    st.markdown("---")

# Reads and renders past journal entries using the cached helper.
    entries = load_journal_history()

    if entries:
# Renders entries in reverse chronological order, beginning with the newest.
        for date_time, text in reversed(entries):
            with st.expander(date_time):
                st.markdown(
                    f'<div class="journal-entry-text">{text}</div>',
                    unsafe_allow_html=True
                )
    else:
        st.info("Nothing here yet. Why don't you change that?")