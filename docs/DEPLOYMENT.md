# Deployment Guide

## Frontend → Vercel

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → Import repo
3. Set **Root Directory** to `frontend`
4. Add environment variables:
   ```
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
   CLERK_SECRET_KEY=sk_live_...
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
   ```
5. Deploy → Done!

---

## Backend → Render

1. Go to [render.com](https://render.com) → New Web Service
2. Connect GitHub repo
3. Configure:
   - **Name**: taxai-backend
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   ```
   GEMINI_API_KEY=AIzaSy...
   DATABASE_URL=postgresql+asyncpg://neondb_owner:...@...neon.tech/neondb?ssl=require
   SECRET_KEY=<random-64-char-string>
   CLERK_SECRET_KEY=sk_live_...
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ENVIRONMENT=production
   ```
5. Deploy!

---

## Database → Neon (PostgreSQL)

Already configured. Just ensure `DATABASE_URL` is set correctly.

To run migrations manually:
```bash
cd backend
DATABASE_URL="your-neon-url" alembic upgrade head
```

---

## Clerk Setup

1. Create account at [clerk.com](https://clerk.com)
2. Create application → Enable:
   - Email/Password
   - Google OAuth
3. Set **Redirect URLs**:
   - Sign-in: `https://your-app.vercel.app/dashboard`
   - Sign-up: `https://your-app.vercel.app/dashboard`
4. Copy keys to both frontend and backend env vars

---

## Post-Deployment Checklist

- [ ] Backend `/health` returns 200
- [ ] Database migrations applied
- [ ] Tax knowledge base seeded (check logs)
- [ ] Clerk redirects working
- [ ] File upload directory writable on Render
- [ ] CORS allows your Vercel domain
- [ ] Gemini API key valid

---

## Scaling Notes

- **ChromaDB**: For production at scale, consider migrating to Pinecone or Weaviate
- **File Storage**: Move uploads to S3/GCS instead of local disk
- **Redis**: Add Redis for session caching and rate limiting
- **Background Jobs**: Use Celery + Redis for document processing
