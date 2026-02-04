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

from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI(
    title="Impact AI Hackathon API",
    description="Solution for Scam Detection and AI Voice Detection",
    version="2.0"
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler for Hackathon Format
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # This specifically catches FastAPI's 404, 405, etc.
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": str(detail)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": f"Internal Server Error: {str(exc)}"}
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
    timestamp: int

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
def verify_api_key(x_api_key: Optional[str]):
    if not x_api_key or x_api_key != Config.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key or malformed request"
        )
    return x_api_key

# --- PROBLEM 2: AGENTIC HONEYPOT ENDPOINTS ---

@app.api_route("/", methods=["GET", "POST"], response_model=HoneypotResponse)
@app.api_route("/honeypot", methods=["GET", "POST"], response_model=HoneypotResponse)
async def honeypot_endpoint(
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """
    Robust endpoint for Honeypot API supporting both GET and POST at / and /honeypot
    """
    if request.method == "GET":
        # Handle verification or health check from root
        return HoneypotResponse(
            status="success",
            reply="Honeypot API is operational. Send a POST request to interact."
        )

    # Verify API Key
    verify_api_key(x_api_key)
    
    try:
        # Load and validate JSON body manually to ensure compatibility
        body = await request.json()
        data = HoneypotRequest(**body)
        
        session_id = data.sessionId
        incoming_message = data.message.text
        conversation_history = data.conversationHistory
        
        # Get or create session
        session = session_manager.get_or_create_session(session_id)
        
        # Add incoming message to session
        session_manager.add_message(
            session_id,
            data.message.sender,
            incoming_message,
            str(data.message.timestamp)
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
        # Return strict error format even for internal errors
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


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

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

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