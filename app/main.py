# from fastapi import FastAPI
# from starlette.middleware.sessions import SessionMiddleware
# from fastapi.middleware.cors import CORSMiddleware

# from app.auth import router as auth_router
# from app.workspaces import router as workspace_router
# from app.auto_upload import router as auto_upload_router
# from app.user import router as user_router
# # from app.powerbi_folder_migration import router as folder_router


# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://1115fb10-6ea8-4052-8d1b-31238016c02e.lovableproject.com",
#         "https://lovable.dev",
#         "https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.add_middleware(
#     SessionMiddleware,
#     secret_key="super-secret-key",
#     same_site="none",
#     https_only=True
#     # same_site="lax",
#     # https_only=False

# )

# app.include_router(auth_router)
# app.include_router(workspace_router)
# app.include_router(auto_upload_router)
# app.include_router(user_router)

# # app.include_router(folder_router)

# @app.get("/")
# def root():
#     return {"status": "Backend running"}


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app import auth, workspaces  # ← Import both routers
import os

app = FastAPI(title="Power BI Azure Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,  # CRITICAL for sessions
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "change-this-in-production-use-secrets-token-urlsafe"),
    max_age=86400,  # 24 hours
    same_site="none",  # For cross-origin
    https_only=True,  # Set to False for local testing
)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(workspaces.router, tags=["Workspaces"])  # ← Add this

@app.get("/")
def read_root():
    return {
        "message": "Power BI Auth API", 
        "status": "running",
        "endpoints": {
            "login": "/login",
            "callback": "/auth/callback",
            "token": "/auth/token",
            "workspaces": "/workspaces"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}