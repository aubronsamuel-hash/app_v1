from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, missions, assignments

app = FastAPI(title="app_v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(missions.router)
app.include_router(assignments.router)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
