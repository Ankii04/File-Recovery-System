import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")
    UPLOAD_FOLDER = "static/uploads"

app_config = Config()
