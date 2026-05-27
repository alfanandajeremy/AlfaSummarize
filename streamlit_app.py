import streamlit as st
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment
import speech_recognition as sr

# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="AI Meeting Recorder",
    page_icon="🎤",
    layout="wide"
)

# =========================================
# DEEPSEEK API KEY
# =========================================

try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    st.error("DeepSeek API Key not configured")
    st.stop()

# =========================================
# DEEPSEEK CLIENT
# =========================================

deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# =========================================
# SESSION STATE
# =========================================

if "history" not in st.session_state:
    st.session_state.history = []

# =========================================
# FUNCTIONS
# =========================================

def convert_webm_to_wav(webm_bytes):

    # SAVE WEBM

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".webm"
    ) as webm_file:

        webm_file.write(webm_bytes)

        webm_path = webm_file.name

    # CONVERT TO WAV

    audio = AudioSegment.from_file(
        webm_path,
        format="webm"
    )

    wav_path = webm_path.replace(
        ".webm",
        ".wav"
    )

    audio.export(
        wav_path,
        format="wav"
    )

    return wav_path


def transcribe_audio(audio_path):

    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:

        audio_data = recognizer.record(source)

    text = recognizer.recognize_google(
        audio_data,
        language="id-ID"
    )

    return text


def analyze_meeting(transcript):

    prompt = f"""
    Analyze this meeting transcript.

    Generate:
    1. Executive Summary
    2. Key Discussion Points
    3. Decisions Made
    4. Action Items
    5. Risks Identified
    6. Recommendations
    7. Communication Insights

    Transcript:
    {transcript}
    """

    response = deepseek_client.chat.completions.create(
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

    # TITLE

    pdf.set_font("Arial", "B", 16)

    pdf.cell(
        200,
        10,
        txt=title,
        ln=True
    )

    # DATE

    pdf.set_font("Arial", size=12)

    pdf.cell(
        200,
        10,
        txt=f"Generated: {datetime.now()}",
        ln=True
    )

    pdf.ln(10)

    # TRANSCRIPT

    pdf.set_font("Arial", "B", 14)

    pdf.cell(
        200,
        10,
        txt="Transcript",
        ln=True
    )

    pdf.set_font("Arial", size=11)

    pdf.multi_cell(
        0,
        8,
        transcript
    )

    pdf.ln(5)

    # ANALYSIS

    pdf.set_font("Arial", "B", 14)

    pdf.cell(
        200,
        10,
        txt="AI Analysis",
        ln=True
    )

    pdf.set_font("Arial", size=11)

    pdf.multi_cell(
        0,
        8,
        analysis
    )

    filename = "meeting_summary.pdf"

    pdf.output(filename)

    return filename

# =========================================
# SIDEBAR
# =========================================

st.sidebar.title("AI Meeting Recorder")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Record Meeting",
        "History"
    ]
)

# =========================================
# DASHBOARD
# =========================================

if page == "Dashboard":

    st.title("🎤 AI Meeting Recorder & Analyzer")

    st.metric(
        "Total Meetings",
        len(st.session_state.history)
    )

    st.info(
        "Record or upload meeting audio to generate AI-powered meeting insights."
    )

    st.markdown("---")

    st.markdown("""
    ## Features

    ✅ Record directly from mobile/device  
    ✅ Upload audio files  
    ✅ Voice to text  
    ✅ DeepSeek AI analysis  
    ✅ Executive summary  
    ✅ Action items extraction  
    ✅ Recommendations  
    ✅ Export PDF  
    ✅ Meeting history  
    """)

# =========================================
# RECORD PAGE
# =========================================

elif page == "Record Meeting":

    st.title("🎙️ Record Meeting")

    # RECORD FROM DEVICE

    st.markdown("## Record From Device")

    audio = mic_recorder(
        start_prompt="▶️ Start Recording",
        stop_prompt="⏹️ Stop Recording",
        just_once=True,
        use_container_width=True
    )

    temp_audio_path = None

    # =====================================
    # RECORD RESULT
    # =====================================

    if audio:

        try:

            temp_audio_path = convert_webm_to_wav(
                audio["bytes"]
            )

            st.success("Recording completed")

            st.audio(
                audio["bytes"]
            )

        except Exception as e:

            st.error(
                f"Audio conversion failed: {str(e)}"
            )

    # =====================================
    # UPLOAD SECTION
    # =====================================

    st.divider()

    st.markdown("## Upload Existing Audio")

    uploaded_file = st.file_uploader(
        "Upload audio file",
        type=[
            "wav",
            "mp3",
            "webm",
            "m4a"
        ]
    )

    if uploaded_file:

        suffix = "." + uploaded_file.name.split(".")[-1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as tmp:

            tmp.write(uploaded_file.read())

            temp_audio_path = tmp.name

        st.audio(temp_audio_path)

    # =====================================
    # ANALYZE BUTTON
    # =====================================

    if temp_audio_path:

        if st.button("🚀 Analyze Meeting"):

            # =====================================
            # TRANSCRIPTION
            # =====================================

            with st.spinner("Converting voice to text..."):

                try:

                    transcript = transcribe_audio(
                        temp_audio_path
                    )

                except Exception as e:

                    st.error(
                        f"Transcription failed: {str(e)}"
                    )

                    st.stop()

            st.success("Voice to text completed")

            st.subheader("📝 Transcript")

            st.write(transcript)

            # =====================================
            # AI ANALYSIS
            # =====================================

            with st.spinner("Analyzing meeting with DeepSeek AI..."):

                try:

                    analysis = analyze_meeting(
                        transcript
                    )

                except Exception as e:

                    st.error(
                        f"AI analysis failed: {str(e)}"
                    )

                    st.stop()

            st.success("AI analysis completed")

            st.subheader("🤖 AI Analysis")

            st.write(analysis)

            # =====================================
            # SAVE HISTORY
            # =====================================

            meeting_data = {
                "title": f"Meeting {datetime.now()}",
                "date": str(datetime.now()),
                "transcript": transcript,
                "analysis": analysis
            }

            st.session_state.history.append(
                meeting_data
            )

            # =====================================
            # PDF EXPORT
            # =====================================

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

# =========================================
# HISTORY
# =========================================

elif page == "History":

    st.title("📚 Meeting History")

    if len(st.session_state.history) == 0:

        st.warning(
            "No meeting history found."
        )

    else:

        for item in reversed(
            st.session_state.history
        ):

            with st.expander(
                f"{item['title']} - {item['date']}"
            ):

                st.subheader("📝 Transcript")

                st.write(
                    item["transcript"]
                )

                st.subheader("🤖 Analysis")

                st.write(
                    item["analysis"]
                )
