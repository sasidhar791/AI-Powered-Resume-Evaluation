from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from typing import List
import pypdf
import google.generativeai as genai
import docx
import io
import pandas as pd

app = FastAPI()

# Set your OpenAI API key here
GOOGLE_GEMINI_API_KEY = "add_your_google_gemini_api_key_here"
genai.configure(api_key=GOOGLE_GEMINI_API_KEY)

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = pypdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(io.BytesIO(file))
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Function to extract ranking criteria from a resume/job description
def extract_criteria_from_text(text):
    prompt = f"""
    Given the following text (job description or resume), extract key ranking criteria such as skills, certifications, experience, and qualifications.
    Include only 5 important criteria for ranking candidates. DO not include more than 5 criteria.
    Text:
    {text}
    
    Return the response as a structured list of key criteria.
    """
    gemini_model = genai.GenerativeModel("gemini-pro")
    response = gemini_model.generate_content(prompt)
    criteria = response.text.strip().split("\n")
    return criteria

# Function to score a resume against extracted criteria
def score_resume(text, criteria):
    scores = {criterion: 0 for criterion in criteria}
    total_score = 0

    for criterion in criteria:
        # Simple scoring: Check if criterion words appear in the text
        score = sum(1 for word in criterion.split() if word.lower() in text.lower())  # Basic word match
        scores[criterion] = min(score, 5)  # Cap the score at 5
        total_score += scores[criterion]

    return scores, total_score

# API Endpoint for scoring multiple resumes (with automatic criteria extraction)
@app.post("/score-resumes")
async def score_resumes(files: List[UploadFile] = File(...)):
    results = []

    if not files:
        return {"error": "No files uploaded"}

    # Extract text from the first resume to generate criteria
    first_file = files.pop(0)
    if first_file.filename.endswith(".pdf"):
        reference_text = extract_text_from_pdf(first_file.file)
    elif first_file.filename.endswith(".docx"):
        reference_text = extract_text_from_docx(first_file.file.read())
    else:
        return {"error": "Unsupported file format. Upload PDF or DOCX."}
    
    # Extract ranking criteria automatically
    criteria = extract_criteria_from_text(reference_text)
    
    for file in files:
        if file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(file.file)
        elif file.filename.endswith(".docx"):
            text = extract_text_from_docx(file.file.read())
        else:
            continue  # Skip unsupported files

        # Score the resume against extracted criteria
        scores, total_score = score_resume(text, criteria)

        # Extract candidate name (assuming filename represents name)
        candidate_name = file.filename.replace(".pdf", "").replace(".docx", "")

        # Append result
        results.append({
            "Candidate Name": candidate_name,
            **scores,
            "Total Score": total_score
        })

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Save as Excel file
    output_file = "scored_resumes.xlsx"
    df.to_excel(output_file, index=False)

    # Return the file for download
    return FileResponse(output_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=output_file)
