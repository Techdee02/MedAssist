# MedAssist AI Service - Deployment Guide

**Target Platform:** Render Free Tier  
**Monthly Cost:** $0-8 (Groq API is FREE + optional Azure services)  
**Deployment Time:** ~5 minutes

---

## Prerequisites

### Required (FREE)
- ✅ GitHub account (to connect repository)
- ✅ Render account (sign up at https://render.com)
- ✅ Groq API key (FREE at https://console.groq.com)

### Optional (Pay-per-use)
- Azure subscription for Document Intelligence (~$1-3/month)
- Azure subscription for AI Translator (~$2-5/month)

---

## Step 1: Prepare Groq API Key

1. Go to https://console.groq.com
2. Sign up/login (FREE - no credit card required)
3. Navigate to "API Keys"
3. Create new API key
4. Copy the key (starts with `gsk_`)

**Your Key:** `gsk_your_groq_api_key_here`

---

## Step 2: Push Code to GitHub

```bash
# Initialize git (if not already done)
cd /workspaces/MedAssist
git init
git add .
git commit -m "feat: Complete MedAssist AI Service with Groq and Azure APIs"

# Push to GitHub
git remote add origin https://github.com/Techdee02/MedAssist.git
git branch -M main
git push -u origin main
```

---

## Step 3: Deploy to Render

### Option A: Using Blueprint (Recommended)

1. **Login to Render**
   - Go to https://dashboard.render.com
   - Sign in with GitHub

2. **New Blueprint**
   - Click "New +" → "Blueprint"
   - Select your repository: `Techdee02/MedAssist`
   - Render will auto-detect `render.yaml`

3. **Configure Environment Variables**
   - Click on the service after creation
   - Go to "Environment" tab
   - Add secrets (sync: false variables):

   ```
   GROQ_API_KEY=your_groq_api_key_here
   
   # Optional: Azure Document Intelligence
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_azure_doc_endpoint
   AZURE_DOCUMENT_INTELLIGENCE_KEY=your_azure_doc_key
   
   # Optional: Azure AI Translator
   AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com/
   AZURE_TRANSLATOR_KEY=your_azure_translator_key
   AZURE_TRANSLATOR_REGION=southafricanorth
   ```

4. **Deploy**
   - Click "Apply" or "Manual Deploy"
   - Wait 3-5 minutes for build
   - Service will be live at: `https://medassist-ai-service.onrender.com`

### Option B: Manual Deployment

1. **New Web Service**
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Select `MedAssist` repository

2. **Configure Service**
   ```
   Name: medassist-ai-service
   Region: Oregon (or Singapore for Africa)
   Branch: main
   Root Directory: ai-service
   Runtime: Docker
   Plan: Free
   ```

3. **Build Settings**
   - Dockerfile Path: `./Dockerfile`
   - Docker Context: `.`

4. **Add Environment Variables** (same as above)

5. **Create Web Service**

---

## Step 4: Verify Deployment

### Test Endpoints

Once deployed, test your service:

```bash
# Replace with your Render URL
export API_URL=https://medassist-ai-service.onrender.com

# 1. Health Check
curl $API_URL/api/v1/health

# 2. Root Endpoint
curl $API_URL/

# 3. Message Processing
curl -X POST $API_URL/api/v1/message/process \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "test-001",
    "patient_id": "patient-123",
    "message": "I need an appointment tomorrow",
    "conversation_history": []
  }'

# 4. Translation
curl -X POST $API_URL/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good morning",
    "target_language": "yo",
    "source_language": "en"
  }'
```

### Expected Responses

**Health Check (should show all services healthy):**
```json
{
  "status": "healthy",
  "components": {
    "groq_api": {
      "status": "healthy",
      "model": "llama-3.3-70b-versatile"
    },
    "azure_document_intelligence": {
      "status": "configured"
    },
    "azure_translator": {
      "status": "configured"
    }
  }
}
```

---

## Step 5: Configure Custom Domain (Optional)

1. Go to service settings in Render
2. Click "Custom Domain"
3. Add your domain (e.g., `api.medassist.ng`)
4. Update DNS records as instructed
5. SSL certificate auto-provisioned (FREE)

---

## Render Free Tier Limitations

### What You Get (FREE)
- ✅ 750 hours/month (enough for 24/7 operation)
- ✅ 512 MB RAM
- ✅ Free SSL certificates
- ✅ Automatic deploys from GitHub
- ✅ Custom domains supported

### Important Notes
- 🔄 **Sleeps after 15 min inactivity**
- ⏰ **~30 second wake-up time** on first request
- 💾 Limited to 512 MB RAM
- 🔁 Can upgrade to paid plan anytime

### Preventing Sleep (Optional)
Use a free uptime monitor to ping every 10 minutes:
- UptimeRobot (https://uptimerobot.com) - FREE
- Ping URL: `https://medassist-ai-service.onrender.com/api/v1/health`
- Interval: 10 minutes

---

## Monitoring & Maintenance

### Health Monitoring

**Endpoint:** `GET /api/v1/health`

Monitor these components:
- `groq_api` - Should be "healthy"
- `azure_document_intelligence` - Should be "configured"
- `azure_translator` - Should be "configured"

### Logs

**View Logs in Render:**
1. Go to your service dashboard
2. Click "Logs" tab
3. Real-time logs stream here

**Important Log Patterns:**
```
✅ "AI Service ready to accept requests" - Service started
✅ "API routers registered successfully" - All endpoints loaded
❌ "groq.APIError" - Groq API key issue
❌ "Azure" errors - Azure credentials issue
```

### Error Alerts

**Set up in Render:**
1. Go to "Notifications"
2. Enable:
   - Deploy failures
   - Service crashes
   - Health check failures

### Cost Monitoring

**Monthly Estimates:**
- Render Free Tier: **$0**
- Groq API (FREE tier): **$0**
- Azure Translator: **$2-5** (pay-per-use)
- Azure Document Intelligence: **$1-3** (pay-per-use)

**Total: $3-8/month** (extremely cost-effective)

---

## Scaling & Optimization

### Upgrade to Paid Plan (If Needed)

**Starter Plan ($7/month):**
- No sleep
- 512 MB RAM
- Faster deploys

**Standard Plan ($25/month):**
- 2 GB RAM
- Multiple workers
- Better performance

### Performance Optimization

**Current Configuration (Free Tier):**
```yaml
workers: 1          # Single worker (free tier limit)
max_tokens: 512     # Balance speed vs quality
temperature: 0.7    # Good for medical tasks
```

**If Upgrading to Paid:**
```yaml
workers: 2-4        # Multiple workers
max_tokens: 1024    # More detailed responses
```

### Caching (Future Enhancement)

Add Redis for:
- Translation caching (reduce Azure costs)
- Session storage
- Response caching

**Free Redis Options:**
- Render Redis (Free tier available)
- Upstash (Generous free tier)

---

## Troubleshooting

### Service Won't Start

**Check logs for:**
```bash
# Missing environment variable
Error: GROQ_API_KEY not set

# Solution: Add in Render dashboard
```

### Groq API Errors

**Error:** `groq.APIError: Invalid API key`
```bash
# Verify key is correct in Render environment variables
# Key should start with "gsk_"
```

**Error:** `Rate limit exceeded`
```bash
# Free tier: 30 requests/minute
# Solution: Implement rate limiting or upgrade Groq plan
```

### Azure API Errors

**Error:** `Azure credential error`
```bash
# Check endpoint URLs and keys
# Ensure region matches (southafricanorth)
```

### Slow Responses

**Render Free Tier Sleep:**
- First request after 15 min: ~30s (wake-up time)
- Solution: Use UptimeRobot to ping every 10 min

**Groq API Latency:**
- Normal: 1-3 seconds per request
- If slower: Check Groq status page

---

## Security Best Practices

### Environment Variables

✅ **DO:**
- Store all API keys in Render's environment variables
- Use "sync: false" for secrets in render.yaml
- Rotate keys periodically

❌ **DON'T:**
- Commit API keys to Git
- Share keys publicly
- Use same keys for dev and production

### API Rate Limiting

Add to `app/main.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/message/process")
@limiter.limit("10/minute")  # 10 requests per minute
async def process_message(...):
    ...
```

### CORS Configuration

Update `app/main.py` for your frontend:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://medassist.ng"],  # Your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## API Documentation

### OpenAPI/Swagger Docs

**Automatically available at:**
- `https://medassist-ai-service.onrender.com/docs` - Interactive Swagger UI
- `https://medassist-ai-service.onrender.com/redoc` - ReDoc documentation

### Backend Integration

**For Spring Boot backend:**

```java
@Service
public class AiServiceClient {
    private final String AI_SERVICE_URL = "https://medassist-ai-service.onrender.com";
    
    public MessageResponse processMessage(MessageRequest request) {
        return restTemplate.postForObject(
            AI_SERVICE_URL + "/api/v1/message/process",
            request,
            MessageResponse.class
        );
    }
}
```

---

## Rollback & Recovery

### Rollback to Previous Version

**In Render Dashboard:**
1. Go to "Deploys" tab
2. Find previous successful deploy
3. Click "Rollback to this version"

### Manual Redeploy

```bash
# In Render dashboard
Click "Manual Deploy" → "Clear build cache & deploy"
```

---

## Next Steps After Deployment

### Week 1
- ✅ Monitor logs daily
- ✅ Test all endpoints
- ✅ Set up UptimeRobot
- ✅ Configure error alerts

### Week 2
- ⏳ Integrate with Spring Boot backend
- ⏳ Add request logging
- ⏳ Monitor API costs
- ⏳ Performance testing

### Month 1
- ⏳ Collect usage metrics
- ⏳ Optimize based on real usage
- ⏳ Consider caching layer
- ⏳ Review and optimize costs

---

## Support & Resources

### Documentation
- API Docs: `https://your-service.onrender.com/docs`
- Groq Docs: https://console.groq.com/docs
- Azure Docs: https://docs.microsoft.com/azure

### Community
- Render Status: https://status.render.com
- Groq Discord: https://discord.gg/groq
- FastAPI Discord: https://discord.gg/fastapi

### Cost Optimization
- Monitor Azure usage in Azure Portal
- Use translation caching to reduce Azure costs
- Groq is FREE - no optimization needed!

---

## Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Groq API key obtained
- [ ] Azure keys configured (optional)
- [ ] render.yaml configured
- [ ] Dockerfile tested locally
- [ ] Environment variables set in Render
- [ ] Service deployed successfully
- [ ] Health check passing
- [ ] All endpoints tested
- [ ] UptimeRobot configured (optional)
- [ ] Error alerts enabled
- [ ] Documentation reviewed
- [ ] Backend team notified of API URL

---

**🎉 Your MedAssist AI Service is ready for production!**

**Live URL:** `https://medassist-ai-service.onrender.com`  
**API Docs:** `https://medassist-ai-service.onrender.com/docs`  
**Cost:** $0-8/month (FREE Groq + optional Azure)
