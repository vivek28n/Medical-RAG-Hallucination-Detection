# 🩺 Medical RAG Hallucination Detection

A Retrieval-Augmented Generation (RAG) based Medical AI Assistant that answers questions from trusted medical guidelines while detecting hallucinations, providing confidence scores, and performing self-correction.

---

## 🎯 Project Objective

The goal of this project is to build an AI assistant that:

- Answers medical questions using trusted medical documents.
- Reduces hallucinations produced by Large Language Models.
- Provides confidence scores for answers.
- Detects answers that are not sufficiently supported by retrieved evidence.
- Performs self-correction when an answer is unreliable.

The system is designed around a Retrieval-Augmented Generation (RAG) pipeline so that responses can be grounded in trusted medical sources instead of relying only on the language model's internal knowledge.

---

## 👥 Team

- Vivek
- Mansi

### Work Division

**Vivek**
- Dataset collection and preparation
- Trusted source-document organization
- Dataset folder management
- Overall RAG pipeline review
- Documentation and integration
- Final testing

**Mansi**
- Coding after the current retrieval stage
- Mainly Google Colab notebook development
- LLM integration
- Hallucination detection
- Confidence scoring
- Self-correction
- Later coding/integration tasks

Dataset changes should only be made by Vivek or with Vivek's approval.

---

## 🛠️ Tech Stack

- Python
- Google Colab
- VS Code
- Git & GitHub
- LangChain
- Sentence Transformers
- FAISS
- PyMuPDF
- FastAPI
- React
- Tailwind CSS
- Gemini API

---

## 📁 Project Structure

