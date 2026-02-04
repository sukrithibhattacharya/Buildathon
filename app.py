from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime

from config import Config
from scam_detector import ScamDetector
from ai_agent import AIAgent
from session_manager import SessionManager
from voice_detector import VoiceDetector

# Initialize FastAPI
app = FastAPI(
    title="Impact AI Hackathon API",
    description="Solution for Scam Detection and AI Voice Detection",
    version="2.0"
)

# Custom Exception Handler for Hackathon Format
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    status_code = 500
    message = str(exc)
    
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=status_code, content=exc.detail)
        message = exc.detail
        
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message}
    )

# Initialize components
detector = ScamDetector()
agent = AIAgent(api_key=Config.GROQ_API_KEY, model=Config.AI_MODEL)
session_manager = SessionManager(guvi_callback_url=Config.GUVI_CALLBACK_URL)
voice_detector = VoiceDetector()

# Request/Response Models
class Message(BaseModel):
    sender: str
    text: str
    timestamp: int  # Changed to int for ms support

class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Dict] = []
    metadata: Optional[Dict] = None

class HoneypotResponse(BaseModel):
    status: str
    reply: str

# Problem 1: Voice Detection Models
class VoiceDetectionRequest(BaseModel):
    language: str
    audioFormat: str
    audioBase64: str

class VoiceDetectionResponse(BaseModel):
    status: str
    language: str
    classification: str
    confidenceScore: float
    explanation: str

# API Key Authentication
def verify_api_key(x_api_key: str):
    if x_api_key != Config.API_KEY:
        # Return strict hackathon error format
        raise HTTPException(
            status_code=401,
            detail={"status": "error", "message": "Invalid API key or malformed request"}
        )
    return x_api_key

# --- PROBLEM 2: AGENTIC HONEYPOT ENDPOINTS ---

@app.post("/", response_model=HoneypotResponse)
@app.post("/honeypot", response_model=HoneypotResponse)
async def honeypot_endpoint(
    request: HoneypotRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Main honeypot endpoint handling both root and /honeypot
    """
    verify_api_key(x_api_key)
    
    try:
        session_id = request.sessionId
        incoming_message = request.message.text
        conversation_history = request.conversationHistory
        
        # Get or create session
        session = session_manager.get_or_create_session(session_id)
        
        # Add incoming message to session
        session_manager.add_message(
            session_id,
            request.message.sender,
            incoming_message,
            str(request.message.timestamp)
        )
        
        # Detect scam
        if not session['scam_detected']:
            detection_result = detector.detect(incoming_message, conversation_history)
            if detection_result['is_scam']:
                session['scam_detected'] = True
                session['scam_info'] = detection_result
        
        # Extract intelligence
        session['intelligence'].extract(incoming_message)
        
        # Generate AI response
        if session['scam_detected']:
            reply = agent.generate_response(
                scam_message=incoming_message,
                conversation_history=conversation_history,
                scam_info=session['scam_info'],
                message_count=session['message_count']
            )
        else:
            reply = "I'm not sure I understand. Can you explain more?"
        
        # Add our reply to session
        session_manager.add_message(
            session_id,
            "user",
            reply,
            datetime.utcnow().isoformat() + "Z"
        )
        
        # Callback check
        if session_manager.should_end_conversation(session_id, Config.MAX_MESSAGES):
            session_manager.send_final_callback(session_id, Config.MIN_MESSAGES_FOR_INTEL)
        
        return HoneypotResponse(status="success", reply=reply)
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# --- PROBLEM 1: AI VOICE DETECTION ENDPOINT ---

@app.post("/api/voice-detection", response_model=VoiceDetectionResponse)
async def voice_detection_endpoint(
    request: VoiceDetectionRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Endpoint for detecting AI-generated voices
    """
    verify_api_key(x_api_key)
    
    result = voice_detector.detect(request.language, request.audioBase64)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
        
    return VoiceDetectionResponse(**result)

# --- UTILITY ENDPOINTS ---

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hackathon-api"}

@app.get("/")
async def root_info():
    return {
        "service": "Impact AI Hackathon API",
        "status": "operational",
        "endpoints": {
            "voice_detection": "/api/voice-detection (POST)",
            "honeypot": "/honeypot (POST) or / (POST)"
        }
    }


# Run server
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False
    )