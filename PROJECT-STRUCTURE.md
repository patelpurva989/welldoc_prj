# FDA Regulatory Automation Platform - Project Structure

## Complete File Tree

```
solution-1-fda-automation/
│
├── 📄 README.md                        # Comprehensive documentation
├── 📄 PROJECT-STATUS.md                # Deployment status & checklist
├── 📄 QUICK-START-GUIDE.md            # 5-minute quickstart
├── 📄 PROJECT-STRUCTURE.md            # This file
│
├── 🐳 docker-compose.yml              # Service orchestration
├── 📄 .env.example                     # Environment template
├── 📄 .gitignore                       # Git exclusions
│
├── 🚀 quickstart.sh                    # Linux/Mac quickstart
├── 🚀 quickstart.bat                   # Windows quickstart
│
├── 📁 backend/                         # FastAPI Backend (Port 8400)
│   ├── 🐳 Dockerfile                   # Backend container
│   ├── 📄 requirements.txt             # Python dependencies
│   ├── 🌱 seed_data.py                 # Sample data seeding
│   │
│   └── 📁 app/
│       ├── 📄 __init__.py
│       ├── 🚀 main.py                  # FastAPI application
│       │
│       ├── 📁 core/                    # Core configuration
│       │   ├── 📄 __init__.py
│       │   ├── ⚙️ config.py            # Settings & env vars
│       │   └── 💾 database.py          # Database setup
│       │
│       ├── 📁 models/                  # SQLAlchemy models
│       │   ├── 📄 __init__.py
│       │   └── 📋 submission.py        # Database schema
│       │       ├── Submission
│       │       ├── SubmissionReview
│       │       ├── AdverseEvent
│       │       └── PredicateDevice
│       │
│       ├── 📁 schemas/                 # Pydantic schemas
│       │   ├── 📄 __init__.py
│       │   └── 📋 submission.py        # API validation
│       │       ├── SubmissionCreate
│       │       ├── SubmissionResponse
│       │       ├── ReviewCreate
│       │       ├── AdverseEventCreate
│       │       └── ComplianceCheckRequest
│       │
│       ├── 📁 api/                     # REST API endpoints
│       │   ├── 📄 __init__.py
│       │   └── 🌐 regulatory.py        # Main API routes
│       │       ├── POST /submissions
│       │       ├── GET /submissions
│       │       ├── POST /generate-submission
│       │       ├── POST /reviews
│       │       ├── GET /adverse-events
│       │       ├── GET /predicate-devices
│       │       └── POST /compliance/check
│       │
│       ├── 📁 agents/                  # AI Agents (Claude)
│       │   ├── 📄 __init__.py
│       │   ├── 🤖 document_agent.py    # 510(k) generation
│       │   ├── 🤖 evidence_agent.py    # Clinical synthesis
│       │   ├── 🤖 adverse_event_agent.py # FAERS monitoring
│       │   └── 🤖 compliance_agent.py  # 21 CFR Part 11
│       │
│       └── 📁 services/                # Business logic (empty - can extend)
│           └── 📄 __init__.py
│
├── 📁 frontend/                        # Next.js Frontend (Port 3400)
│   ├── 🐳 Dockerfile                   # Frontend container
│   ├── 📄 package.json                 # Node dependencies
│   ├── 📄 tsconfig.json                # TypeScript config
│   ├── 📄 tailwind.config.ts           # TailwindCSS config
│   ├── 📄 next.config.js               # Next.js config
│   ├── 📄 postcss.config.js            # PostCSS config
│   │
│   ├── 📁 app/                         # Next.js 14 App Router
│   │   ├── 🎨 layout.tsx               # Root layout
│   │   ├── 🎨 page.tsx                 # Dashboard (home)
│   │   ├── 🎨 globals.css              # Global styles
│   │   │
│   │   ├── 📁 submit/                  # New submission page
│   │   │   └── 🎨 page.tsx
│   │   │
│   │   └── 📁 review/                  # Review workflow page
│   │       └── 🎨 page.tsx
│   │
│   ├── 📁 components/                  # React components
│   │   ├── 🧩 SubmissionCard.tsx       # Submission display
│   │   └── 🧩 ComplianceChecker.tsx    # Compliance UI
│   │
│   └── 📁 lib/                         # Utilities
│       └── 🌐 api.ts                   # API client & types
│
└── 📁 tests/                           # Tests (can be added)
    └── 📄 (test files here)
```

---

## Component Breakdown

### Backend Services

#### 1. Core Configuration (`app/core/`)
- **config.py**: Environment variables, API keys, database URLs
- **database.py**: SQLAlchemy engine, session management

#### 2. Database Layer (`app/models/`)
- **submission.py**:
  - `Submission`: Main submission records
  - `SubmissionReview`: HITL review workflow
  - `AdverseEvent`: Safety monitoring
  - `PredicateDevice`: Reference device database

#### 3. API Layer (`app/schemas/`)
- **submission.py**: Pydantic models for request/response validation

