import streamlit as st
import tempfile
import os
import json
from datetime import datetime
from fpdf import FPDF
import speech_recognition as sr
from openai import OpenAI

st.set_page_config(
    page_title="AI Meeting Recorder",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 AI Meeting Recorder & Analyzer")

DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.title("Menu")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Upload Audio", "History"]
)

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language="id-ID")
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
            {"role": "system", "content": "You are an AI meeting analyst."},
            {"role": "user", "content": prompt},
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

    pdf.multi_cell(0, 10, f"Generated: {datetime.now()}")

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Transcript", ln=True)

    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, transcript)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "AI Analysis", ln=True)

    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, analysis)

    pdf_path = "meeting_summary.pdf"
    pdf.output(pdf_path)

    return pdf_path

if page == "Dashboard":
    st.subheader("Dashboard")

    st.metric("Total Meetings", len(st.session_state.history))

    st.info(
        "Upload meeting audio to generate transcript and AI insights."
    )

elif page == "Upload Audio":
    st.subheader("Upload Meeting Audio")

    uploaded_file = st.file_uploader(
        "Upload audio file",
        type=["wav", "mp3"]
    )

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_file.read())
            temp_audio_path = tmp.name

        st.audio(temp_audio_path)

        if st.button("Analyze Meeting"):
            with st.spinner("Transcribing audio..."):
                transcript = transcribe_audio(temp_audio_path)

            st.success("Transcription completed")

            st.subheader("Transcript")
            st.write(transcript)

            with st.spinner("Analyzing with DeepSeek AI..."):
                analysis = analyze_meeting(transcript)

            st.success("AI analysis completed")

            st.subheader("AI Analysis")
            st.write(analysis)

            meeting_data = {
                "title": uploaded_file.name,
                "date": str(datetime.now()),
                "transcript": transcript,
                "analysis": analysis
            }

            st.session_state.history.append(meeting_data)

            pdf_path = generate_pdf(
                uploaded_file.name,
                transcript,
                analysis
            )

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Download PDF",
                    f,
                    file_name="meeting_summary.pdf",
                    mime="application/pdf"
                )

elif page == "History":
    st.subheader("Meeting History")

    if len(st.session_state.history) == 0:
        st.warning("No meeting history found.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['title']} - {item['date']}"):
                st.subheader("Transcript")
                st.write(item["transcript"])

                st.subheader("Analysis")
                st.write(item["analysis"])
