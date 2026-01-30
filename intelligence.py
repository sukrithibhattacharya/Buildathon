import re
from typing import Dict, List

class IntelligenceExtractor:
    """Extract and categorize scam intelligence"""
    
    def __init__(self):
        self.intelligence = {
            'bankAccounts': [],
            'upiIds': [],
            'phishingLinks': [],
            'phoneNumbers': [],
            'suspiciousKeywords': [],
            'emailAddresses': [],
            'organizationNames': [],
        }
    
    def extract(self, message: str) -> None:
        """Extract intelligence from a message"""
        
        # Extract bank accounts
        bank_patterns = [
            r'\b\d{9,18}\b',  # Account numbers
            r'[A-Z]{4}0[A-Z0-9]{6}',  # IFSC codes
        ]
        for pattern in bank_patterns:
            matches = re.findall(pattern, message)
            self.intelligence['bankAccounts'].extend(matches)
        
        # Extract UPI IDs
        upi_pattern = r'[\w\.-]+@[\w\.-]+'
        upi_matches = re.findall(upi_pattern, message)
        for match in upi_matches:
            if any(provider in match.lower() for provider in ['paytm', 'phonepe', 'gpay', 'upi', 'ybl', 'okhdfcbank', 'oksbi']):
                self.intelligence['upiIds'].append(match)
            elif '@' in match and '.' in match:
                self.intelligence['emailAddresses'].append(match)
        
        # Extract phone numbers
        phone_pattern = r'(\+91|0)?[6-9]\d{9}'
        phone_matches = re.findall(phone_pattern, message)
        self.intelligence['phoneNumbers'].extend(phone_matches)
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        url_matches = re.findall(url_pattern, message)
        self.intelligence['phishingLinks'].extend(url_matches)
        
        # Extract organization names (basic)
        org_patterns = [
            r'(SBI|HDFC|ICICI|Axis|Paytm|PhonePe|Google Pay|Amazon|Flipkart)\s*(Bank|Pay)?',
        ]
        for pattern in org_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                self.intelligence['organizationNames'].extend([m[0] for m in matches])
        
        # Deduplicate
        for key in self.intelligence:
            self.intelligence[key] = list(set(self.intelligence[key]))
    
    def get_intelligence(self) -> Dict:
        """Get all extracted intelligence"""
        return {k: v for k, v in self.intelligence.items() if v}  # Only non-empty
    
    def get_count(self) -> int:
        """Get total items extracted"""
        return sum(len(v) for v in self.intelligence.values())