#### 4. REST API (`app/api/`)
- **regulatory.py**: Complete CRUD + AI generation endpoints

#### 5. AI Agents (`app/agents/`)
All powered by Claude 3.5 Sonnet via PydanticAI:

| Agent | Purpose | Key Functions |
|-------|---------|---------------|
| **Document Agent** | Generate 510(k) documents | `generate_510k_submission()`, `generate_substantial_equivalence_analysis()` |
| **Evidence Agent** | Synthesize clinical data | `synthesize_clinical_evidence()`, `analyze_safety_data()` |
| **Adverse Event Agent** | Monitor FAERS | `analyze_adverse_event()`, `monitor_faers_database()` |
| **Compliance Agent** | CFR Part 11 checking | `check_submission_compliance()`, `validate_electronic_signature()` |

---

### Frontend Structure

#### 1. Pages (`app/`)
| Page | Route | Purpose |
|------|-------|---------|
| **page.tsx** | `/` | Dashboard with stats, recent submissions, high-risk events |
| **submit/page.tsx** | `/submit` | New submission form with AI generation |
| **review/page.tsx** | `/review` | HITL review workflow with filtering |

#### 2. Components (`components/`)
| Component | Purpose |
|-----------|---------|
| **SubmissionCard** | Display submission with status, compliance, actions |
| **ComplianceChecker** | Run and display 21 CFR Part 11 checks |

#### 3. API Client (`lib/`)
- **api.ts**: TypeScript client with type-safe functions for all endpoints

---

## Technology Stack

### Backend
```yaml
Framework: FastAPI 0.109.0
Language: Python 3.11+
Database: PostgreSQL 15
Cache: Redis 7
ORM: SQLAlchemy 2.0 (async)
Validation: Pydantic v2
AI Framework: PydanticAI 0.0.13
AI Model: Claude 3.5 Sonnet (Anthropic)
Server: Uvicorn
```

### Frontend
```yaml
Framework: Next.js 14 (App Router)
Language: TypeScript 5
Styling: TailwindCSS v4
HTTP Client: Axios 1.6.5
Date Handling: date-fns 3.2.0
Runtime: Node.js 20
```

### Infrastructure
```yaml
Containerization: Docker + Docker Compose
Database: PostgreSQL 15-alpine
Cache: Redis 7-alpine
Ports:
  - Backend: 8400
  - Frontend: 3400
  - PostgreSQL: 5433 (host) / 5432 (container)
  - Redis: 6379
```

---

## Data Flow

### 1. Create Submission Flow
```
User fills form → Frontend (submit/page.tsx)
  ↓
API Client (lib/api.ts) → POST /api/v1/regulatory/submissions
  ↓
Backend API (api/regulatory.py) → Creates Submission record
  ↓
Database (PostgreSQL) → Stores submission
  ↓
Response → Frontend updates dashboard
```

### 2. Document Generation Flow
```
User clicks "Generate" → Frontend
  ↓
POST /generate-submission → Backend API
  ↓
Document Agent → Calls Claude API
  ↓
Claude generates 510(k) → Returns structured document
  ↓
Evidence Agent → Analyzes clinical data (if provided)
  ↓
Compliance Agent → Runs CFR Part 11 check
  ↓
Database → Updates submission with generated docs
  ↓
Response → Frontend displays results
```

### 3. Adverse Event Monitoring Flow
```
GET /adverse-events/monitor/{device} → Backend API
  ↓
Adverse Event Agent → Queries FDA FAERS API
  ↓
For each event → AI analyzes and scores risk (0-100)
  ↓
Database → Stores events with AI analysis
  ↓
Response → Dashboard shows high-risk events
```

### 4. Review Workflow Flow
```
User views submission → Frontend (review/page.tsx)
  ↓
User adds comments → POST /reviews
  ↓
Backend → Creates SubmissionReview record
  ↓
Database → Links review to submission
  ↓
If approved → Updates submission status
  ↓
Response → Frontend refreshes status
```

---

## API Endpoint Map

### Submissions
```
POST   /api/v1/regulatory/submissions              Create
GET    /api/v1/regulatory/submissions              List all
GET    /api/v1/regulatory/submissions/{id}         Get one
PATCH  /api/v1/regulatory/submissions/{id}         Update
DELETE /api/v1/regulatory/submissions/{id}         Delete
```

### AI Generation
```
POST   /api/v1/regulatory/generate-submission      Generate docs
```

### Reviews (HITL)
```
POST   /api/v1/regulatory/reviews                  Create review
GET    /api/v1/regulatory/submissions/{id}/reviews Get reviews
```

### Adverse Events
```
POST   /api/v1/regulatory/adverse-events           Report event
GET    /api/v1/regulatory/adverse-events           List events
GET    /api/v1/regulatory/adverse-events/monitor/{device} Monitor FAERS
```

### Predicate Devices
```
GET    /api/v1/regulatory/predicate-devices        Search
GET    /api/v1/regulatory/predicate-devices/{k}    Get one
```

### Compliance
```
POST   /api/v1/regulatory/compliance/check         Run check
GET    /api/v1/regulatory/compliance/checklist/{type} Get checklist
```

