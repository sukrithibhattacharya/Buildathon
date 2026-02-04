import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Settings
    API_KEY = os.getenv("API_KEY", "your-secret-honeypot-key-12345")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Server Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # GUVI Callback
    GUVI_CALLBACK_URL = os.getenv(
        "GUVI_CALLBACK_URL",
        "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    )
    
    # Agent Settings
    MAX_MESSAGES = 25  # Maximum messages before ending
    MIN_MESSAGES_FOR_INTEL = 1  # Send callback as soon as scam is confirmed
    
    # Scam Detection Thresholds
    SCAM_THRESHOLD = 0.6  # 60% confidence = scam
    
    # AI Model
    AI_MODEL = "mixtral-8x7b-32768"  # Fast and free on Groq