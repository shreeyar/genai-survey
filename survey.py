import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import csv
import io

# -------------------------
# App configuration & styles
# -------------------------
st.set_page_config(page_title="SoM AI First Learning Interests & Readiness Survey", page_icon="📝", layout="centered")

BRAND_CSS = """
<style>
:root {
  --brand: #0f62fe;
  --brand-dark: #0043ce;
  --bg: #fafafa;
  --border: #e0e0e0;
  --text: #161616;
  --muted: #6f6f6f;
  --danger: #da1e28;
  --success: #198038;
}
html, body, [class*="css"]  {
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}
.container-like {
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  padding: 16px 20px;
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.intro { color: var(--muted); margin-bottom: 12px; }
.hr { height: 1px; background: var(--border); margin: 16px 0; }
.required { color: var(--danger); margin-left: 4px; }
.success { color: var(--success); font-weight: 600; }
.error { color: var(--danger); font-weight: 600; }
.help { color: var(--muted); font-size: 0.9rem; }
.small { font-size: 0.92rem; color: var(--muted); margin-top: -6px; }
</style>
"""
st.markdown(BRAND_CSS, unsafe_allow_html=True)

# -------------------------
# Constants
# -------------------------
CSV_PATH = Path("SoM_GenAI_Survey.csv")

TOOLS_OPTIONS = [
    "ChatGPT",
    "GPS Sidekick",
    "Microsoft Copilot",
    "Google Gemini",
    "Claude",
    "Other (please specify)",
    "None yet",
]

ROLE_OPTIONS = [
    "Developer",
    "Business Analyst",
    "Tester/QA",
    "Project Manager",
    "Design/UX",
    "Leadership/People Manager",
    "Organizational Change Management",
    "Other",
]

FORMATS_OPTIONS = [
    "Live demo + Q&A (60–90 min)",
    "Hands-on lab with guided exercises",
    "Office hours / coaching",
    "Self-paced materials and quick reference guides",
    "Show-and-tell of internal use cases",
]

COMFORT_OPTIONS = [
    "1 – New to AI (need basics)",
    "2 – Some exposure",
    "3 – Comfortable with common tools",
    "4 – Confident (use AI regularly)",
    "5 – Advanced (build/evaluate AI solutions)",
]

FREQ_OPTIONS = ["Daily", "Weekly", "Monthly", "Rarely", "Never"]

LEARNING_INTERESTS_OPTIONS = [
    "Everyday productivity with AI (Copilot, ChatGPT/Sidekick)",
    "Find and use the right information (RAG, vector search)",
    "Agentic AI and workflows (AI “agents” that plan and take multi-step actions)",
    "Build AI-powered apps and integrations (APIs, function calling, connecting tools)",
    "Safe and responsible AI (security, privacy, governance)",
    "Other (please specify)",
]

# Output schema columns
COLUMNS = [
    "timestamp","comfort","tools_used","tools_used_other","tools_used_other_optional",
    "role","role_other","learning_interests","learning_interests_other","implementation_idea_flag",
    "implementation_idea_text","session_formats"
]

# -------------------------
# Utilities: CSV append + load
# -------------------------
def append_row_to_csv(row: dict):
    record = {c: row.get(c, "") for c in COLUMNS}
    is_new = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if is_new:
            w.writeheader()
        w.writerow(record)

def df_current() -> pd.DataFrame:
    if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
        try:
            return pd.read_csv(CSV_PATH)
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

# -------------------------
# UI
# -------------------------
st.markdown('<div class="container-like">', unsafe_allow_html=True)
st.title("SoM GenAI Learning Interests & Readiness Survey")
st.markdown(
    '<p class="intro">Take a quick (3–5 minute) survey to help us design GenAI learning that’s most useful for you! <br> Fun Fact: We used Sidekick to build this survey in just 5 hours! </p>',
    unsafe_allow_html=True,
)

