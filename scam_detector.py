import re
from typing import Dict, List

class ScamDetector:
    """Advanced multi-layer scam detection engine"""
    
    SCAM_KEYWORDS = {
        'urgent': 3.0,
        'verify': 2.5,
        'account blocked': 4.0,
        'suspended': 3.5,
        'immediate': 3.0,
        'click here': 2.5,
        'confirm': 2.0,
        'update': 2.0,
        'security': 2.0,
        'otp': 3.5,
        'upi': 2.5,
        'bank': 2.0,
        'payment': 2.0,
        'transfer': 2.5,
        'prize': 3.0,
        'winner': 3.0,
        'congratulations': 2.5,
        'lottery': 4.0,
        'refund': 2.5,
        'cashback': 2.5,
        'limited time': 3.0,
        'expire': 2.5,
        'last chance': 3.0,
        'act now': 3.0,
        'kycupdate': 4.0,
        'block': 3.5,
        'fraud': 3.0,
        'unauthorized': 3.0,
    }
    
    URGENCY_PATTERNS = [
        r'within \d+ (hours?|minutes?|days?)',
        r'immediately',
        r'right now',
        r'asap',
        r'urgent',
        r'today',
        r'expire',
        r'last chance',
    ]
    
    SENSITIVE_DATA_REQUESTS = [
        r'(otp|pin|password|cvv)',
        r'(account number|bank account)',
        r'(upi id|upi pin)',
        r'(card number|debit card|credit card)',
        r'(aadhaar|pan card)',
        r'(verify|confirm|update).*(detail|information)',
    ]
    
    def detect(self, message: str, conversation_history: List[Dict]) -> Dict:
        """
        Multi-layer scam detection
        Returns: {
            'is_scam': bool,
            'confidence': float,
            'scam_type': str,
            'risk_factors': List[str]
        }
        """
        message_lower = message.lower()
        score = 0.0
        risk_factors = []
        
        # 1. Keyword Analysis
        for keyword, weight in self.SCAM_KEYWORDS.items():
            if keyword in message_lower:
                score += weight
                risk_factors.append(f"Scam keyword: '{keyword}'")
        
        # 2. Urgency Detection
        for pattern in self.URGENCY_PATTERNS:
            if re.search(pattern, message_lower):
                score += 2.0
                risk_factors.append("Urgency tactic detected")
                break
        
        # 3. Sensitive Data Request
        for pattern in self.SENSITIVE_DATA_REQUESTS:
            if re.search(pattern, message_lower):
                score += 3.0
                risk_factors.append("Requesting sensitive information")
                break
        
        # 4. URL/Link Detection
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        if re.search(url_pattern, message):
            score += 2.5
            risk_factors.append("Contains suspicious link")
        
        # 5. Phone Number Detection
        phone_pattern = r'(\+91|0)?[6-9]\d{9}'
        if re.search(phone_pattern, message):
            score += 1.5
            risk_factors.append("Contains phone number")
        
        # 6. Money Request
        money_patterns = [r'₹\s?\d+', r'rs\.?\s?\d+', r'pay\s+\d+', r'\d+\s*rupees']
        for pattern in money_patterns:
            if re.search(pattern, message_lower):
                score += 3.0
                risk_factors.append("Money request detected")
                break
        
        # Normalize score to 0-1 confidence
        confidence = min(score / 15.0, 1.0)
        
        # Determine scam type
        scam_type = self._classify_scam_type(message_lower, risk_factors)
        
        return {
            'is_scam': confidence >= 0.6,
            'confidence': round(confidence, 2),
            'scam_type': scam_type,
            'risk_factors': risk_factors,
            'risk_score': round(score, 2)
        }
    
    def _classify_scam_type(self, message: str, risk_factors: List[str]) -> str:
        """Classify the type of scam"""
        if 'bank' in message or 'account' in message:
            return "Bank Account Fraud"
        elif 'upi' in message:
            return "UPI Fraud"
        elif 'otp' in message or 'pin' in message:
            return "OTP/PIN Theft"
        elif 'prize' in message or 'winner' in message or 'lottery' in message:
            return "Prize/Lottery Scam"
        elif 'kyc' in message or 'verify' in message:
            return "KYC/Verification Scam"
        elif any('link' in rf.lower() for rf in risk_factors):
            return "Phishing"
        else:
            return "Generic Fraud"