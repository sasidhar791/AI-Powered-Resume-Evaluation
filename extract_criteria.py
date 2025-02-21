from fastapi import FastAPI, File, UploadFile
import pypdf
import google.generativeai as genai
import docx
import io
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

app = FastAPI()

# Set your OpenAI API key here
GOOGLE_GEMINI_API_KEY = "add_your_google_gemini_api_key_here"
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_GEMINI_API_KEY)

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = pypdf.PdfReader(file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(io.BytesIO(file))
    return "\n".join([para.text for para in doc.paragraphs])
    

# LLM function to extract criteria
def extract_criteria_from_text(text,tags=["skills", "certifications", "experience", "qualifications"]):
   
    criteria = ", ".join(tags)        
    
    prompt_template = PromptTemplate(   
    input_variables=["criteria", "job_description"], 
    template="Extract key ranking criteria like {criteria} from this job description:\n{job_description}"
)

    llm_chain = LLMChain(llm = llm,prompt = prompt_template)
    response = llm_chain.run(job_description=text,criteria=criteria)
    return response.split("\n")  # Convert response to a list


# API Endpoint
@app.post("/extract-criteria")
async def extract_criteria(file: UploadFile = File(...), tags: list[str] = []):
    if file.filename.endswith(".pdf"):        
        text = extract_text_from_pdf(file.file)        
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file.file)#.read()
    else:
        return {"error": "Unsupported file format. Upload PDF or DOCX."}
    
    criteria = extract_criteria_from_text(text, tags)

    return {"criteria": criteria}