```text
Medical-RAG-Hallucination-Detection/
│
├── assets/
│
├── backend/
│
├── dataset/
│   ├── raw/
│   │   └── niddk_guiding_principles_diabetes.pdf
│   └── .gitkeep
│
├── docs/
│   ├── PROJECT_PLAN.md
│   ├── ROADMAP.md
│   ├── TEAM_GUIDELINES.md
│   └── TEAM_HANDOFF.md
│
├── frontend/
│
├── models/
│
├── notebooks/
│   ├── Notebook_01_Project_Setup.ipynb
│   ├── Notebook_02_Environment_Setup.ipynb
│   └── Notebook_03_PDF_Text_Extraction.ipynb
│
├── outputs/
├── presentation/
├── research/
├── screenshots/
├── scripts/
├── tests/
├── vector_db/
│
├── .gitignore
├── LICENSE
└── README.md
📓 Notebook Workflow

The project is developed step-by-step through separate notebooks.

Notebook 01 — Project Setup
notebooks/Notebook_01_Project_Setup.ipynb

Handles the initial project setup and verifies the connection between the local project repository and GitHub.

Status

✅ Completed

Notebook 02 — Environment Setup
notebooks/Notebook_02_Environment_Setup.ipynb

Prepares and verifies the development environment.

Current setup includes:

Python environment verification
Operating system and machine verification
PyTorch verification
Google Colab environment setup
T4 GPU configuration
Required Python libraries
Library import testing
Environment compatibility checks
Status

✅ Completed

Notebook 03 — PDF Text Extraction & Retrieval
notebooks/Notebook_03_PDF_Text_Extraction.ipynb

This notebook implements the current document-processing and retrieval pipeline.

Current Workflow
Medical PDF
     ↓
PDF Text Extraction
     ↓
Text Cleaning
     ↓
Text Chunking
     ↓
Text Embeddings
     ↓
FAISS Vector Search
     ↓
Similarity Retrieval
Current Status

✅ PDF loading
✅ Text extraction
✅ Text cleaning
✅ Text chunking
✅ Embedding generation
✅ FAISS vector search
✅ Similarity retrieval

📊 Current Results
Source Document
dataset/raw/niddk_guiding_principles_diabetes.pdf

Current document:

Type: Medical diabetes guideline
Pages: 83
Processing Results
Total pages:          83
Total chunks:         277
Chunk size:           1000 characters
Chunk overlap:        200 characters
Embedding dimension:  384
Vector database:      FAISS
Retrieval status:     Successfully tested

Relevant chunks can currently be retrieved from the medical document based on similarity to a user query.

🧩 Current RAG Pipeline
1. Document Loading

The medical PDF is loaded from:

dataset/raw/niddk_guiding_principles_diabetes.pdf
2. Text Extraction

Text is extracted from the PDF using PyMuPDF.

3. Text Cleaning

Extracted text is cleaned to remove unnecessary formatting and improve the quality of retrieved content.

4. Text Chunking

The cleaned document is divided into smaller chunks using:

RecursiveCharacterTextSplitter

Current configuration:

chunk_size = 1000
chunk_overlap = 200

Current result:

277 chunks
5. Embedding Generation

Sentence-transformer embeddings are generated for each chunk.

Current embedding size:

384 dimensions
6. Vector Storage

FAISS is used for efficient similarity-based vector search.

7. Retrieval

When a query is provided, the system searches the vector index and retrieves the most relevant medical chunks.

The retrieval stage has been successfully tested with diabetes-related queries.

Retrieved results contain information such as:

Chunk ID
Page number
Distance / similarity
Retrieved text
🔍 Example Retrieval Topics

The current retrieval system can retrieve relevant sections discussing:

Diabetes introduction
Diabetes risk factors
Diabetes management
Blood glucose control
Physical activity
Cardiovascular disease risk factors
Diabetes prevention
Treatment principles
📚 Dataset

The current project uses a trusted medical guideline document related to diabetes.

Current source:

dataset/raw/niddk_guiding_principles_diabetes.pdf

The document contains:

83 pages

It is processed through the PDF extraction, cleaning, chunking and embedding pipeline before retrieval.

Dataset Responsibility

Dataset preparation and organization are handled separately from the main coding workflow.

Do not modify, rename or reorganize dataset files without coordination with the dataset owner.

🚀 Next Development Stage

The current FAISS retrieval layer is the foundation for the next stage.

The planned development flow is:

Existing FAISS Retrieval
        ↓
Retrieved Medical Context
        ↓
LLM Integration
        ↓
Grounded Answer Generation
        ↓
Evidence / Answer Comparison
        ↓
Hallucination Detection
        ↓
Confidence Score
        ↓
Self-Correction
        ↓
Backend Integration
        ↓
Frontend Integration
        ↓
Testing & Evaluation
🗺️ Development Roadmap
[✓] Project Setup
        ↓
[✓] Environment Setup
        ↓
[✓] GPU Configuration
        ↓
[✓] Medical PDF Added
        ↓
[✓] PDF Text Extraction
        ↓
[✓] Text Cleaning
        ↓
[✓] Text Chunking
        ↓
[✓] Embedding Generation
        ↓
[✓] FAISS Retrieval
        ↓
[ ] LLM Integration
        ↓
[ ] Medical Answer Generation
        ↓
[ ] Hallucination Detection
        ↓
[ ] Confidence Scoring
        ↓
[ ] Self-Correction
        ↓
[ ] Backend Integration
        ↓
[ ] Frontend Integration
        ↓
[ ] Testing & Evaluation
💻 Google Colab Setup

For a fresh Colab runtime, use a T4 GPU when required.

Clone Repository
!git clone https://github.com/vivek28n/Medical-RAG-Hallucination-Detection.git
%cd Medical-RAG-Hallucination-Detection

If the repository is already cloned:

%cd /content/Medical-RAG-Hallucination-Detection
Verify Repository
import os

print("Current directory:", os.getcwd())
print("Dataset exists:", os.path.exists("dataset"))
print("Raw folder exists:", os.path.exists("dataset/raw"))

if os.path.exists("dataset/raw"):
    print("Files:", os.listdir("dataset/raw"))

Expected file:

niddk_guiding_principles_diabetes.pdf
📦 Dependencies

For a fresh Colab runtime:

!pip install -q \
    langchain \
    langchain-community \
    langchain-text-splitters \
    faiss-cpu \
    sentence-transformers \
    pymupdf \
    pypdf \
    fastapi \
    uvicorn

Then verify imports:

import langchain
import faiss
import sentence_transformers
import fitz
import fastapi

print("Required libraries imported successfully!")

Install required packages before importing them.

⚠️ Common Errors
No module named 'fitz'

Install:

!pip install -q pymupdf

Then:

import fitz
No module named 'langchain_text_splitters'

Install:

!pip install -q langchain-text-splitters

Then:

from langchain_text_splitters import RecursiveCharacterTextSplitter
No module named 'faiss'

Install:

!pip install -q faiss-cpu

Then:

import faiss
PDF Not Found

Check:

import os

print(os.getcwd())
print(os.listdir("dataset/raw"))

Expected directory:

/content/Medical-RAG-Hallucination-Detection

Expected file:

dataset/raw/niddk_guiding_principles_diabetes.pdf

Do not add an extra .pdf to the filename.

🤝 Team Collaboration

The project uses Git and GitHub for version control.

Before starting a new coding session:

git pull --rebase origin main

After completing a meaningful change:

git status

Add only the required files:

git add <changed-files>

Commit:

git commit -m "Describe the change"

Before pushing:

git pull --rebase origin main

Then:

git push origin main
Important

Never use:

git push -f

If a merge or rebase conflict occurs, stop and coordinate with the other team member before resolving it.

🔐 Security

Never commit API keys, passwords, tokens or other secrets.

Do NOT write:

API_KEY = "actual-secret-key"

Use environment variables or Colab Secrets instead.

Example:

import os

API_KEY = os.environ.get("API_KEY")

Never commit:

.env
API keys
passwords
access tokens
private credentials
👩‍💻 Coding Rules for the Next Stage

The coding workflow should remain incremental.

Work in small notebook cells.
Run each cell before continuing.
Fix errors before moving forward.
Install missing packages before imports.
Reuse existing variables whenever possible.
Do not unnecessarily recreate the existing retrieval pipeline.
Do not change dataset paths without coordination.
Keep notebook code readable and maintainable.
Test important components before integration.
Do not blindly run all cells after an error.
📓 Future Notebook Organization

The next stages can be separated into notebooks such as:

Notebook_04_LLM_Integration.ipynb
Notebook_05_Hallucination_Detection.ipynb
Notebook_06_Confidence_Scoring.ipynb
Notebook_07_Self_Correction.ipynb

The exact notebook structure may be adjusted as development progresses.

📖 Team Handoff

Detailed instructions for continuing the project are available in:

docs/TEAM_HANDOFF.md

The handoff document contains:

Current project status
Colab setup
Dependency installation
Common error fixes
Git workflow
Work division
Coding rules
ChatGPT instructions for the coding workflow
Next development direction
🧠 ChatGPT Workflow for Coding

When working on the next stage, use ChatGPT as a step-by-step coding assistant.

The preferred workflow is:

One task
   ↓
One/few cells
   ↓
Run
   ↓
Check output
   ↓
Fix errors if needed
   ↓
Next task

Do not request or execute the entire project implementation at once.

When an error occurs, provide the complete error/output to ChatGPT and fix it before continuing.

🧪 Testing & Evaluation

Testing will be performed progressively as the system develops.

Planned evaluation areas include:

Retrieval relevance
Answer grounding
Hallucination detection
Confidence scoring
Self-correction
End-to-end response quality

The final system should be evaluated against trusted medical evidence rather than only judging whether an answer sounds plausible.

⚕️ Medical Disclaimer

This project is intended for research and educational purposes.

It is not a replacement for professional medical advice, diagnosis or treatment.

The system should use trusted medical sources as the basis for retrieval and answer generation.

🔮 Future Vision

The final system aims to provide a medical AI assistant that does more than simply generate an answer.

The intended workflow is:

User Question
      ↓
Retrieve Trusted Medical Evidence
      ↓
Generate Answer
      ↓
Check Answer Against Evidence
      ↓
Calculate Confidence
      ↓
Hallucination Detected?
    ↙       ↘
  YES        NO
   ↓          ↓
Self-Correct  Return Answer
   ↓
Final Verified Answer

The ultimate goal is to make generated medical responses more:

Grounded
Transparent
Reliable
Evidence-based
Resistant to hallucination
📌 Project Status

Current milestone:

PDF processing → chunking → embeddings → FAISS retrieval completed successfully.

Next milestone:

LLM integration and grounded medical answer generation.