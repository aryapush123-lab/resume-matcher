# ============================================
# AI Resume Screening & Job Matching System
# VERSION 4 - Final version (chart, CSV download, explanations)
# ============================================
# What is new in Version 4:
#   1. A bar chart that compares the scores of all candidates.
#   2. A button to download the ranking as a CSV file (opens in Excel).
#   3. A "Verdict" for every candidate (Strong / Moderate / Low match).
#   4. A "How does this work?" section on the page - useful for your demo.
#   5. Results stay on the screen after you click the download button.
#
# Scoring: 70% skill match + 30% overall text match.

import csv                      # Lets us create a CSV file
import io                       # Holds the CSV text in memory
import re                       # Helps us search for exact words in text
import pandas as pd             # Tables of data (installed together with Streamlit)
import streamlit as st          # Builds the website UI
import PyPDF2                   # Reads text from PDF resumes
from sklearn.feature_extraction.text import TfidfVectorizer  # Converts text to numbers
from sklearn.metrics.pairwise import cosine_similarity        # Compares two texts


# ============================================
# PART A: The skills database
# ============================================
# Format:  "Skill name shown on screen": ["words to look for in the text"]
# A skill can have more than one way of being written (called "aliases").
# You can ADD your own skills here anytime - this is the easiest way to
# improve your project!

SKILLS = {
    # Programming languages
    "Python": ["python"],
    "Java": ["java"],
    "Kotlin": ["kotlin"],
    "Spring Boot": ["spring boot", "springboot"],
    "JavaScript": ["javascript", "js"],
    "C++": ["c++"],
    "C#": ["c#"],
    "SQL": ["sql", "mysql", "postgresql", "sqlite"],
    "TypeScript": ["typescript"],

    # Web development
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "React": ["react", "reactjs", "react.js"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "Flask": ["flask"],
    "Django": ["django"],
    "Streamlit": ["streamlit"],
    "REST API": ["rest api", "restful", "rest apis"],

    # Data and AI
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Data Visualization": ["data visualization", "matplotlib", "tableau", "power bi"],

    # Tools
    "Git": ["git", "github", "gitlab"],
    "Docker": ["docker"],
    "Linux": ["linux"],
    "AWS": ["aws", "amazon web services"],
    "MongoDB": ["mongodb"],

    # CS fundamentals
    "Data Structures": ["data structures", "dsa"],
    "Algorithms": ["algorithms"],
    "OOP": ["oop", "object oriented", "object-oriented"],

    # Soft skills
    "Communication": ["communication"],
    "Teamwork": ["teamwork", "team player", "work in a team", "collaboration"],
    "Problem Solving": ["problem solving", "problem-solving"],
    "Leadership": ["leadership"],
}


# ============================================
# PART B: Functions (the "brain" of the project)
# ============================================

def extract_text_from_pdf(uploaded_file):
    """Reads a PDF and returns all the text inside it."""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        # Some pages return nothing, so we use "or ''" to avoid errors
        text += (page.extract_text() or "") + "\n"
    return text


def find_skills(text):
    """
    Looks through the text and returns the set of skills found in it.

    We search for whole words only. For example, the skill "java" should be
    found in "I know Java" but NOT inside "JavaScript".
    """
    text = text.lower()
    # Turn line breaks and extra spaces into single spaces, so that
    # "machine\nlearning" (split across two lines) is still found.
    text = re.sub(r"\s+", " ", text)
    found = set()

    for skill_name, aliases in SKILLS.items():
        for alias in aliases:
            # The pattern means: the alias must NOT have a letter/number
            # right before it or right after it.
            pattern = r"(?<![a-z0-9+#])" + re.escape(alias) + r"(?![a-z0-9+#])"
            if re.search(pattern, text):
                found.add(skill_name)
                break  # skill found, no need to check its other aliases

    return found


def calculate_text_similarity(resume_text, job_description):
    """
    TF-IDF + cosine similarity (the same idea as Version 1).
    Returns how similar the two texts are overall (0 to 100).
    """
    documents = [resume_text, job_description]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return round(float(similarity[0][0]) * 100, 2)


def analyze_match(resume_text, job_description):
    """
    Analyzes ONE resume against the job description.
    Returns everything in one dictionary.
    """
    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_description)

    matched = sorted(resume_skills & job_skills)   # in BOTH resume and job
    missing = sorted(job_skills - resume_skills)   # job wants it, resume lacks it
    extra = sorted(resume_skills - job_skills)     # resume has it, job didn't ask

    text_score = calculate_text_similarity(resume_text, job_description)

    if len(job_skills) > 0:
        skill_score = round(len(matched) / len(job_skills) * 100, 2)
        final_score = round(0.7 * skill_score + 0.3 * text_score, 2)
    else:
        # The job description had no skills we recognise
        skill_score = None
        final_score = text_score

    return {
        "final_score": final_score,
        "skill_score": skill_score,
        "text_score": text_score,
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "job_skill_count": len(job_skills),
    }


