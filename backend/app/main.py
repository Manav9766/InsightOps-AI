from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_upload import router as upload_router
from app.api.routes_analysis import router as analysis_router

app = FastAPI(
    title="InsightOps AI API",
    description="Backend API for the Agentic Data Analyst & Business Intelligence Platform.",
    version="0.1.0",
)

# Frontend will use this later.
# For now, allow local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local development or any frontend that needs to access the API. In production, you should restrict this to your frontend domain.
    allow_credentials=True, # Allow cookies and authentication headers to be sent in cross-origin requests.
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "InsightOps AI backend is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "insightops-ai-backend",
    }