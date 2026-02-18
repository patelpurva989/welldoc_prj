# FDA Regulatory Automation Platform

**AI-powered FDA submission automation with human-in-the-loop workflows**

## Overview

This platform automates FDA 510(k) premarket notification submissions using AI agents powered by Claude. It includes:

- **Regulatory Document Agent**: Auto-generates 510(k) submissions and substantial equivalence analyses
- **Clinical Evidence Synthesizer**: Analyzes and synthesizes clinical study data
- **Adverse Event Monitor**: Real-time FAERS database monitoring with AI risk assessment
- **Compliance Agent**: 21 CFR Part 11 compliance checking

## Features

### 1. Automated Document Generation
- Complete 510(k) submission documents
- Substantial equivalence analysis
- Clinical evidence synthesis
- Regulatory-compliant formatting

### 2. Predicate Device Search
- Search FDA database for predicate devices
- Automated comparison and analysis
- Substantial equivalence determination

### 3. Adverse Event Monitoring
- Real-time FAERS API integration
- AI-powered risk scoring (0-100)
- Automated event analysis and recommendations
- Safety report generation

### 4. Human-in-the-Loop Review
- Multi-reviewer workflow
- Section-by-section review
- Comment and suggestion tracking
- Approval/rejection workflow

### 5. Compliance Checking
- 21 CFR Part 11 validation
- Electronic signature verification
- Audit trail requirements
- Record retention compliance

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **AI**: PydanticAI + Claude API
- **ORM**: SQLAlchemy 2.0 (async)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: TailwindCSS
- **HTTP Client**: Axios

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Ports**: Backend (8400), Frontend (3400)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Anthropic API key (Claude)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd solution-1-fda-automation
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

3. **Start the services**
   ```bash
   docker-compose up --build
   ```

4. **Access the platform**
   - Frontend: http://localhost:3400
   - Backend API: http://localhost:8400
   - API Docs: http://localhost:8400/api/docs

### First Submission

1. Navigate to http://localhost:3400/submit
2. Fill in device information:
   - Device Name: e.g., "CardioMonitor Pro"
   - Manufacturer: e.g., "MedTech Innovations"
   - Description and indications for use
   - Predicate device (optional)
3. Click "Create & Generate Submission"
4. AI agents will generate complete submission documents
5. Review in dashboard

## API Endpoints

### Submissions
- `POST /api/v1/regulatory/submissions` - Create submission
- `GET /api/v1/regulatory/submissions` - List submissions
- `GET /api/v1/regulatory/submissions/{id}` - Get submission
- `PATCH /api/v1/regulatory/submissions/{id}` - Update submission
- `DELETE /api/v1/regulatory/submissions/{id}` - Delete submission

### Document Generation
- `POST /api/v1/regulatory/generate-submission` - Generate 510(k) documents

### Reviews (HITL)
- `POST /api/v1/regulatory/reviews` - Submit review
- `GET /api/v1/regulatory/submissions/{id}/reviews` - Get reviews

### Adverse Events
- `POST /api/v1/regulatory/adverse-events` - Report adverse event
- `GET /api/v1/regulatory/adverse-events` - List adverse events
- `GET /api/v1/regulatory/adverse-events/monitor/{device}` - Monitor FAERS

### Predicate Devices
- `GET /api/v1/regulatory/predicate-devices` - Search predicates
- `GET /api/v1/regulatory/predicate-devices/{k_number}` - Get predicate

### Compliance
- `POST /api/v1/regulatory/compliance/check` - Run compliance check
- `GET /api/v1/regulatory/compliance/checklist/{type}` - Get checklist

## AI Agents

### 1. Document Agent
**Purpose**: Generate FDA submission documents

**Capabilities**:
- Complete 510(k) submissions
- Substantial equivalence analysis
- Regulatory-compliant formatting
- Evidence-based content

**Model**: Claude 3.5 Sonnet

### 2. Evidence Agent
**Purpose**: Synthesize clinical evidence

