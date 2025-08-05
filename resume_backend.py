from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import openai
import tempfile
import docx
import os

app = FastAPI()

# CORS to allow requests from your Shopify frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your OpenAI API Key here
openai.api_key = "YOUR_OPENAI_API_KEY"

def extract_text_from_resume(file: UploadFile) -> str:
    suffix = file.filename.split(".")[-1].lower()
    temp = tempfile.NamedTemporaryFile(delete=False, suffix="." + suffix)
    temp.write(file.file.read())
    temp.close()

    text = ""
    if suffix == "pdf":
        import pdfplumber
        with pdfplumber.open(temp.name) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif suffix in ["doc", "docx"]:
        doc = docx.Document(temp.name)
        text = "\n".join([p.text for p in doc.paragraphs])
    
    os.unlink(temp.name)
    return text

def generate_ai_response(resume_text: str) -> dict:
    prompt = f"""
You are a resume assistant. Based on the following resume text:

\"\"\"{resume_text}\"\"\"

1. Identify missing skills or areas of improvement.
2. Recommend 3 job roles with title, company, location, and link.
3. Recommend 3 online courses to cover the gaps with name, platform, price, and link.
Return response in JSON format like:
{{
  "gaps": ["Skill A", "Skill B"],
  "jobs": [{{"title": "", "company": "", "location": "", "link": ""}}, ...],
  "courses": [{{"name": "", "platform": "", "price": "", "link": ""}}, ...]
}}
"""

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    
    import json
    response = completion.choices[0].message["content"]
    
    try:
        parsed = json.loads(response)
        return parsed
    except:
        return {"error": "AI response was not in correct format", "raw": response}

@app.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    resume_text = extract_text_from_resume(file)
    result = generate_ai_response(resume_text)
    return result