---

## Database Schema

### submissions
```sql
id                              SERIAL PRIMARY KEY
submission_type                 ENUM (510k, pma, de_novo, ide)
status                          ENUM (draft, generating, review_pending, ...)
device_name                     VARCHAR(255)
device_description              TEXT
manufacturer                    VARCHAR(255)
indications_for_use             TEXT
predicate_device_name           VARCHAR(255)
predicate_k_number              VARCHAR(50)
clinical_data                   JSON
generated_submission            TEXT
substantial_equivalence_analysis TEXT
compliance_status               ENUM (compliant, non_compliant, needs_review)
compliance_report               JSON
created_at                      TIMESTAMP
updated_at                      TIMESTAMP
submitted_at                    TIMESTAMP
```

### submission_reviews
```sql
id                  SERIAL PRIMARY KEY
submission_id       INTEGER FK → submissions.id
reviewer_name       VARCHAR(255)
reviewer_email      VARCHAR(255)
section_reviewed    VARCHAR(100)
comments            TEXT
suggested_changes   TEXT
approved            INTEGER (-1, 0, 1)
created_at          TIMESTAMP
reviewed_at         TIMESTAMP
```

### adverse_events
```sql
id              SERIAL PRIMARY KEY
submission_id   INTEGER FK → submissions.id (nullable)
event_id        VARCHAR(100) UNIQUE
device_name     VARCHAR(255)
event_type      VARCHAR(100)
severity        VARCHAR(50)
description     TEXT
patient_age     INTEGER
patient_sex     VARCHAR(10)
event_date      TIMESTAMP
reported_date   TIMESTAMP
ai_analysis     TEXT
risk_score      INTEGER (0-100)
created_at      TIMESTAMP
```

### predicate_devices
```sql
id                          SERIAL PRIMARY KEY
k_number                    VARCHAR(50) UNIQUE
device_name                 VARCHAR(255)
manufacturer                VARCHAR(255)
device_class                VARCHAR(10)
product_code                VARCHAR(10)
indications_for_use         TEXT
technological_characteristics JSON
performance_data            JSON
decision_date               TIMESTAMP
decision                    VARCHAR(50)
created_at                  TIMESTAMP
updated_at                  TIMESTAMP
```

---

## File Size Estimates

```
Total Project Size: ~150 KB (excluding node_modules, venv, .next)

Backend:
  agents/        ~40 KB (4 files × ~10 KB each)
  api/           ~16 KB (1 large file)
  models/        ~5 KB
  schemas/       ~4 KB
  core/          ~2 KB
  seed_data.py   ~6 KB

Frontend:
  app/           ~15 KB (3 pages)
  components/    ~5 KB (2 components)
  lib/           ~6 KB (API client)

Config:
  Docker files   ~2 KB
  package.json   ~1 KB
  requirements.txt ~1 KB

Documentation:
  README.md      ~12 KB
  PROJECT-STATUS.md ~10 KB
  QUICK-START-GUIDE.md ~8 KB
```

---

## Environment Variables

### Required
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx    # Claude API key (REQUIRED)
DATABASE_URL=postgresql://...      # PostgreSQL connection
```

### Optional
```env
REDIS_URL=redis://redis:6379/0     # Redis cache
FAERS_API_URL=https://...          # FDA FAERS API
DEBUG=True                          # Debug mode
SECRET_KEY=your-secret-key          # JWT secret
CLAUDE_MODEL=claude-3-5-sonnet-20241022 # Model version
```

---

## Development Workflow

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8400
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Database Operations
```bash
# Seed data
docker-compose exec backend python seed_data.py

# Database shell
docker-compose exec postgres psql -U fda_user -d fda_regulatory
```

### Logs
```bash
docker-compose logs -f                # All services
docker-compose logs -f backend        # Backend only
docker-compose logs -f frontend       # Frontend only
```

---

## Deployment Checklist

- [x] Dockerfile for backend
- [x] Dockerfile for frontend
- [x] docker-compose.yml
- [x] .env.example
- [x] Health check endpoints
- [x] Database persistence (volumes)
- [x] CORS configuration
- [x] Error handling
- [x] Input validation
- [x] Sample data seeding
- [x] Quickstart scripts
- [x] Complete documentation

---

## Next Steps for Customization

### Add New Features
1. Create new model in `backend/app/models/`
2. Create schema in `backend/app/schemas/`
3. Add API endpoints in `backend/app/api/`
4. Create frontend page in `frontend/app/`
5. Add API client functions in `frontend/lib/api.ts`

### Add New AI Agent
1. Create agent file in `backend/app/agents/`
2. Define system prompt and functions
3. Import and use in `backend/app/api/regulatory.py`

### Add Authentication
1. Install: `pip install python-jose[cryptography] passlib[bcrypt]`
2. Create auth models and endpoints
3. Add JWT token generation
4. Protect routes with dependencies

---

**Project Structure Version**: 1.0.0
**Last Updated**: January 30, 2026
