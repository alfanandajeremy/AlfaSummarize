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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================
# MODERN UI CSS
# =========================================

st.markdown("""
<style>

/* Hide Streamlit Branding */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

/* App Background */

.stApp {
    background: #0f172a;
    color: white;
}

/* Main Container */

.block-container {
    padding-top: 1rem;
    padding-bottom: 6rem;
    max-width: 100%;
}

/* Typography */

h1 {
    font-size: 34px !important;
    font-weight: 800 !important;
    color: white !important;
}

h2, h3 {
    color: white !important;
}

/* Buttons */

.stButton button {
    width: 100%;
    border-radius: 16px;
    height: 52px;
    border: none;
    background: linear-gradient(
        135deg,
        #2563eb,
        #7c3aed
    );
    color: white;
    font-size: 16px;
    font-weight: 700;
}

/* Metric Cards */

[data-testid="metric-container"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 20px;
}

/* Expander */

.streamlit-expanderHeader {
    background: #1e293b;
    border-radius: 14px;
}

/* Inputs */

.stTextInput input {
    border-radius: 12px;
}

/* Hero Card */

.hero-card {
    padding: 28px;
    border-radius: 24px;
    background: linear-gradient(
        135deg,
        #2563eb,
        #7c3aed
    );
    margin-bottom: 24px;
}

/* Upload */

[data-testid="stFileUploader"] {
    background: #1e293b;
    border-radius: 18px;
    padding: 20px;
}

/* Mobile */

@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    h1 {
        font-size: 28px !important;
    }

}

</style>
""", unsafe_allow_html=True)

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
# AUDIO CONVERTER
# =========================================

def convert_audio_to_wav(input_path):

    audio = AudioSegment.from_file(input_path)

    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    wav_path = input_path + ".wav"

    audio.export(
        wav_path,
        format="wav"
    )

    return wav_path

# =========================================
# TRANSCRIPTION
# =========================================

def transcribe_audio(audio_path):

    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:

        audio_data = recognizer.record(source)

    text = recognizer.recognize_google(
        audio_data,
        language="id-ID"
    )

    return text

# =========================================
# AI ANALYSIS
# =========================================

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

# =========================================
# PDF GENERATOR
# =========================================

def generate_pdf(title, transcript, analysis):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 18)

    pdf.cell(
        200,
        10,
        txt=title,
        ln=True
    )

    pdf.set_font("Arial", size=12)

    pdf.cell(
        200,
        10,
        txt=f"Generated: {datetime.now()}",
        ln=True
    )

    pdf.ln(10)

    # Transcript

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

    # Analysis

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
# NAVIGATION
# =========================================

page = st.radio(
    "",
    ["🏠 Home", "🎙️ Record", "📚 History"],
    horizontal=True
)

# =========================================
# HOME
# =========================================

if page == "🏠 Home":

    st.markdown("""
    <div class="hero-card">
        <h1>🎤 AI Meeting Recorder</h1>
        <p>
        Record meetings, convert voice to text,
        analyze conversations with AI,
        and generate actionable insights.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Meetings",
            len(st.session_state.history)
        )

    with col2:

        st.metric(
            "AI Status",
            "Active"
        )

    st.markdown("---")

    st.subheader("Features")

    st.markdown("""
    ✅ Mobile recording  
    ✅ Upload audio  
    ✅ Voice to text  
    ✅ AI meeting summary  
    ✅ Action items extraction  
    ✅ Recommendations  
    ✅ Export PDF  
    ✅ Mobile-first UI  
    """)

# =========================================
# RECORD PAGE
# =========================================

elif page == "🎙️ Record":

    st.title("🎙️ Record Meeting")

    st.markdown("### Record from mobile/device")

    audio = mic_recorder(
        start_prompt="▶️ Start Recording",
        stop_prompt="⏹️ Stop Recording",
        just_once=True,
        use_container_width=True
    )

    temp_audio_path = None

    # =====================================
    # RECORDED AUDIO
    # =====================================

    if audio:

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".webm"
            ) as f:

                f.write(audio["bytes"])

                webm_path = f.name

            temp_audio_path = convert_audio_to_wav(
                webm_path
            )

            st.success("Recording completed")

            st.audio(audio["bytes"])

        except Exception as e:

            st.error(
                f"Audio conversion failed: {str(e)}"
            )

    # =====================================
    # FILE UPLOAD
    # =====================================

    st.markdown("---")

    st.markdown("### Upload Existing Audio")

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

        try:

            suffix = "." + uploaded_file.name.split(".")[-1]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as tmp:

                tmp.write(uploaded_file.read())

                original_path = tmp.name

            temp_audio_path = convert_audio_to_wav(
                original_path
            )

            st.audio(original_path)

        except Exception as e:

            st.error(
                f"Upload conversion failed: {str(e)}"
            )

    # =====================================
    # ANALYZE
    # =====================================

    if temp_audio_path:

        if st.button("🚀 Analyze Meeting"):

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

            with st.spinner("Analyzing with DeepSeek AI..."):

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
            # PDF
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

elif page == "📚 History":

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

                st.subheader("🤖 AI Analysis")

                st.write(
                    item["analysis"]
                )
