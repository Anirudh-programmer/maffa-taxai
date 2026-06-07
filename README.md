# 🤖 TaxAI — AI-Powered Indian Tax Advisor SaaS

A production-ready, full-stack AI Tax Advisor built for Indian taxpayers. Calculate taxes, compare regimes, analyze tax documents, and get personalized recommendations powered by **Google Gemini AI**.

![TaxAI](https://img.shields.io/badge/Stack-Next.js%2014%20%2B%20FastAPI-14b8a6?style=flat-square)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?style=flat-square)
![DB](https://img.shields.io/badge/DB-PostgreSQL%20%2B%20ChromaDB-336791?style=flat-square)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Tax Advisor** | Gemini-powered chat with deep Indian tax knowledge |
| 🧮 **Tax Calculator** | Precise Old vs New regime comparison (FY 2024-25) |
| 📄 **Document Analysis** | Upload Form 16, salary slips, ITR PDFs for AI analysis |
| 🔍 **RAG Knowledge Base** | ChromaDB + LangChain semantic retrieval of tax law |
| 📊 **Analytics Dashboard** | Track savings, consultations, documents |
| 🔐 **Auth** | Clerk authentication (Google, email) |
| 📱 **Responsive** | Mobile-first design, works on all devices |
| 🎨 **Premium UI** | Glassmorphism, animations, dark/light mode |

---

## 🏗️ Tech Stack

### Frontend
- **Next.js 14** (App Router) + TypeScript
- **Tailwind CSS** + custom design system
- **Framer Motion** for animations
- **Clerk** for authentication
- **Zustand** for state management
- **Recharts** for analytics charts
- **React Dropzone** for file uploads

### Backend
- **FastAPI** (Python) — async, modular
- **SQLAlchemy 2.0** async ORM
- **PostgreSQL** (Neon-hosted) with JSONB
- **Alembic** for migrations
- **ChromaDB** + **LangChain** for RAG
- **Google Gemini** (gemini-1.5-pro) for AI
- **PyMuPDF** for PDF text extraction

---

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- A [Clerk](https://clerk.com) account (free)
- A [Neon](https://neon.tech) PostgreSQL database (free tier)

### 1. Clone & Install

```bash
git clone <your-repo>
cd taxai

# Install frontend deps
cd frontend && npm install && cd ..

# Install backend deps
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 2. Configure Environment

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your keys

# Frontend
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with your Clerk keys
```

**Backend `.env` keys:**
```env
GEMINI_API_KEY=your-gemini-api-key-here
DATABASE_URL=postgresql+asyncpg://neondb_owner:...@...neon.tech/neondb?ssl=require
SECRET_KEY=your-random-secret-key-min-32-chars
CLERK_SECRET_KEY=sk_test_...
ALLOWED_ORIGINS=http://localhost:3000
```

**Frontend `.env.local` keys:**
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Set Up Clerk

1. Create a project at [clerk.com](https://clerk.com)
2. Enable **Google** and **Email** sign-in methods
3. Copy your publishable and secret keys to `.env.local`
4. Set redirect URLs: `http://localhost:3000/dashboard`

### 4. Run Migrations & Seed

```bash
cd backend
# Apply database migrations
alembic upgrade head

# Seed tax knowledge base + demo user
python scripts/seed.py
```

### 5. Start Development Servers

```bash
# Terminal 1 — Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) 🎉

**Demo credentials:** `demo@taxai.app` / `demo123`

---

## 🐳 Docker (One Command)

```bash
# Copy and fill environment files first
cp backend/.env.example backend/.env
# (edit backend/.env)

docker-compose up --build
```

---

## 📡 API Documentation

With the backend running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/clerk/sync` | Sync Clerk auth token |
| POST | `/api/v1/chat/stream` | Stream AI chat response (SSE) |
| GET | `/api/v1/chat/sessions` | List chat sessions |
| POST | `/api/v1/tax/calculate` | Calculate old + new regime tax |
| POST | `/api/v1/documents/upload` | Upload & analyze tax document |
| GET | `/api/v1/users/me/dashboard` | Get dashboard stats |

---

## 🚢 Deployment

### Frontend → Vercel

```bash
cd frontend
npx vercel --prod
```

Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- `NEXT_PUBLIC_API_URL` → your Render backend URL

### Backend → Render

1. Create new **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repo
3. Set:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add all environment variables from `backend/.env`

---

## 🧮 Tax Calculation Logic

All tax math is done in **pure Python** (`backend/app/services/tax_calculator.py`).

The AI **never calculates taxes** — it only explains results and provides guidance.

**FY 2024-25 rules implemented:**
- Old regime slabs (normal, senior citizen, super senior)
- New regime slabs (post Budget 2024)
- HRA exemption (Section 10(13A))
- All major deductions: 80C, 80CCD, 80D, 80E, 80G, 80TTA, 24b
- Section 87A rebate
- Surcharge (with 25% cap under new regime)
- 4% Health & Education Cess

---

## 📁 Project Structure

```
taxai/
├── frontend/                 # Next.js 14 app
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   │   ├── page.tsx      # Landing page
│   │   │   ├── dashboard/    # Dashboard
│   │   │   ├── chat/         # AI chat
│   │   │   ├── calculator/   # Tax calculator
│   │   │   ├── upload/       # Document upload
│   │   │   ├── analytics/    # Analytics
│   │   │   ├── settings/     # Settings
│   │   │   └── auth/         # Sign in/up
│   │   ├── components/       # Reusable components
│   │   ├── lib/              # API client, utils
│   │   ├── store/            # Zustand stores
│   │   └── types/            # TypeScript types
│   └── package.json
│
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── api/v1/endpoints/ # Route handlers
│   │   ├── core/             # Config, DB, Security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── ai_service.py    # Gemini AI
│   │   │   ├── rag_service.py   # ChromaDB RAG
│   │   │   ├── tax_calculator.py # Tax math
│   │   │   └── pdf_service.py   # PDF processing
│   │   └── middleware/       # Auth middleware
│   ├── alembic/              # DB migrations
│   ├── scripts/              # Seed scripts
│   └── main.py               # App entry point
│
├── docker-compose.yml
└── README.md
```

---

## 🔒 Security

- JWT tokens (7-day expiry)
- Clerk for OAuth (Google, GitHub, email)
- CORS configured per environment
- File upload validation (type + size)
- Rate limiting via SlowAPI
- Input sanitization via Pydantic
- Environment variables only (no secrets in code)

---

## ⚠️ Disclaimer

TaxAI provides educational guidance only. For complex tax situations, consult a Chartered Accountant. Tax calculations are based on publicly available FY 2024-25 rules and may not account for all individual circumstances.

---

## 📄 License

MIT — free for personal and commercial use.
