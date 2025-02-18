# 📄 Resume Ranking API (Extract Criteria & Score Resumes)

This API provides two main functionalities:
1. **Extract Criteria** - Extracts key ranking criteria (skills, certifications, experience) from a job description file (PDF or DOCX).
2. **Score Resumes** - Scores multiple resumes against the extracted ranking criteria and generates an Excel report.

---

##  **1. Installation and Setup**

### **1.1 Prerequisites**
- Python **3.8+**
- An API key for **Google Gemini** ([Get it here](https://ai.google.dev/))
- `pip` installed


###  **1.2. Clone the Repository**
To get started, clone this repository using:
```bash
git clone https://github.com/your-username/resume-ranking-api.git
cd resume-ranking-api
```

### **1.3 Install Dependencies**
Run the following command to install all required libraries:
```bash
pip install -r requirements.txt
```

### **1.4 Set API key**
Add API key in both the scripts,
```bash
# Set your OpenAI API key here
GOOGLE_GEMINI_API_KEY = "add_your_google_gemini_api_key_here"
```

## **2. Run the API**
For extracting criteria task,
```bash
uvicorn extract_criteria:app
```

For scoring resume task,
```bash
uvicorn score_resume:app
```

The API will start at: http://127.0.0.1:8000

Swagger UI available at: http://127.0.0.1:8000/docs


## **3. API endpoints**

### **3.1 Extracts ranking criteria from a job description**
Endpoint:
```bash
POST /extract-criteria
```


Note that here if user doesn't provide desired criteria for ranking, implicitly criteria will be taken as "skills", "certifications", "experience", "qualifications".

Request Example (Using cURL):
```bash
curl -X POST "http://127.0.0.1:8000/extract-criteria" \
  -F "file=@job_description.pdf" \
  -F "tags=experience" \
  -F "tags=skills" \
  -F "tags=certification"
```

Response example:
```bash
{
  "criteria": [
    "5+ years of experience in Python",
    "Strong background in Machine Learning",
    "Must have certification XYZ"
  ]
}
```

### **3.2 Score resume based on Job description**
Endpoint:
```bash
POST /score-resumes
```


Scores multiple resumes against the extracted ranking criteria and returns an Excel report.

Request Example (Using cURL):
```bash
curl -X POST "http://127.0.0.1:8000/score-resumes" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx"
```

Response:
📥 A downloadable Excel file (scored_resumes.xlsx) containing candidate scores.


Example Excel output:

| **Candidate Name**    | **Python Experience** | **Machine Learning** | **Certification XYZ** | **Total Score** |
|-----------------------|-----------------------|----------------------|------------------------|-----------------|
| John Doe             | 5                     | 4                    | 3                      | 12              |
| Jane Smith           | 4                     | 3                    | 4                      | 11              |
| Alan Brown           | 3                     | 5                    | 3                      | 11              |





