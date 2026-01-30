# 🍯 Agentic Honeypot API - Winning Solution

AI-powered honeypot system for scam detection and intelligence extraction.

## 🚀 Quick Deploy

### Railway (Recommended - FREE)

1. Sign up at railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Connect your GitHub repo with this code
4. Add environment variables:
   - `API_KEY`: your-secret-key-12345
   - `GROQ_API_KEY`: your-groq-api-key
5. Deploy!

Your API will be at: `https://your-project.railway.app/honeypot`

## 🔑 Get API Keys

1. **Groq API Key** (FREE):
   - Go to console.groq.com
   - Sign up
   - Create API key
   - Copy it to `.env` file

2. **Your API Key**:
   - Make up a secret key (e.g., `honeypot-secret-abc123`)
   - Use this when submitting to GUVI

## 📡 API Endpoint

**URL**: `https://your-domain.com/honeypot`
**Method**: POST
**Headers**:
- `x-api-key`: your-secret-key-12345
- `Content-Type`: application/json

## 🧪 Test Locally
```bash
pip install -r requirements.txt
python app.py
```

Visit: http://localhost:8000

## 📊 Features

✅ Multi-layer scam detection
✅ AI agent with adaptive personas
✅ Advanced intelligence extraction
✅ Automatic GUVI callback
✅ Fast response time (<500ms)
✅ Session management

## 🏆 Built to Win!
```

---

## 🎯 DEPLOYMENT INSTRUCTIONS

### **Option 1: Railway (EASIEST - FREE)**

1. **Create account**: Go to [railway.app](https://railway.app)
2. **New Project**: Click "New Project" → "Empty Project"
3. **Create GitHub Repo**:
   - Create new repo on GitHub
   - Upload ALL the files above
   - Push to GitHub
4. **Deploy**:
   - In Railway, click "Deploy from GitHub"
   - Select your repo
   - Railway will auto-detect Python and deploy
5. **Add Environment Variables**:
   - Click on your project → "Variables"
   - Add:
     - `API_KEY` = `your-secret-honeypot-key-12345`
     - `GROQ_API_KEY` = (get from console.groq.com)
6. **Get URL**:
   - Railway will give you a URL like: `honeypot-production-xxxx.up.railway.app`
   - Your endpoint: `https://honeypot-production-xxxx.up.railway.app/honeypot`

### **Option 2: Render (FREE)**

1. Go to [render.com](https://render.com)
2. "New" → "Web Service"
3. Connect GitHub repo
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy!

---

## 🔑 GET GROQ API KEY (FREE!)

1. Go to: https://console.groq.com
2. Sign up (free)
3. Click "API Keys" → "Create API Key"
4. Copy the key
5. Add to `.env` file: `GROQ_API_KEY=gsk_xxxxx...`

---

## 📝 SUBMISSION TO GUVI

When submitting:

**Endpoint URL**: `https://your-railway-url.railway.app/honeypot`
**API Key Header**: `x-api-key`
**API Key Value**: `your-secret-honeypot-key-12345` (whatever you set in .env)

---