def rank_resumes(resumes, job_description):
    """
    'resumes' is a list of (file_name, resume_text) pairs.
    We analyze each one, then sort so the BEST score comes first.
    """
    results = []
    for file_name, resume_text in resumes:
        result = analyze_match(resume_text, job_description)
        result["name"] = file_name
        results.append(result)

    # Sort from highest final score to lowest
    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results


def get_verdict(score):
    """NEW in Version 4: turns a score into a simple label."""
    if score >= 70:
        return "Strong match"
    elif score >= 40:
        return "Moderate match"
    else:
        return "Low match"


def build_ranking_table(ranked, include_skills=False):
    """
    NEW in Version 4: turns the ranked results into a table (a list of rows).
    On the screen we show a short table. For the CSV download we also
    include the skill names (include_skills=True).
    """
    table = []
    for position, r in enumerate(ranked, start=1):
        row = {
            "Rank": position,
            "Resume": r["name"],
            "Final Score (%)": r["final_score"],
            "Skill Match (%)": r["skill_score"] if r["skill_score"] is not None else "N/A",
            "Text Similarity (%)": r["text_score"],
            "Skills Matched": len(r["matched"]),
            "Skills Missing": len(r["missing"]),
            "Verdict": get_verdict(r["final_score"]),
        }
        if include_skills:
            row["Matched Skills"] = "; ".join(r["matched"])
            row["Missing Skills"] = "; ".join(r["missing"])
        table.append(row)
    return table


def table_to_csv(table):
    """NEW in Version 4: turns the table into CSV text for the download button."""
    buffer = io.StringIO()
    if table:
        writer = csv.DictWriter(buffer, fieldnames=list(table[0].keys()))
        writer.writeheader()
        writer.writerows(table)
    return buffer.getvalue()


# ============================================
# PART C: The website interface
# ============================================

st.set_page_config(page_title="Resume Matcher", page_icon="📄", layout="centered")

st.title("📄 AI Resume Screening & Job Matching System")
st.write("Upload one or more resumes and paste a job description. The app finds "
         "the skills in each resume and ranks the candidates from best to worst.")

# ---- Explanation section (great for your demo / viva) ----
with st.expander("ℹ️ How does this work?"):
    st.markdown(
        """
**Step 1 - Read:** the text is taken out of every PDF resume.

**Step 2 - Find skills:** the app looks for known skills (like Python, SQL, Git)
in the resume and in the job description. It matches whole words only, so
"Java" is not found inside "JavaScript".

**Step 3 - Score each resume:**
- **Skill Match** = skills the resume has that the job asks for, divided by all
  skills the job asks for.
- **Text Similarity** = how close the two texts are overall (TF-IDF and
  cosine similarity).
- **Final Score** = 70% Skill Match + 30% Text Similarity.

**Step 4 - Rank:** resumes are sorted from the highest final score to the lowest.

**Verdict:** 70% or more is a *Strong match*, 40% to 69% is *Moderate*,
below 40% is *Low*.
        """
    )

