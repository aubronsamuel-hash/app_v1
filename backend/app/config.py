import os

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
TOKEN_TTL = int(os.environ.get("TOKEN_TTL", "1440"))
