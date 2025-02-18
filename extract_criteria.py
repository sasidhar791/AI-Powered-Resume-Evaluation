from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import openai
import pypdf
import google.generativeai as genai
import threading
import uvicorn
import docx
import io

app = FastAPI()

# Set your OpenAI API key here
GOOGLE_GEMINI_API_KEY = "AIzaSyDOzVV6yB3TphbYsquFYQLFisum7g_nzJk"
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

# LLM function to extract criteria
def extract_criteria_from_text(text,tags=["skills", "certifications", "experience", "qualifications"]):
    """
    Extracts ranking criteria (skills, certifications, experience, qualifications) from a job description.

    **Input:**
    - **file (PDF/DOCX)**: Upload a job description in either PDF or DOCX format.

    **Output:**
    - Returns a **JSON list** of extracted criteria such as skills, certifications, experience, and qualifications.

    **Example Response:**
    ```json
    {
      "criteria": [
        "5+ years of experience in Python development",
        "Strong background in Machine Learning",
        "Must have certification XYZ"
      ]
    }
    ```
    """
    criteria = ''
    for tag in tags:
        criteria += f"{tag}:\n"
    
    
    prompt = f"""
    Given the following job description, extract key ranking criteria such as {criteria}.
    
    Job Description:
    {text}
    
    Return the response as a structured list of key criteria.
    """
    
    genai.configure(api_key=GOOGLE_GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-pro")
    response = gemini_model.generate_content(prompt)
    criteria = response.text    
    
    return criteria.split("\n")  # Convert response to a list

# API Endpoint
@app.post("/extract-criteria")
async def extract_criteria(file: UploadFile = File(...), tags: list[str] = []):
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file.file)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file.file.read())
    else:
        return {"error": "Unsupported file format. Upload PDF or DOCX."}
    
    criteria = extract_criteria_from_text(text, tags)

    return {"criteria": criteria}