with st.form("survey_form", clear_on_submit=True):
    # Consent
    consent = st.radio("Consent to proceed?*", options=["Yes, continue", "No, exit survey"], horizontal=True, index=0)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    
    # Q1 Comfort
    comfort = st.selectbox("Q1. How comfortable are you with using AI?*", options=["Select one"] + COMFORT_OPTIONS)

    # Q2 Tools
    tools = st.multiselect("Q2. Which AI tools have you used? Select all that apply.*", TOOLS_OPTIONS)
    tools_other = ""
    if "None yet" in tools and len(tools) > 1:
        tools = ["None yet"]
    if "Other (please specify)" in tools:
        tools_other = st.text_input("Please specify other tool(s)")
    # Optional field to capture any additional AI tool(s) we missed
    tools_other_optional = st.text_input(
        "OPTIONAL: Add any AI tool not listed",
        key="tools_other_optional",
        placeholder="e.g., Claude Code, Canva AI, Grok",
    )

    # Q3 Role + optional free text always visible
    role = st.selectbox(
        "Q3. What is your primary role?*",
        options=["Select one"] + [
            "Developer","Business Analyst","Tester/QA","Project Manager","Design/UX",
            "Leadership/People Manager","Organizational Change Management","Other",
        ],
        key="role_select",
    )
    role_other = st.text_input(
        "OPTIONAL: Add a role not listed",
        key="role_other_text",
        placeholder="e.g., Data Engineer, Scrum Master",
    )
    
    # Q4 Interests
    learning = st.multiselect(
        "Q4. What do you want to learn more about regarding AI? Select up to 3 topics.*",
        options=LEARNING_INTERESTS_OPTIONS,
    )
    learning_other = ""
    if "Other (please specify)" in learning:
        learning_other = st.text_input("Other interest (short)")

    # NEW: Always-visible optional textbox under Q4
    learning_other_optional = st.text_input(
        "OPTIONAL: If there is a topic that was not listed, please list it here",
        key="learning_other_optional",
        placeholder="e.g., AI for data governance, AI for portfolio planning",
    )

    # Q5 Implementation ideas
    idea_flag = st.radio(
        "Q5. Do you already have an idea to apply AI in your role?*",
        options=["Yes", "Not yet"],
        horizontal=True,
        key="q5_flag",
    )
    idea_text = st.text_area(
        "OPTIONAL: If you have an idea, describe it briefly",
        key="q5_text",
        max_chars=300,
        height=90,
        placeholder="e.g., Use AI to auto-summarize test results to reduce reporting time by 30%...",
    )
    
    # Q6 Session formats
    formats = st.multiselect("Q6. Which session formats would be most helpful? Select all that apply.*", [
        "Live demo + Q&A (60–90 min)",
        "Hands-on lab with guided exercises",
        "Office hours / coaching",
        "Self-paced materials and quick reference guides",
        "Show-and-tell of internal use cases",
    ])

    # Submit button
    submitted = st.form_submit_button("Submit response")

# -------------------------
# Validation & Submission
# -------------------------
status_area = st.empty()

def required_field_checks():
    if consent != "Yes, continue":
        return False, "Please provide consent to proceed."
    if comfort == "Select one":
        return False, "Please select your comfort level for Q1."
    if len(tools) == 0:
        return False, "Please select at least one tool option for Q2."
    if role == "Select one":
        return False, "Please select your role for Q3."
    if not learning:
        return False, "Please select at least one topic for Q5."
    if len(learning) > 3:
        return False, "Please select up to 3 topics for Q5."
    if "Other (please specify)" in learning and not (learning_other or "").strip():
        return False, "Please type a short topic for Q5."
    if idea_flag == "Yes" and not (idea_text or "").strip():
        return False, "Please describe your implementation idea for Q5."
    return True, ""

if submitted:
    ok, msg = required_field_checks()
    if not ok:
        status_area.markdown(f'<p class="error">{msg}</p>', unsafe_allow_html=True)
    else:
        selected_topics = [t for t in learning if t != "Other (please specify)"]

        # Combine conditional "Other" and the always-optional free text, separated by "; "
        # This preserves your existing learning_interests_other usage and appends the optional field if provided.
        others_list = []
        if "Other (please specify)" in learning and (learning_other or "").strip():
            others_list.append((learning_other or "").strip())
        if (learning_other_optional or "").strip():
            others_list.append((learning_other_optional or "").strip())
        learning_interests_other_combined = "; ".join(others_list)

        row = {
            "timestamp": datetime.now(ZoneInfo("America/Detroit")).strftime("%Y-%m-%d %H:%M:%S"),
            "comfort": comfort,
            "tools_used": "; ".join(tools),
            "tools_used_other": (tools_other or "").strip() if "Other (please specify)" in tools else "",
            "tools_used_other_optional": (tools_other_optional or "").strip(),
            "role": role,
            "role_other": (role_other or "").strip(),
            "learning_interests": "; ".join(selected_topics),
            "learning_interests_other": learning_interests_other_combined,
            "implementation_idea_flag": idea_flag,
            "implementation_idea_text": (idea_text or "").strip() if idea_flag == "Yes" else "",
            "session_formats": "; ".join(formats),
        }
        try:
            append_row_to_csv(row)
            status_area.markdown('<p class="success">Response recorded. Thank you! </p>', unsafe_allow_html=True)
        except Exception as e:
            status_area.markdown(f'<p class="error">Could not save your response: {e}</p>', unsafe_allow_html=True)

# -------------------------
# Downloads and live view
# -------------------------
st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
st.subheader("Responses")

current_df = df_current()
st.caption("Live responses (from CSV):")
st.dataframe(
    current_df,
    use_container_width=True,
    hide_index=True,
    height=800  # lets you see many more rows at once
)

csv_buf = io.StringIO()
current_df.to_csv(csv_buf, index=False)
st.download_button(
    "Download CSV",
    data=csv_buf.getvalue(),
    file_name=CSV_PATH.name,
    mime="text/csv",
)

st.markdown("</div>", unsafe_allow_html=True)
