import os

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
TOKEN_TTL_HOURS = int(os.environ.get("TOKEN_TTL_HOURS", "24"))
