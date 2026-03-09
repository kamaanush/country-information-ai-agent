from fastapi import FastAPI
from pydantic import BaseModel
from .graph import build_graph

app = FastAPI(title="Country Information AI Agent")
graph = build_graph()

class QueryIn(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ask")
def ask(q: QueryIn):
    try:
        result = graph.invoke({"user_query": q.question})
        return {"answer": result["answer"]}
    except Exception as e:
        # return the real error instead of generic 500
        return {"answer": f"ERROR: {type(e).__name__}: {e}"}