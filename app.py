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

# Initialize FastAPI
app = FastAPI(
    title="Agentic Honeypot API",
    description="AI-powered honeypot for scam detection and intelligence extraction",
    version="2.0"
)

# Initialize components
detector = ScamDetector()
agent = AIAgent(api_key=Config.GROQ_API_KEY, model=Config.AI_MODEL)
session_manager = SessionManager(guvi_callback_url=Config.GUVI_CALLBACK_URL)

from typing import Union

class Message(BaseModel):
    sender: str
    text: str
    timestamp: Union[str, int]  # Accept both string and integer

class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Dict] = []
    metadata: Optional[Dict] = None

class HoneypotResponse(BaseModel):
    status: str
    reply: str

# API Key Authentication
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != Config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# Main Endpoint
@app.post("/honeypot", response_model=HoneypotResponse)
async def honeypot_endpoint(
    request: HoneypotRequest,
    x_api_key: str = Header(...)
):
    """
    Main honeypot endpoint that receives scam messages and returns AI-generated responses
    """
    # Verify API Key
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
            request.message.timestamp
        )
        
        # Detect scam (only on first message or if not already detected)
        if not session['scam_detected']:
            detection_result = detector.detect(incoming_message, conversation_history)
            
            if detection_result['is_scam']:
                session['scam_detected'] = True
                session['scam_info'] = detection_result
        
        # Extract intelligence from this message
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
            # If not scam, give neutral response
            reply = "I'm not sure I understand. Can you explain more?"
        
        # Add our reply to session
        session_manager.add_message(
            session_id,
            "user",
            reply,
            datetime.utcnow().isoformat() + "Z"
        )
        
        # Check if conversation should end
        if session_manager.should_end_conversation(session_id, Config.MAX_MESSAGES):
            # Send final callback to GUVI
            session_manager.send_final_callback(session_id, Config.MIN_MESSAGES_FOR_INTEL)
        
        return HoneypotResponse(
            status="success",
            reply=reply
        )
    
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "honeypot-api"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Agentic Honeypot API",
        "version": "2.0",
        "status": "operational",
        "endpoints": {
            "honeypot": "/honeypot (POST)",
            "health": "/health (GET)"
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