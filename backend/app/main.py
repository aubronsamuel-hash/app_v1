from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import config
from app.routers import auth, missions, assignments, admin

app = FastAPI(title="app_v1")

if config.ALLOWED_ORIGINS == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in config.ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(missions.router)
app.include_router(assignments.router)
app.include_router(admin.router)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
