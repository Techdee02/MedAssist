# Groq API Setup Guide

## What is Groq?

Groq provides **FREE, blazing-fast Llama inference** via their API. This eliminates the need to download and host large language models locally.

**Benefits:**
- ✅ **100% FREE** for development and production (no credit card required)
- ✅ **Llama 3.1 70B** - Better and newer than Llama 2 7B
- ✅ **Extremely fast** - 2-5x faster than self-hosted solutions
- ✅ **30 requests/minute** - Perfect for MVP and small-scale production
- ✅ **No infrastructure** - Just API calls, no model hosting

---

## Getting Your Free Groq API Key

### Step 1: Sign Up
1. Go to [https://console.groq.com](https://console.groq.com)
2. Click **"Sign Up"** or **"Get Started"**
3. Sign up with:
   - Google account, OR
   - GitHub account, OR
   - Email address

**NO credit card required!**

### Step 2: Create API Key
1. After logging in, go to **API Keys** section
2. Click **"Create API Key"**
3. Give it a name (e.g., "MedAssist-Dev")
4. Copy the API key (starts with `gsk_...`)
   - ⚠️ **Save it immediately** - you won't see it again!

### Step 3: Add to Your Project
1. Open `/workspaces/MedAssist/ai-service/.env`
2. Find the line: `GROQ_API_KEY=your_groq_api_key_here`
3. Replace `your_groq_api_key_here` with your actual key:
   ```
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
4. Save the file

---

## Available Groq Models

MedAssist is pre-configured to use `llama-3.1-70b-versatile`, but you can switch to other models:

| Model Name | Size | Best For | Speed |
|------------|------|----------|-------|
| `llama-3.1-70b-versatile` | 70B | **General use (RECOMMENDED)** | Very Fast |
| `llama3-70b-8192` | 70B | Long context (8K tokens) | Fast |
| `llama3-8b-8192` | 8B | Faster responses, simpler tasks | Extremely Fast |
| `mixtral-8x7b-32768` | 47B | Very long context (32K) | Fast |

To change models, update `MODEL_NAME` in `.env`:
```bash
MODEL_NAME=llama-3.1-70b-versatile
```

---

## Testing Your Setup

### Quick Test
```bash
cd /workspaces/MedAssist/ai-service
source /workspaces/MedAssist/.venv/bin/activate
pytest tests/test_intent_classifier.py -v
```

### Expected Output
```
test_emergency_detection PASSED
test_appointment_booking_intent PASSED
test_medication_refill_intent PASSED
...
15/15 tests PASSED ✅
```

---

## Usage Limits (FREE Tier)

| Metric | Limit | Notes |
|--------|-------|-------|
| **Requests/Minute** | 30 | Perfect for MVP |
| **Requests/Day** | 14,400 | ~600/hour |
| **Tokens/Minute** | 20,000 | Very generous |
| **Cost** | $0 | Completely FREE! |

**For MedAssist MVP:**
- 100 patients/day = ~200 API calls/day
- Well within free tier limits ✅

---

## Troubleshooting

### Error: "GROQ_API_KEY not found"
- Check `.env` file has `GROQ_API_KEY=gsk_...`
- Restart your FastAPI server after updating `.env`

### Error: "API key invalid"
- Verify you copied the full key (starts with `gsk_`)
- Create a new key at [console.groq.com](https://console.groq.com)

### Error: "Rate limit exceeded"
- Free tier: 30 requests/minute
- Wait 60 seconds or upgrade to paid tier
- For MVP scale, this should rarely happen

### Slow responses?
- Groq is typically <1 second
- Check your internet connection
- Try a smaller model: `llama3-8b-8192`

---

## Deployment Notes

### Environment Variables
When deploying to Render/Azure/etc., set these environment variables:

```bash
USE_LLM=true
GROQ_API_KEY=gsk_your_key_here
MODEL_NAME=llama-3.1-70b-versatile
```

### Free Deployment Stack
1. **AI Service**: Render Free Tier (512MB RAM) ✅
2. **Llama Inference**: Groq API (FREE) ✅
3. **Total Cost**: $0 🎉

---

## Next Steps

1. ✅ Get your Groq API key: [console.groq.com](https://console.groq.com)
2. ✅ Add to `.env` file
3. ✅ Run tests to verify
4. 🚀 Deploy to production!

**Questions?**
- Groq Docs: [https://docs.groq.com](https://docs.groq.com)
- Groq Discord: [https://discord.gg/groq](https://discord.gg/groq)
