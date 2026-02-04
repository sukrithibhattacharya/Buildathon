from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import json

from config import Config
from scam_detector import ScamDetector
from ai_agent import AIAgent
from session_manager import SessionManager
from voice_detector import VoiceDetector

# Initialize FastAPI
app = FastAPI(
    title="Impact AI Hackathon API",
    description="Solution for Scam Detection and AI Voice Detection",
    version="2.1"
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---

class Message(BaseModel):
    sender: str
    text: str
    timestamp: int

class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Dict] = []
    metadata: Optional[Dict] = None

class HoneypotResponse(BaseModel):
    status: str
    reply: str

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

# --- EXCEPTION HANDLERS ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure all errors return required format if possible"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": str(exc.detail)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for internal server errors"""
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": f"Global Error: {str(exc)}"}
    )

# --- COMPONENTS ---

detector = ScamDetector()
agent = AIAgent(api_key=Config.GROQ_API_KEY, model=Config.AI_MODEL)
session_manager = SessionManager(guvi_callback_url=Config.GUVI_CALLBACK_URL)
voice_detector = VoiceDetector()

def verify_api_key(x_api_key: Optional[str]):
    """Strict API key verification"""
    if not x_api_key or x_api_key != Config.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key or malformed request"
        )

# --- PROBLEM 2: AGENTIC HONEYPOT ENDPOINTS ---

async def handle_honeypot_logic(request: Request, x_api_key: Optional[str]):
    """Core logic for honeypot processing"""
    # Verify API Key
    verify_api_key(x_api_key)
    
    try:
        # Load JSON body
        body = await request.json()
        payload = HoneypotRequest(**body)
        
        session_id = payload.sessionId
        incoming_message = payload.message.text
        conversation_history = payload.conversationHistory
        
        # Session state management
        session = session_manager.get_or_create_session(session_id)
        session_manager.add_message(
            session_id, 
            payload.message.sender, 
            incoming_message, 
            str(payload.message.timestamp)
        )
        
        # Scam detection
        if not session['scam_detected']:
            detection_result = detector.detect(incoming_message, conversation_history)
            if detection_result['is_scam']:
                session['scam_detected'] = True
                session['scam_info'] = detection_result
        
        # Intelligence extraction
        session['intelligence'].extract(incoming_message)
        
        # Response generation
        if session['scam_detected']:
            reply = agent.generate_response(
                scam_message=incoming_message,
                conversation_history=conversation_history,
                scam_info=session['scam_info'],
                message_count=session['message_count']
            )
        else:
            # Humanitarian/curious response or neutral fallback
            reply = "I'm not sure I understand. Can you explain more?"
        
        # Record response
        session_manager.add_message(
            session_id,
            "user",
            reply,
            datetime.utcnow().isoformat() + "Z"
        )
        
        # Mandatory Callback Check
        # Trigger callback if scam is detected and we have engaged enough
        if session['scam_detected'] and session['message_count'] >= Config.MIN_MESSAGES_FOR_INTEL:
            session_manager.send_final_callback(session_id, min_messages=0) # Logic handled here
            
        return HoneypotResponse(status="success", reply=reply)
        
    except Exception as e:
        print(f"Logic Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Explicitly handle POST and GET on both root and /honeypot to avoid 405
@app.post("/", response_model=HoneypotResponse)
@app.post("/honeypot", response_model=HoneypotResponse)
async def post_honeypot(request: Request, x_api_key: Optional[str] = Header(None, alias="x-api-key")):
    return await handle_honeypot_logic(request, x_api_key)

@app.get("/")
@app.get("/honeypot")
async def get_honeypot():
    return {
        "status": "success", 
        "message": "Honeypot API active. Please use POST with x-api-key."
    }

# --- PROBLEM 1: AI VOICE DETECTION ENDPOINT ---

@app.post("/api/voice-detection", response_model=VoiceDetectionResponse)
async def voice_detection_endpoint(
    request: VoiceDetectionRequest,
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    verify_api_key(x_api_key)
    result = voice_detector.detect(request.language, request.audioBase64)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return VoiceDetectionResponse(**result)

# --- UTILITIES ---

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hackathon-api"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

# --- STARTUP ---

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False
    )