with st.expander(f"📋 Skills this app can recognise ({len(SKILLS)})"):
    st.write(", ".join(sorted(SKILLS.keys())))

# ---- Inputs ----
uploaded_resumes = st.file_uploader(
    "Upload Resumes (PDF only - you can select many at once)",
    type=["pdf"],
    accept_multiple_files=True,
)
job_description = st.text_area("Paste Job Description Here", height=200)

# ---- When the button is clicked: do the work and SAVE the results ----
# We save the results in st.session_state so they stay on the screen even
# after the page refreshes (for example when you click the download button).
if st.button("Rank Resumes"):

    if uploaded_resumes and job_description.strip() != "":

        resumes = []      # list of (file name, text) for readable PDFs
        unreadable = []   # names of PDFs we could not read

        with st.spinner("Analyzing..."):
            for pdf_file in uploaded_resumes:
                try:
                    text = extract_text_from_pdf(pdf_file)
                except Exception:
                    text = ""

                if text.strip() == "":
                    unreadable.append(pdf_file.name)
                else:
                    resumes.append((pdf_file.name, text))

            ranked = rank_resumes(resumes, job_description)

        if ranked:
            st.session_state["results"] = {
                "ranked": ranked,
                "job_skills": sorted(find_skills(job_description)),
                "unreadable": unreadable,
            }
        else:
            st.session_state["results"] = None
            st.error("None of the uploaded PDFs could be read. They may be scanned "
                     "images. Please use PDFs where you can select the text.")

    else:
        st.session_state["results"] = None
        st.error("Please upload at least one resume AND paste a job description first.")

# ---- Show the saved results ----
results = st.session_state.get("results")

if results:
    ranked = results["ranked"]

    st.caption("Showing results from the last time you clicked 'Rank Resumes'.")

    # PDFs we had to skip
    if results["unreadable"]:
        st.warning("Could not read text from: " + ", ".join(results["unreadable"]) +
                   ". They may be scanned images.")

    # Skills the job is asking for
    if results["job_skills"]:
        st.markdown("**Skills found in the job description:** " +
                    ", ".join(results["job_skills"]))
    else:
        st.info("No known skills were found in the job description, so only "
                "text similarity was used. Try a more detailed job description.")

    # Best candidate
    best = ranked[0]
    st.success(f"🏆 Best match: {best['name']} ({best['final_score']}%)")

    # Ranking table
    st.subheader("Ranking")
    st.dataframe(build_ranking_table(ranked), hide_index=True)

    # Bar chart (we add the rank to each name so every bar has a unique label)
    st.subheader("Score comparison")
    chart_data = pd.DataFrame(
        {"Final Score (%)": [r["final_score"] for r in ranked]},
        index=[f"#{i} {r['name']}" for i, r in enumerate(ranked, start=1)],
    )
    st.bar_chart(chart_data)

    # CSV download
    csv_text = table_to_csv(build_ranking_table(ranked, include_skills=True))
    st.download_button(
        label="⬇️ Download ranking as CSV",
        data=csv_text,
        file_name="resume_ranking.csv",
        mime="text/csv",
    )

    # Details for each resume
    st.subheader("Details for each resume")
    for position, r in enumerate(ranked, start=1):
        label = f"#{position}  {r['name']} - {r['final_score']}%  ({get_verdict(r['final_score'])})"
        with st.expander(label, expanded=(position == 1)):
            st.progress(min(int(r["final_score"]), 100))

            st.markdown("**✅ Matched skills**")
            st.write(", ".join(r["matched"]) if r["matched"] else "None")

            st.markdown("**❌ Missing skills**")
            st.write(", ".join(r["missing"]) if r["missing"]
                     else "None. This resume covers every skill in the job description!")

            st.markdown("**➕ Extra skills** (in resume, not requested by the job)")
            st.write(", ".join(r["extra"]) if r["extra"] else "None")
