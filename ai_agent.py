from groq import Groq
from typing import List, Dict
import random

class AIAgent:
    """AI Agent with personas for engaging scammers"""
    
    PERSONAS = {
        'elderly': {
            'style': 'confused, worried, asks for clarification, slow to understand technology',
            'sample': 'Oh my! I am very worried. Can you please explain this to me slowly? I am not good with these mobile things.',
        },
        'eager': {
            'style': 'willing to help, asks questions, wants to solve the problem quickly',
            'sample': 'Yes yes, I want to fix this immediately! What do I need to do? Please tell me step by step.',
        },
        'skeptical': {
            'style': 'cautious, asks for verification, wants proof',
            'sample': 'Hmm, how do I know this is real? Can you give me your company details? My son told me to always verify.',
        },
        'technical': {
            'style': 'claims technical issues, asks for alternatives, needs help',
            'sample': 'I am trying but getting error. Is there another way? Can you send me the link via SMS?',
        }
    }
    
    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.current_persona = None
    
    def select_persona(self, scam_type: str) -> str:
        """Select appropriate persona based on scam type"""
        if not self.current_persona:
            # Select persona based on scam type or randomly
            if 'KYC' in scam_type or 'Bank' in scam_type:
                self.current_persona = random.choice(['elderly', 'skeptical'])
            elif 'Prize' in scam_type or 'Lottery' in scam_type:
                self.current_persona = 'eager'
            else:
                self.current_persona = random.choice(list(self.PERSONAS.keys()))
        
        return self.current_persona
    
    def generate_response(
        self,
        scam_message: str,
        conversation_history: List[Dict],
        scam_info: Dict,
        message_count: int
    ) -> str:
        """Generate human-like response to engage scammer"""
        
        persona_name = self.select_persona(scam_info.get('scam_type', 'Generic'))
        persona = self.PERSONAS[persona_name]
        
        # Build conversation context
        history_text = ""
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = "Scammer" if msg['sender'] == 'scammer' else "You"
            history_text += f"{role}: {msg['text']}\n"
        
        # Create dynamic prompt based on conversation stage
        if message_count < 5:
            goal = "Express concern and ask clarifying questions to understand the situation better"
        elif message_count < 12:
            goal = "Show willingness to comply but ask for verification details (phone number, website, company name, etc.)"
        elif message_count < 20:
            goal = "Claim technical difficulties or ask for alternative methods. Extract payment details if offered."
        else:
            goal = "Start showing slight suspicion or say you need to consult someone, but still extract any final details"
        
        system_prompt = f"""You are pretending to be a {persona_name} victim of a scam. Your goal is to extract information from the scammer while appearing believable.

PERSONA: {persona['style']}
EXAMPLE RESPONSE: {persona['sample']}

SCAM TYPE: {scam_info.get('scam_type', 'Unknown')}
CURRENT GOAL: {goal}

RULES:
1. NEVER reveal you know it's a scam
2. Ask questions that might make the scammer reveal:
   - Phone numbers
   - UPI IDs or payment details
   - Website links
   - Company/organization names
   - Bank account details
3. Keep responses short (1-3 sentences)
4. Show appropriate emotion (worry, confusion, eagerness)
5. Sometimes make spelling/grammar mistakes to seem more human
6. Ask for verification but be willing to proceed

PREVIOUS CONVERSATION:
{history_text}

LATEST SCAMMER MESSAGE: {scam_message}

Respond as this persona would, naturally continuing the conversation:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": scam_message}
                ],
                temperature=0.8,  # More creative/varied
                max_tokens=150,
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Remove any meta-commentary
            reply = reply.replace("As the victim,", "").replace("*", "").strip()
            
            return reply
            
        except Exception as e:
            # Fallback responses
            fallbacks = [
                "I am worried. Can you please explain more?",
                "What should I do? I don't want my account blocked!",
                "Can you give me your phone number? I want to call and verify.",
                "Is there a website I can check? My son told me to always verify.",
            ]
            return random.choice(fallbacks)