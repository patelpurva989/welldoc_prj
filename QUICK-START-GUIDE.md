# FDA Regulatory Automation Platform - Quick Start Guide

**Get up and running in 5 minutes!**

---

## Prerequisites

1. **Docker Desktop** installed and running
2. **Anthropic API Key** (Claude) - Get from: https://console.anthropic.com/

---

## Step 1: Configure Environment (2 minutes)

1. Navigate to the project folder:
   ```bash
   cd solution-1-fda-automation
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your API key:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

---

## Step 2: Start the Platform (2 minutes)

**Windows**:
```bash
quickstart.bat
```

**Linux/Mac**:
```bash
chmod +x quickstart.sh
./quickstart.sh
```

Or manually:
```bash
docker-compose up --build
```

Wait for all services to start (about 30 seconds).

---

## Step 3: Access the Platform (1 minute)

Open your browser:

1. **Dashboard**: http://localhost:3400
2. **API Docs**: http://localhost:8400/api/docs

---

## Create Your First Submission

### Option 1: Via Web UI (Recommended)

1. Go to: http://localhost:3400/submit

2. Fill in the form:
   - **Device Name**: CardioMonitor Pro
   - **Manufacturer**: MedTech Innovations
   - **Submission Type**: 510(k)
   - **Device Description**:
     ```
     Continuous cardiac monitoring device with real-time ECG,
     heart rate monitoring, and automatic arrhythmia detection.
     Features include wireless connectivity, 7-day battery life,
     and cloud-based data storage.
     ```
   - **Indications for Use**:
     ```
     For continuous monitoring of cardiac rhythm in adult patients
     at risk of arrhythmias. Intended for use in hospitals, clinics,
     and home care settings.
     ```
   - **Predicate Device Name**: HeartWatch 3000
   - **Predicate K Number**: K123456

3. Click **"Create & Generate Submission"**

4. Wait 10-30 seconds for AI to generate:
   - Complete 510(k) submission document
   - Substantial equivalence analysis
   - Compliance check report

5. View the generated submission in the dashboard!

### Option 2: Via API

```bash
# Create submission
curl -X POST http://localhost:8400/api/v1/regulatory/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "submission_type": "510k",
    "device_name": "CardioMonitor Pro",
    "manufacturer": "MedTech Innovations",
    "device_description": "Continuous cardiac monitoring device",
    "indications_for_use": "For continuous monitoring of cardiac rhythm",
    "predicate_k_number": "K123456"
  }'

# Note the ID from response, then generate documents
curl -X POST http://localhost:8400/api/v1/regulatory/generate-submission \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": 1,
    "include_predicate_analysis": true,
    "include_clinical_summary": true
  }'
```

---

## Explore the Platform

### Dashboard (http://localhost:3400)
- View all submissions
- See statistics and status
- Monitor high-risk adverse events

### New Submission (http://localhost:3400/submit)
- Create new FDA submissions
- AI auto-generates documents
- Compliance checking included

### Review Queue (http://localhost:3400/review)
- Human-in-the-loop workflow
- Review AI-generated documents
- Approve or reject submissions

### API Documentation (http://localhost:8400/api/docs)
- Interactive API explorer
- Try all endpoints
- See request/response schemas

---

## Key Features to Try

### 1. Automatic Document Generation
- Submit a new device
- AI generates complete 510(k) in 10-30 seconds
- Includes substantial equivalence analysis

### 2. Predicate Device Search
Via API:
```bash
curl http://localhost:8400/api/v1/regulatory/predicate-devices?device_name=Heart
```

### 3. Adverse Event Monitoring
Monitor FAERS database:
```bash
curl http://localhost:8400/api/v1/regulatory/adverse-events/monitor/CardioMonitor
```

### 4. Compliance Checking
Run 21 CFR Part 11 compliance check:
```bash
curl -X POST http://localhost:8400/api/v1/regulatory/compliance/check \
  -H "Content-Type: application/json" \
  -d '{"submission_id": 1}'
