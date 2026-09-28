from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.schemas import AskRequest, AskResponse, SourceEvidence
from app.services.retrieval import retrieval_service
from app.services.llm import llm_service
import traceback

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting up FastAPI. Loading models...")
    retrieval_service.load_models_and_index()
    llm_service.initialize()
    yield
    # Shutdown logic
    print("Shutting down...")

app = FastAPI(title="Medical RAG API", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok", "models_loaded": retrieval_service.index is not None}

@app.post("/api/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    try:
        print(f"Received query: {request.query}")
        # 1. Retrieve chunks
        raw_results = retrieval_service.search(request.query)
        
        # 2. Build context and map sources
        context = ""
        sources = []
        for i, res in enumerate(raw_results, 1):
            context += f"\n--- Evidence {i} ---\n"
            context += f"Source page: {res['page']}\n"
            context += f"Chunk ID: {res['chunk_id']}\n\n"
            context += f"{res['text']}\n"
            
            sources.append(SourceEvidence(
                chunk_id=res['chunk_id'],
                page=res['page'],
                text=res['text']
            ))
            
        # 3. LLM generation
        answer = llm_service.generate_grounded_answer(request.query, context)
        
        return AskResponse(
            answer=answer,
            sources=sources
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