**Capabilities**:
- Clinical study analysis
- Safety profile assessment
- Literature comparison
- Statistical interpretation

**Model**: Claude 3.5 Sonnet

### 3. Adverse Event Agent
**Purpose**: Monitor and analyze adverse events

**Capabilities**:
- FAERS API integration
- Risk scoring (0-100)
- Pattern analysis
- Safety report generation

**Model**: Claude 3.5 Sonnet

### 4. Compliance Agent
**Purpose**: Ensure 21 CFR Part 11 compliance

**Capabilities**:
- Electronic records validation
- Electronic signature verification
- Audit trail checking
- ALCOA+ data integrity

**Model**: Claude 3.5 Sonnet

## Database Schema

### Main Tables
- **submissions**: FDA submission records
- **submission_reviews**: HITL review workflow
- **adverse_events**: Adverse event tracking
- **predicate_devices**: Predicate device database

### Enums
- `SubmissionType`: 510k, pma, de_novo, ide
- `SubmissionStatus`: draft, generating, review_pending, approved, rejected, submitted
- `ComplianceStatus`: compliant, non_compliant, needs_review

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload --port 8400
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Sample Data

The platform includes sample predicate devices for testing:

```sql
INSERT INTO predicate_devices (k_number, device_name, manufacturer, device_class, indications_for_use)
VALUES
  ('K123456', 'HeartWatch 3000', 'CardioTech Inc', 'II', 'Continuous cardiac monitoring'),
  ('K789012', 'BloodFlow Analyzer', 'VascuMed Corp', 'II', 'Non-invasive blood flow measurement');
```

## Configuration

### Environment Variables

**Backend**:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ANTHROPIC_API_KEY`: Claude API key
- `CLAUDE_MODEL`: Claude model name (default: claude-3-5-sonnet-20241022)
- `FAERS_API_URL`: FDA FAERS API endpoint
- `DEBUG`: Enable debug mode

**Frontend**:
- `NEXT_PUBLIC_API_URL`: Backend API URL

### Ports
- Backend: 8400
- Frontend: 3400
- PostgreSQL: 5433 (host) / 5432 (container)
- Redis: 6379

## Compliance

### 21 CFR Part 11
This platform includes compliance checking for:
- Electronic records (Subpart B)
- Electronic signatures (Subpart C)
- Audit trail requirements
- Record retention

### ALCOA+ Principles
- Attributable
- Legible
- Contemporaneous
- Original
- Accurate
- Complete
- Consistent
- Enduring
- Available

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Deployment

### Production Deployment

1. **Update environment variables**
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure production database

2. **Build production images**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

3. **Deploy to server**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Hostinger VPS Deployment

```bash
# SSH into VPS
ssh root@your-vps-ip

# Clone repository
git clone <repo-url>
cd solution-1-fda-automation

# Configure environment
cp .env.example .env
nano .env  # Add API keys

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Monitoring

### Health Checks
- Backend: http://localhost:8400/health
- Database: `docker-compose exec postgres pg_isready`
- Redis: `docker-compose exec redis redis-cli ping`

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# View logs
docker-compose logs postgres
```

### API Key Issues
- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check API key is valid
- Ensure sufficient API credits

### Port Conflicts
```bash
# Check if ports are in use
netstat -ano | findstr :8400
netstat -ano | findstr :3400

# Stop conflicting services or change ports in docker-compose.yml
```

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Email: support@example.com
- Documentation: http://localhost:8400/api/docs

## Roadmap

### Phase 1 (Current)
- ✅ 510(k) submission automation
- ✅ HITL review workflow
- ✅ Adverse event monitoring
- ✅ Compliance checking

### Phase 2 (Planned)
- [ ] PMA submission support
- [ ] De Novo classification
- [ ] Integration with FDA ESG
- [ ] Multi-tenant support

### Phase 3 (Future)
- [ ] Machine learning for risk prediction
- [ ] Automated literature search
- [ ] Real-time FDA database sync
- [ ] Mobile app for reviewers

---

**Built with Claude AI** | **Version 1.0.0** | **January 2026**
