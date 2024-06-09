from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph import LangGraph

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    results: list

@app.post("/query", response_model=QueryResponse)
def execute_query(request: QueryRequest):
    langgraph = LangGraph("bolt://localhost:7687", "neo4j", "test")
    try:
        results = langgraph.execute_query(request.query)
        return QueryResponse(results=[dict(record) for record in results])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        langgraph.close()
