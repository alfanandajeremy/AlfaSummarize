import streamlit as st
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="AI Meeting Recorder",
    page_icon="🎤",
    layout="wide"
)

# =========================
# API KEY SETUP
# =========================

try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    st.error("DeepSeek API Key not configured")
    st.stop()

# =========================
# OPENAI CLIENT (DEEPSEEK)
# =========================

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# =========================
# SESSION STATE
# =========================

if "history" not in st.session_state:
    st.session_state.history = []

# =========================
# FUNCTIONS
# =========================

def transcribe_audio(audio_path):

    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(
            audio_data,
            language="id-ID"
        )
        return text

    except Exception as e:
        return f"Transcription Error: {str(e)}"


def analyze_meeting(transcript):

    prompt = f"""
    Analyze this meeting transcript.

    Generate:
    1. Executive summary
    2. Key discussion points
    3. Decisions made
    4. Action items
    5. Risks identified
    6. Recommendations
    7. Communication insights

    Transcript:
    {transcript}
    """

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "You are a professional AI meeting analyst."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


def generate_pdf(title, transcript, analysis):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=title, ln=True)

    pdf.set_font("Arial", size=12)
    pdf.cell(
        200,
        10,
        txt=f"Generated: {datetime.now()}",
        ln=True
    )

    pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="Transcript", ln=True)

    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, transcript)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="AI Analysis", ln=True)

    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, analysis)

    filename = "meeting_summary.pdf"

    pdf.output(filename)

    return filename

# =========================
# SIDEBAR
# =========================

st.sidebar.title("AI Meeting Recorder")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Record Meeting",
        "History"
    ]
)

# =========================
# DASHBOARD
# =========================

if page == "Dashboard":

    st.title("🎤 AI Meeting Recorder & Analyzer")

    st.metric(
        "Total Meetings",
        len(st.session_state.history)
    )

    st.info(
        "Record or upload meeting audio to generate AI insights."
    )

    st.markdown("---")

    st.markdown("""
    ### Features

    ✅ Record from mobile/device  
    ✅ Upload audio  
    ✅ Speech-to-text  
    ✅ AI meeting summary  
    ✅ Action items  
    ✅ AI recommendations  
    ✅ Export PDF  
    """)

# =========================
# RECORD PAGE
# =========================

elif page == "Record Meeting":

    st.title("🎙️ Record Meeting")

    st.markdown("## Record From Device")

    audio = mic_recorder(
        start_prompt="▶️ Start Recording",
        stop_prompt="⏹️ Stop Recording",
        just_once=True,
        use_container_width=True
    )

    temp_audio_path = None

    # =========================
    # RECORD RESULT
    # =========================

    if audio:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as f:

            f.write(audio["bytes"])

            temp_audio_path = f.name

        st.success("Recording completed")

        st.audio(temp_audio_path)

    # =========================
    # UPLOAD SECTION
    # =========================

    st.divider()

    st.markdown("## Upload Existing Audio")

    uploaded_file = st.file_uploader(
        "Upload audio file",
        type=["wav", "mp3"]
    )

    if uploaded_file:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as tmp:

            tmp.write(uploaded_file.read())

            temp_audio_path = tmp.name

        st.audio(temp_audio_path)

    # =========================
    # ANALYZE BUTTON
    # =========================

    if temp_audio_path:

        if st.button("🚀 Analyze Meeting"):

            # =========================
            # TRANSCRIBE
            # =========================

            with st.spinner("Transcribing audio..."):

                transcript = transcribe_audio(
                    temp_audio_path
                )

            st.success("Transcription completed")

            st.subheader("📝 Transcript")

            st.write(transcript)

            # =========================
            # AI ANALYSIS
            # =========================

            with st.spinner("Analyzing with DeepSeek AI..."):

                analysis = analyze_meeting(
                    transcript
                )

            st.success("AI analysis completed")

            st.subheader("🤖 AI Analysis")

            st.write(analysis)

            # =========================
            # SAVE HISTORY
            # =========================

            meeting_data = {
                "title": f"Meeting {datetime.now()}",
                "date": str(datetime.now()),
                "transcript": transcript,
                "analysis": analysis
            }

            st.session_state.history.append(
                meeting_data
            )

            # =========================
            # PDF EXPORT
            # =========================

            pdf_path = generate_pdf(
                meeting_data["title"],
                transcript,
                analysis
            )

            with open(pdf_path, "rb") as f:

                st.download_button(
                    "📄 Download PDF",
                    f,
                    file_name="meeting_summary.pdf",
                    mime="application/pdf"
                )

# =========================
# HISTORY PAGE
# =========================

elif page == "History":

    st.title("📚 Meeting History")

    if len(st.session_state.history) == 0:

        st.warning("No meeting history found.")

    else:

        for item in reversed(st.session_state.history):

            with st.expander(
                f"{item['title']} - {item['date']}"
            ):

                st.subheader("📝 Transcript")

                st.write(item["transcript"])

                st.subheader("🤖 Analysis")

                st.write(item["analysis"])
