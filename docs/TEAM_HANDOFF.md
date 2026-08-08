# 🤝 Team Handoff — Vivek & Mansi

## 1. Project Goal

Build a medical Retrieval-Augmented Generation (RAG) assistant that retrieves trusted medical evidence, generates grounded answers, detects hallucinations, provides confidence scores, and self-corrects unreliable answers.

Current stage: **document processing + embeddings + FAISS retrieval**.

## 2. Current Status

Completed:
- Project setup and Git/GitHub workflow
- Google Colab environment
- T4 GPU verification
- Diabetes medical source document
- PDF text extraction and cleaning
- Text chunking
- Sentence-transformer embeddings
- FAISS similarity retrieval

Dataset:
```text
dataset/raw/niddk_guiding_principles_diabetes.pdf
```

Baseline:
```text
Pages:               83
Chunks:              277
Chunk size:          1000
Chunk overlap:       200
Embedding dimension: 384
Vector search:       FAISS
Retrieval:           Tested successfully
```

## 3. Notebook Order

```text
Notebook_01_Project_Setup.ipynb
        ↓
Notebook_02_Environment_Setup.ipynb
        ↓
Notebook_03_PDF_Text_Extraction.ipynb
        ↓
Next coding notebook
```

Do not recreate completed notebooks unless fixing a specific bug.

## 4. Mansi's Colab Setup

Select:

```text
Runtime → Change runtime type → T4 GPU
```

Fresh runtime:

```python
!git clone https://github.com/vivek28n/Medical-RAG-Hallucination-Detection.git
%cd Medical-RAG-Hallucination-Detection
```

If already cloned:

```python
%cd /content/Medical-RAG-Hallucination-Detection
```

Verify:

```python
import os
print("Current directory:", os.getcwd())
print("Dataset exists:", os.path.exists("dataset"))
print("Raw folder exists:", os.path.exists("dataset/raw"))
print("Files:", os.listdir("dataset/raw"))
```

Expected file:

```text
niddk_guiding_principles_diabetes.pdf
```

## 5. Install Dependencies First

For a fresh Colab runtime:

```python
!pip install -q     langchain     langchain-community     langchain-text-splitters     faiss-cpu     sentence-transformers     pymupdf     pypdf     fastapi     uvicorn
```

Verify:

```python
import langchain
import faiss
import sentence_transformers
import fitz
import fastapi

print("Required libraries imported successfully!")
```

If Colab asks for a runtime restart, restart and rerun the setup/import cells.

## 6. Common Errors

### `No module named 'fitz'`

```python
!pip install -q pymupdf
```

Then:

```python
import fitz
```

### `No module named 'langchain_text_splitters'`

```python
!pip install -q langchain-text-splitters
```

Then:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
```

### `No module named 'faiss'`

```python
!pip install -q faiss-cpu
```

Then:

```python
import faiss
```

### PDF not found

Check:

```python
import os
print(os.getcwd())
print(os.listdir("dataset/raw"))
```

Expected directory:

```text
/content/Medical-RAG-Hallucination-Detection
```

Correct path:

```python
pdf_path = "dataset/raw/niddk_guiding_principles_diabetes.pdf"
```

Do not add an extra `.pdf`.

## 7. Collaboration Rules

Before starting:

```bash
git pull --rebase origin main
```

After completing work:

```bash
git status
git add <files-you-changed>
git commit -m "Describe the change"
git pull --rebase origin main
git push origin main
```

Never use:

```bash
git push -f
```

If a rebase/merge conflict appears, stop and ask Vivek before resolving it.

## 8. Work Division

### Vivek
- Dataset collection/preparation
- Source-document organization
- Dataset folder management
- Overall RAG review
- Documentation/integration
- Final testing

### Mansi
- Coding after the current retrieval stage
- Primarily Google Colab notebook development
- Do not modify the dataset unless Vivek explicitly asks

## 9. ChatGPT Context for Mansi

Paste this into her ChatGPT before coding:

> We are working on a shared GitHub project called `Medical-RAG-Hallucination-Detection`. It is a medical RAG assistant focused on hallucination detection, confidence scoring and self-correction. Notebook 01, Notebook 02 and Notebook 03 are already completed. The diabetes PDF has 83 pages, 277 chunks, chunk size 1000, overlap 200, and 384-dimensional sentence-transformer embeddings. FAISS similarity retrieval is working successfully. I am responsible for coding after this stage. Dataset preparation is handled separately by Vivek. I am using Google Colab with a T4 GPU. Before giving code, check whether packages need installation. Give code in small cells, explain where each cell goes, and reuse existing variables instead of recreating the pipeline. Do not change the dataset structure unless explicitly requested.

For errors, ask:

```text
I completed the previous cell successfully. Here is the error/output:

[paste output]

Give me only the next step. First tell me if a package needs to be installed, then give the exact Colab cell to run.
```

## 10. Coding Rules

1. Work in small cells.
2. Run each cell before moving on.
3. If a cell errors, fix it before continuing.
4. Do not blindly run all cells after an error.
5. Reuse existing variables.
6. Do not change dataset paths without discussion.
7. Never hard-code API keys.
8. Never commit secrets or `.env` files.
9. Never force-push.
10. Keep notebook cells readable.
11. Save before committing.
12. Test important changes from a clean runtime when practical.

## 11. Secrets

Never commit:

```python
API_KEY = "actual-secret-key"
```

Use Colab Secrets or environment variables:

```python
import os
API_KEY = os.environ.get("API_KEY")
```

## 12. Baseline That Must Keep Working

```text
✓ Repository clone
✓ Dataset path
✓ PDF loading
✓ 83-page PDF
✓ Text extraction
✓ Text cleaning
✓ 277 chunks
✓ 1000-character chunk size
✓ 200-character overlap
✓ 384-dimensional embeddings
✓ FAISS similarity search
✓ Relevant diabetes guideline retrieval
```

If a new change breaks one of these, fix the regression first.

## 13. Next Development Direction

Build on the existing retrieval layer:

```text
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
```

Implement incrementally; do not unnecessarily replace the working retrieval pipeline.

## 14. What Mansi Reports After a Task

```text
Completed:
- What was implemented
- Notebook/file changed
- Cells added or modified
- Test queries/results
- Remaining warnings/errors
- Git commit hash
```

## 15. Development Principle

```text
Setup
  ↓
Environment
  ↓
Document Processing
  ↓
Retrieval
  ↓
Generation
  ↓
Hallucination Detection
  ↓
Confidence
  ↓
Self-Correction
  ↓
Backend
  ↓
Frontend
  ↓
Evaluation
```

Each stage should work before moving to the next.
