# AI-Powered Lead Automation System (Aviara Labs)

This is a production-oriented AI Lead Automation System built to ingest, enrich, classify, store, and route leads automatically in real-time.

---

## Folder Structure

```text
Aviara labs/
├── README.md                 # System overview, setup instructions & API reference
├── system_design.md          # Architectural scaling, queues, & reliability design
├── docker-compose.yml        # Multi-container orchestration (FastAPI, Postgres, Redis)
├── db/
│   └── schema.sql            # PostgreSQL DDL table schema & indices
├── n8n/
│   └── workflow.json         # Exported n8n workflow JSON ready for import
└── backend/
    ├── Dockerfile            # Production multi-stage Docker build
    ├── requirements.txt      # Python package dependencies
    ├── .env.example          # Template for environment variables
    └── app/
        ├── __init__.py
        ├── main.py           # FastAPI server initialization & middleware
        ├── config.py         # Config loader using Pydantic Settings
        ├── database.py       # Async SQL Alchemy DB connection pool & session
        ├── models.py         # Lead ORM database model
        ├── schemas.py        # Pydantic validation schemas
        ├── routers/
        │   ├── __init__.py
        │   ├── enrich.py     # HTTP route POST /enrich
        │   └── classify.py   # HTTP route POST /classify
        └── services/
            ├── __init__.py
            ├── enrichment.py # Email-domain heuristic enrichment engine
            └── groq_llm.py   # Groq SDK AI classification with local fallbacks
```

---

## Features

- **Automated Workflow (n8n)**: Fully handles webhook triggers, input validation, backend API calling, Postgres database storage, conditional Slack alerts, and retry logging.
- **FastAPI Backend**: Uses an asynchronous event loop with `asyncpg` for PostgreSQL transactions, and incorporates robust input validation via Pydantic.
- **Database Indexing**: Pre-configured indices on key query paths (`email`, `status`, `created_at`) to optimize read/write performance.
- **AI Classification**: Integrates with Groq Cloud Cloud APIs (Llama model) using structured JSON output. Includes deterministic fallback keyword classification for resilience.
- **Dockerized Architecture**: Launches fully configured local environments (Database, Caching Broker, Backend app) using a single command.

---

## Getting Started

### 1. Local Run with Docker Compose (Recommended)

To run the entire ecosystem (FastAPI Backend, PostgreSQL, and Redis) locally with all dependencies pre-installed:

```bash
# Clone the repository and navigate to the directory
cd "Aviara labs"

# Copy environment template
cp backend/.env.example .env

# Fire up all services
docker-compose up -d --build
```

- **FastAPI API Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.
- **PostgreSQL Database**: Accessible on `localhost:5432` (User: `postgres`, Password: `postgres`, DB: `leads_db`).
- **Redis Service**: Accessible on `localhost:6379`.

---

### 2. Manual Local Installation

If you prefer to run the Python backend service directly on your machine:

#### Prerequisites
- Python 3.10+
- PostgreSQL server running locally or on Supabase.

#### Steps
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your configuration .env file
cp .env.example .env
# Edit .env file and paste your GROQ_API_KEY & Database URLs

# Run application locally
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

### 3. Importing n8n Workflow

1. Open your n8n workspace.
2. Click on the **Workflow Settings Menu** (top-right three dots).
3. Select **Import from File**.
4. Choose the `n8n/workflow.json` file.
5. Setup your environment credentials:
   - Configure your **Postgres Connection node** pointing to your PostgreSQL / Supabase server.
   - Configure your **Slack Credential node** to push notifications.
6. Click **Save** and toggle the workflow to **Active**.

---

## API Reference

### 1. Lead Data Enrichment
Enriches corporate lead details from an email domain.

- **URL**: `/enrich`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`
  - `X-API-KEY: <secret-token>` (Optional, if configured)
- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "email": "john@stripe.com",
    "company": "Stripe"
  }
  ```
- **Response Body (200 OK)**:
  ```json
  {
    "linkedin_url": "https://linkedin.com/in/john-doe?org=stripe",
    "company_size": "5,000 - 10,000",
    "industry": "Financial Technology (Fintech)"
  }
  ```

---

### 2. AI Intent Classification
Classifies lead request messages into structured business categories.

- **URL**: `/classify`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "message": "I am interested in setting up a call to discuss pricing and demo options for our enterprise tier."
  }
  ```
- **Response Body (200 OK)**:
  ```json
  {
    "intent": "sales_enquiry",
    "confidence": 0.9654
  }
  ```

*Intents categorizations supported:* `sales_enquiry`, `support`, `job_application`, `partnership`, `spam`, `other`.

---

### 3. System Health Check
Verifies status of backend router and active PostgreSQL connection.

- **URL**: `/health`
- **Method**: `GET`
- **Response Body (200 OK)**:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "environment": "development"
  }
  ```