```

### 5. Human Review Workflow
1. Create a submission (status becomes "review_pending")
2. Go to http://localhost:3400/review
3. Click on the submission
4. Add comments and approve/reject

---

## Sample Predicate Devices

The platform includes 5 sample predicate devices:

1. **HeartWatch 3000** (K123456) - Cardiac monitor
2. **BloodFlow Analyzer** (K789012) - Doppler ultrasound
3. **GlucoseGuard Pro** (K345678) - Glucose monitor
4. **RespiMonitor Elite** (K901234) - Respiratory monitor
5. **NeuroStim System** (K567890) - TMS device

Use these K numbers when creating test submissions!

---

## Useful Commands

### View Logs
```bash
docker-compose logs -f
```

### View Specific Service Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services
```bash
docker-compose restart
```

### Stop Platform
```bash
docker-compose down
```

### Start Again
```bash
docker-compose up
```

### Rebuild After Changes
```bash
docker-compose up --build
```

---

## Troubleshooting

### "Port already in use"
**Problem**: Another app is using port 8400 or 3400

**Solution**:
```bash
# Windows - Find and kill process
netstat -ano | findstr :8400
taskkill /PID <process-id> /F

# Linux/Mac
lsof -i :8400
kill -9 <process-id>
```

### "API key not valid"
**Problem**: Claude API key is missing or invalid

**Solution**:
1. Check `.env` file has correct key
2. Verify key starts with `sk-ant-`
3. Restart services: `docker-compose restart backend`

### "Database connection failed"
**Problem**: PostgreSQL not ready

**Solution**:
```bash
# Wait a bit longer, then check
docker-compose exec postgres pg_isready -U fda_user

# If still failing, restart
docker-compose restart postgres
```

### "Frontend not loading"
**Problem**: Next.js build issues

**Solution**:
```bash
# Rebuild frontend
docker-compose up --build frontend
```

---

## What's Next?

### Try These Workflows:

1. **Create Multiple Submissions**
   - Different device types
   - Compare predicate analysis
   - Review compliance scores

2. **Test Review Workflow**
   - Create submission
   - Review as different reviewers
   - Approve sections
   - Track status changes

3. **Monitor Adverse Events**
   - Query FAERS API
   - See AI risk scoring
   - Review safety analysis

4. **Export Data**
   - Use API to get submission data
   - Parse generated documents
   - Extract compliance reports

### Customize the Platform:

1. **Add More Predicate Devices**
   - Edit `backend/seed_data.py`
   - Add your own devices
   - Run: `docker-compose exec backend python seed_data.py`

2. **Modify AI Prompts**
   - Edit agent files in `backend/app/agents/`
   - Customize system prompts
   - Adjust output formatting

3. **Extend API**
   - Add endpoints in `backend/app/api/regulatory.py`
   - Create new models in `backend/app/models/`
   - Update schemas in `backend/app/schemas/`

4. **Enhance UI**
   - Modify pages in `frontend/app/`
   - Add components in `frontend/components/`
   - Update styles with TailwindCSS

---

## Support & Resources

### Documentation
- **README**: Comprehensive platform documentation
- **API Docs**: http://localhost:8400/api/docs (when running)
- **Project Status**: See PROJECT-STATUS.md

### Architecture
- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: Next.js 14 + TailwindCSS
- **AI**: PydanticAI + Claude 3.5 Sonnet
- **Deployment**: Docker Compose

### Key Files
```
solution-1-fda-automation/
├── backend/
│   ├── app/
│   │   ├── agents/          # 4 AI agents
│   │   ├── api/             # REST endpoints
│   │   ├── models/          # Database models
│   │   └── schemas/         # Pydantic validation
│   └── seed_data.py         # Sample data
├── frontend/
│   ├── app/                 # Next.js pages
│   ├── components/          # React components
│   └── lib/                 # API client
├── docker-compose.yml       # Service orchestration
└── README.md                # Full documentation
```

---

## Success! You're Ready to Go! 🎉

You now have a fully functional FDA regulatory automation platform with:

✅ AI-powered document generation
✅ Real-time adverse event monitoring
✅ Human-in-the-loop review workflow
✅ 21 CFR Part 11 compliance checking
✅ Complete API with documentation
✅ Modern web interface

**Start automating your FDA submissions today!**

---

**Questions?** Check the API docs at http://localhost:8400/api/docs

**Need help?** Review README.md for detailed documentation

**Want to customize?** All code is well-documented and modular!
