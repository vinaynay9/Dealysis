# Deploying to Render

## Quick Setup

### 1. **Configure Render Service**

In your Render dashboard:
- **Root Directory**: `vc-memo-backend`
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Python Version**: Will use `runtime.txt` (Python 3.12.7)

### 2. **Set Environment Variable**

Add in Render dashboard under Environment:
- **Key**: `OPENAI_API_KEY`
- **Value**: Your OpenAI API key

### 3. **Deploy**

Push to your Git repository and Render will auto-deploy.

## Manual Configuration Steps

If not using `render.yaml`:

1. **Create New Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect your repository

2. **Service Configuration**
   - **Name**: `dealysis-api`
   - **Root Directory**: `vc-memo-backend` ⚠️ **IMPORTANT**
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

3. **Environment Variables**
   - `OPENAI_API_KEY` - Your OpenAI API key (required)

4. **Advanced Settings** (optional)
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Yes

## Using render.yaml (Blueprint)

A `render.yaml` file is included for automated deployment:

```bash
# Push your code
git add .
git commit -m "Deploy to Render"
git push

# In Render Dashboard:
# New → Blueprint → Connect your repo
```

The blueprint will automatically configure everything!

## Troubleshooting

### Issue: Python 3.13 being used instead of 3.12

**Solution**: Ensure `runtime.txt` exists in `vc-memo-backend/` with:
```
python-3.12.7
```

And that **Root Directory** in Render is set to `vc-memo-backend`.

### Issue: Pandas compilation errors

If you see Cython/pandas build errors, it's likely a Python version mismatch. Ensure:
- `runtime.txt` specifies Python 3.12.x
- Root directory is set correctly to `vc-memo-backend`

### Issue: Module not found errors

Make sure Build Command includes:
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

### Issue: Port binding errors

The app automatically uses Render's `$PORT` environment variable. No configuration needed.

## Verifying Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app.onrender.com/health

# API info
curl https://your-app.onrender.com/

# API docs (in browser)
https://your-app.onrender.com/docs
```

## Performance Notes

**Free Tier:**
- Service spins down after 15 minutes of inactivity
- First request after idle may take 30-60 seconds
- Limited to 512 MB RAM

**Starter Tier ($7/month):**
- Always on
- 1 GB RAM
- Better for production use

## Security Recommendations

1. **Update CORS settings** in `main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend.com"],  # ← Change this
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Add authentication** for production use

3. **Rate limiting** - Consider adding rate limiting middleware

## Next Steps

- Set up monitoring/logging
- Add Redis for job storage (instead of in-memory)
- Configure custom domain
- Set up CI/CD pipeline

---

**Your API will be live at**: `https://your-service-name.onrender.com` 🚀

