# 🩺 Medical RAG Hallucination Detection

A Retrieval-Augmented Generation (RAG) based Medical AI Assistant that answers questions from trusted medical guidelines while detecting hallucinations, providing confidence scores, and performing self-correction.

---

## 🎯 Project Objective

The goal of this project is to build an AI assistant that:

- Answers medical questions using trusted medical documents.
- Reduces hallucinations produced by Large Language Models.
- Provides confidence scores for every answer.
- Performs self-correction when an answer is unreliable.

The system is designed around a Retrieval-Augmented Generation (RAG) pipeline so that responses can be grounded in trusted medical sources instead of relying only on the language model's internal knowledge.

---

## 👥 Authors

- Vivek
- Mansi

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
│
├── presentation/
│
├── research/
│
├── screenshots/
│
├── scripts/
│
├── tests/
│
├── vector_db/
│
├── .gitignore
├── LICENSE
└── README.md
📓 Notebook Workflow

The project is being developed step-by-step through separate notebooks.

Notebook 01 — Project Setup

File:

notebooks/Notebook_01_Project_Setup.ipynb

This notebook handles the initial project setup and verifies the connection between the local project repository and GitHub.

Notebook 02 — Environment Setup

File:

notebooks/Notebook_02_Environment_Setup.ipynb

This notebook prepares and verifies the development environment.

Current setup includes:

Python environment verification.
Operating system and machine verification.
PyTorch verification.
Google Colab environment setup.
T4 GPU runtime configuration.
Required Python libraries installation.
Library import testing.
Environment compatibility checks.
Notebook 03 — PDF Text Extraction & Retrieval

File:

notebooks/Notebook_03_PDF_Text_Extraction.ipynb

This notebook implements the initial document-processing and retrieval pipeline.

Current workflow:

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
Current Results
Source document: Diabetes medical guideline PDF
Total pages: 83
Total text chunks: 277
Chunk size: 1000 characters
Chunk overlap: 200 characters
Embedding dimension: 384
FAISS-based similarity retrieval: Successfully tested

Relevant chunks can currently be retrieved from the medical document based on similarity to a query.

📚 Dataset

The current project uses a trusted medical guideline document related to diabetes.

Current Source
dataset/raw/niddk_guiding_principles_diabetes.pdf

The document contains 83 pages of diabetes-related medical guidance.

The document is processed through the PDF extraction pipeline before being used for retrieval.

🧩 Current RAG Pipeline

The current implementation follows these stages:

1. Document Loading

The medical PDF is loaded from the project's dataset directory.

2. Text Extraction

Text is extracted from the PDF using PyMuPDF.

3. Text Cleaning

Extracted text is cleaned to remove unnecessary formatting and improve the quality of the retrieved content.

4. Text Chunking

The cleaned document is divided into smaller chunks using:

RecursiveCharacterTextSplitter

Current configuration:

chunk_size = 1000
chunk_overlap = 200

This currently produces:

277 chunks
5. Embedding Generation

Sentence-transformer embeddings are generated for each chunk.

Current embedding size:

384 dimensions
6. Vector Storage

FAISS is used for efficient similarity-based vector search.

7. Retrieval

When a query is provided, the system searches the vector index and retrieves the most relevant medical chunks.

This retrieval stage has been successfully tested with diabetes-related queries.

🔍 Example Retrieval

The current retrieval system can return relevant sections from the medical guideline.

For example, diabetes-related queries can retrieve chunks discussing:

Diabetes introduction and risk factors.
Diabetes management.
Blood glucose control.
Physical activity.
Cardiovascular disease risk factors.
Diabetes prevention and treatment principles.

The retrieved results include metadata such as:

Chunk ID
Page Number
Distance / Similarity
Retrieved Text
🚧 Planned Components

The following components are part of the overall project objective and will be implemented in later stages:

Medical question answering.
LLM-based response generation.
Hallucination detection.
Answer confidence scoring.
Evidence-based answer verification.
Self-correction of unreliable responses.
API/backend integration.
Frontend interface.
End-to-end testing.
Evaluation of retrieval and answer quality.
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
💻 Development Workflow

The project uses Git and GitHub for version control.

Local Development
git clone https://github.com/vivek28n/Medical-RAG-Hallucination-Detection.git
cd Medical-RAG-Hallucination-Detection
Working with Changes

After making changes:

git status

Add the required files:

git add .

Commit the changes:

git commit -m "Describe your changes"

Pull the latest remote changes before pushing:

git pull --rebase origin main

Then push:

git push origin main

Always pull/rebase before pushing when working collaboratively to avoid overwriting changes made by another contributor.

📓 Running the Notebooks

The notebooks are designed to be executed sequentially.

Recommended order:

1. Notebook_01_Project_Setup.ipynb
2. Notebook_02_Environment_Setup.ipynb
3. Notebook_03_PDF_Text_Extraction.ipynb

Google Colab can be used for notebook execution and GPU-based workloads.

⚠️ Important Notes
Medical information retrieved by this project is intended for research and educational purposes.
The system should not be treated as a replacement for professional medical advice.
Trusted source documents should be used as the basis for retrieval.
API keys and other secrets must never be committed to GitHub.
Large generated files and temporary runtime files should not be committed unless required by the project.
Changes should be committed regularly with clear commit messages.
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

The ultimate goal is to make the generated medical responses more grounded, transparent, reliable, and resistant to hallucination.


