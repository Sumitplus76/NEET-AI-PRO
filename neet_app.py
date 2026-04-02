import streamlit as st
from langchain_groq import ChatGroq
import json
import re
import time
import os
from fpdf import FPDF  # PDF generation ke liye

# --- 1. THE PREMIUM DOCTOR'S UI ---
st.set_page_config(page_title="NEET AI PRO v8", page_icon="🏥", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9 !important; }
    .main-header { color: #003366; text-align: center; font-size: 42px; font-weight: 900; margin-bottom: 5px; }
    .sub-header { color: #555; text-align: center; font-size: 16px; margin-bottom: 30px; }
    .q-card {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 40px;
        border-top: 5px solid #0056b3;
    }
    .q-text { color: #1a1a1a; font-size: 22px; font-weight: 700; line-height: 1.4; margin-bottom: 20px; }
    div[data-testid="stRadio"] > label { display: none; }
    div[data-testid="stRadio"] label p { color: #1a1a1a !important; font-weight: 600 !important; font-size: 16px !important; }
    .pyq-tag {
        background: linear-gradient(90deg, #ff8c00, #ffba00);
        color: white; padding: 4px 12px; border-radius: 5px; font-size: 13px; font-weight: bold; display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND SETUP ---
GROQ_API_KEY = "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"
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=GROQ_API_KEY, temperature=0.3)
MISTAKE_FILE = "mistake_notebook.json"

if 'quiz' not in st.session_state: st.session_state.quiz = []
if 'answers' not in st.session_state: st.session_state.answers = {}
if 'start_time' not in st.session_state: st.session_state.start_time = None

# --- FUNCTIONS ---
def save_mistake(question_obj):
    mistakes = []
    if os.path.exists(MISTAKE_FILE):
        with open(MISTAKE_FILE, "r") as f: mistakes = json.load(f)
    # Check for duplicates
    if not any(m['q'] == question_obj['q'] for m in mistakes):
        mistakes.append(question_obj)
        with open(MISTAKE_FILE, "w") as f: json.dump(mistakes, f)

def generate_pdf(quiz_data, topic):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"NEET Practice Paper: {topic}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    
    for i, item in enumerate(quiz_data):
        pdf.multi_cell(0, 10, txt=f"Q{i+1}: {item['q']}")
        pdf.cell(0, 10, txt=f"A) {item['a']}   B) {item['b']}", ln=True)
        pdf.cell(0, 10, txt=f"C) {item['c']}   D) {item['d']}", ln=True)
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

def get_questions(topic):
    prompt = f"""Act as a NEET Professor. Generate 30 MCQs for: {topic}. Include PYQs. Return ONLY raw JSON list with keys: q, a, b, c, d, ans, exp, year."""
    res = llm.invoke(prompt)
    clean = re.sub(r'```json|```', '', res.content).strip()
    return json.loads(clean)

# --- 3. UI ---
st.markdown("<div class='main-header'>🩺 NEET AI PRO v8</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Target: August 2026 | Sumit Sahu</div>", unsafe_allow_html=True)

# SIDEBAR: Mistake Notebook
with st.sidebar:
    st.header("📓 Mistake Notebook")
    if os.path.exists(MISTAKE_FILE):
        with open(MISTAKE_FILE, "r") as f:
            saved_mistakes = json.load(f)
            st.write(f"Total Backlogs: {len(saved_mistakes)}")
            if st.button("Clear Notebook 🗑️"):
                os.remove(MISTAKE_FILE)
                st.rerun()
            for m in saved_mistakes[-3:]: # Show last 3 mistakes
                st.info(f"Weak Point: {m['q'][:50]}...")
    else:
        st.write("No mistakes yet! Keep it up.")

# MAIN INPUT
topic = st.text_input("Enter Topic Name:", placeholder="e.g. Human Reproduction")

if st.button("Generate Paper (30 Qs) 💉"):
    with st.spinner("AI is analyzing PYQs..."):
        try:
            st.session_state.quiz = get_questions(topic)
            st.session_state.answers = {}
            st.session_state.start_time = time.time()
            st.rerun()
        except: st.error("AI Error. Try again.")

# --- 4. RENDER TEST ---
if st.session_state.quiz:
    # PDF Download Button
    pdf_bytes = generate_pdf(st.session_state.quiz, topic)
    st.download_button(label="📥 Download as PDF (OMR Practice)", data=pdf_bytes, file_name=f"NEET_{topic}.pdf", mime="application/pdf")
    
    st.write("---")
    for i, item in enumerate(st.session_state.quiz):
        st.markdown(f"<div class='q-card'>", unsafe_allow_html=True)
        if item.get('year') and item['year'] != "None":
            st.markdown(f"<span class='pyq-tag'>🔥 PYQ {item['year']}</span>", unsafe_allow_html=True)
        st.markdown(f"<div class='q-text'>{i+1}. {item['q']}</div>", unsafe_allow_html=True)
        
        opts = [f"A) {item['a']}", f"B) {item['b']}", f"C) {item['c']}", f"D) {item['d']}"]
        selection = st.radio(f"Q{i}", opts, index=None, key=f"quest_{i}")
        st.session_state.answers[i] = selection

        if selection:
            correct_letter = item['ans']
            if selection.startswith(correct_letter):
                st.success(f"✅ Correct! Answer: {correct_letter}")
            else:
                st.error(f"❌ Wrong! Correct Answer: {correct_letter}")
                save_mistake(item) # Auto-save to notebook
                st.info(f"💡 Explanation: {item['exp']}")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🏁 FINISH TEST"):
        elapsed = time.time() - st.session_state.start_time
        score = sum(1 for i, item in enumerate(st.session_state.quiz) if st.session_state.answers.get(i, "").startswith(item['ans']))
        st.header("📊 Final Report")
        st.metric("SCORE", f"{score}/30")
        st.metric("TIME", f"{int(elapsed//60)}m {int(elapsed%60)}s")
        st.balloons()