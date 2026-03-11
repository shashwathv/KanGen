from fastapi.middleware.cors import CORSMiddleware
import os

def add_cors(app):
    ENV = os.getenv("ENV", "development")

    if ENV == "production":
        origins = [os.getenv("FRONTEND_URL", "https://yourfrontend.com")]
    else:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False
    )