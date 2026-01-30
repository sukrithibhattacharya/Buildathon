from typing import Dict, List, Optional
from datetime import datetime
import requests
from intelligence import IntelligenceExtractor

class SessionManager:
    """Manage conversation sessions and intelligence"""
    
    def __init__(self, guvi_callback_url: str):
        self.sessions: Dict[str, Dict] = {}
        self.guvi_callback_url = guvi_callback_url
    
    def get_or_create_session(self, session_id: str) -> Dict:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'session_id': session_id,
                'started_at': datetime.utcnow().isoformat(),
                'message_count': 0,
                'scam_detected': False,
                'scam_info': {},
                'intelligence': IntelligenceExtractor(),
                'conversation': [],
                'agent_persona': None,
                'callback_sent': False,
            }
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, sender: str, text: str, timestamp: str):
        """Add message to session"""
        session = self.get_or_create_session(session_id)
        session['conversation'].append({
            'sender': sender,
            'text': text,
            'timestamp': timestamp
        })
        session['message_count'] += 1
    
    def should_end_conversation(self, session_id: str, max_messages: int = 25) -> bool:
        """Determine if conversation should end"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # End if max messages reached
        if session['message_count'] >= max_messages:
            return True
        
        # End if scammer seems to give up (check last messages)
        if session['message_count'] > 10:
            last_messages = session['conversation'][-3:]
            scammer_messages = [m['text'] for m in last_messages if m['sender'] == 'scammer']
            
            # If scammer is repeating or getting frustrated
            if len(scammer_messages) >= 2:
                if scammer_messages[-1] == scammer_messages[-2]:
                    return True
        
        return False
    
    def send_final_callback(self, session_id: str, min_messages: int = 5) -> bool:
        """Send final intelligence to GUVI"""
        session = self.sessions.get(session_id)
        if not session or session['callback_sent']:
            return False
        
        # Don't send if too few messages
        if session['message_count'] < min_messages:
            return False
        
        intelligence_data = session['intelligence'].get_intelligence()
        
        # Add suspicious keywords from conversation
        all_messages = ' '.join([m['text'] for m in session['conversation'] if m['sender'] == 'scammer'])
        keywords = self._extract_keywords(all_messages)
        if keywords:
            intelligence_data['suspiciousKeywords'] = keywords
        
        payload = {
            "sessionId": session_id,
            "scamDetected": session['scam_detected'],
            "totalMessagesExchanged": session['message_count'],
            "extractedIntelligence": intelligence_data,
            "agentNotes": self._generate_agent_notes(session)
        }
        
        try:
            response = requests.post(
                self.guvi_callback_url,
                json=payload,
                timeout=5
            )
            session['callback_sent'] = True
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send callback: {e}")
            return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract suspicious keywords"""
        keywords = []
        suspicious_words = ['urgent', 'verify', 'block', 'suspend', 'otp', 'upi', 'bank', 'pay', 'transfer', 'prize', 'winner']
        text_lower = text.lower()
        
        for word in suspicious_words:
            if word in text_lower:
                keywords.append(word)
        
        return list(set(keywords))[:10]  # Max 10 keywords
    
    def _generate_agent_notes(self, session: Dict) -> str:
        """Generate summary notes"""
        scam_type = session['scam_info'].get('scam_type', 'Unknown')
        risk_factors = session['scam_info'].get('risk_factors', [])
        intel_count = session['intelligence'].get_count()
        
        notes = f"Scam Type: {scam_type}. "
        notes += f"Extracted {intel_count} intelligence items. "
        
        if risk_factors:
            notes += f"Key tactics: {', '.join(risk_factors[:3])}."
        
        return notes