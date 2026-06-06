# System Design: AI Lead Automation System (Aviara Labs)

This document describes the production-ready architecture designed to process, enrich, classify, and store incoming leads reliably at high scale.

---

## 1. System Architecture Diagram

The system employs a decoupled, asynchronous, worker-based architecture to handle peak traffic without bottlenecks.

```mermaid
graph TD
    %% Clients & Webhooks
    Client[Incoming Lead Webhook] -->|HTTP POST| Webhook[n8n Webhook / Gateway]
    
    %% API Gateway / n8n
    subgraph Workflow Engine (n8n)
        Webhook -->|1. Ingest & Validate| Validator[Input Validator Node]
        Validator -->|2. Dispatch Task| QueueManager{Redis Broker}
    end

    %% Queue & Workers
    subgraph Asynchronous Worker Layer
        QueueManager -->|Enrichment Job Queue| EW[Enrichment Workers]
        QueueManager -->|Classification Job Queue| CW[LLM Classify Workers]
        
        %% Third Party / LLM integrations
        EW -->|REST API| ExternalEnrich[Apollo.io / Clearbit]
        CW -->|JSON Mode| GroqLLM[Groq Cloud API]
    end

    %% Database & Notification
    EW & CW -->|Write Results| DB[(Supabase PostgreSQL / Connection Pooler)]
    DB -->|Post-Save Trigger| Routing[Router Node]
    Routing -->|Notify High Value| Slack[Slack Channel / Alerting]
    
    %% Dead Letter Queue
    QueueManager -->|Failures / Retry Limit Exceeded| DLQ[(Redis Dead Letter Queue)]
    DLQ -->|Manual Intervention / Retry Job| OpsAlert[Ops Slack Alert]

    style QueueManager fill:#D32F2F,stroke:#fff,stroke-width:2px,color:#fff
    style DB fill:#388E3C,stroke:#fff,stroke-width:2px,color:#fff
    style GroqLLM fill:#F57C00,stroke:#fff,stroke-width:2px,color:#fff
    style DLQ fill:#7B1FA2,stroke:#fff,stroke-width:2px,color:#fff
```

---

## 2. Scaling to 1,000+ Leads/Hour

A throughput of 1,000+ leads/hour translates to roughly ~0.28 leads per second on average. However, marketing campaigns or webinars can trigger flash spikes of **100+ leads per second**. To design for these bursts without system failure:

### A. Non-blocking Ingestion
- The ingestion endpoint (`n8n Webhook` or the FastAPI `/leads` handler) is completely non-blocking. It accepts the JSON payload, performs lightweight validation (Pydantic schema check), issues a unique transaction ID (`lead_id`), pushes the task to the queue, and returns an HTTP `202 Accepted` status code within **< 20ms**.

### B. Database Connection Pooling
- Supabase/PostgreSQL has limited concurrent connections. Direct connection from short-lived serverless functions or multiple workers will exhaust it.
- **Solution:** Implement **PgBouncer** or Supabase's built-in connection pooler (running in `transaction` mode) to multiplex thousands of client connections onto a small pool of actual database server connections.
- In FastAPI, we use SQLAlchemy's `AsyncSession` with `pool_size=10` and `max_overflow=20` to prevent socket starvation.

### C. Write Buffering & Bulk Inserts
- If needed, workers can buffer lead updates in Redis and perform batch database writes (e.g., writing every 5 seconds or every 50 leads) to minimize IOPS on the database.

---

## 3. Worker-Based Architecture & Queues (Redis / Celery)

Relying on synchronous HTTP chains in n8n for slow third-party API calls (Groq classification, Clearbit enrichment) introduces extreme vulnerability. If Groq takes 3 seconds to respond, n8n keeps the HTTP connection open, rapidly consuming threads/memory.

### A. Queue-Based Decoupling
- **Broker (Redis):** Acts as the message transporter.
- **Backend (FastAPI/Celery):** Manages worker processes.
- The pipeline splits into two distinct, isolated queues:
  1. **`enrichment_queue`**: Processes API integrations. I/O-bound.
  2. **`classification_queue`**: Processes LLM classification. Heavy network latency, potential rate-limit thresholds.

### B. Worker Isolation Strategy
```text
[Redis Broker]
   ├── Queue: enrichment_queue -----> [Enrichment Worker Pool] (Concurrency: 50)
   └── Queue: classification_queue -> [Groq Classifier Pool]  (Concurrency: 10)
```
- **Why?** If the Groq API gets heavily throttled or experiences high response latency, only the `classification_queue` blocks. Enrichment processing continues completely uninterrupted.

---

## 4. Idempotency Strategy

In automated pipelines, network failures often cause n8n or clients to retry webhook requests. Without idempotency, this results in duplicate leads, multiple Slack alerts, and wasted LLM credits.

### A. Deterministic Idempotency Key
1. **Source Deduplication:** Generate a SHA-256 hash from the unique combination of the lead's email and a daily/weekly salt (or just the email if it represents a unique lead).
2. **Redis Lock / Cache:**
   - On receiving a payload, check Redis: `EXISTS lead:lock:{email_hash}`.
   - If it exists, return the cached result of the running task instead of reprocessing.
   - Set lock TTL to 5 minutes to prevent race conditions during simultaneous requests.

### B. Database Level Safeguard
- The PostgreSQL schema enforces a `UNIQUE` constraint on the `email` column.
- The workflow and APIs use upsert semantics (`INSERT ... ON CONFLICT (email) DO UPDATE`).
- This guarantees that even if a parallel process bypasses the Redis lock, only a single row will exist in the database for that email address.

---

## 5. Retry and Failure Handling (DLQ & Fallbacks)

### A. Exponential Backoff & Jitter
- Network hiccups to external APIs are inevitable. Webhook and HTTP nodes in n8n are configured with:
  - **Retries**: 3
  - **Backoff policy**: Exponential backoff (e.g., retry after 5s, then 20s, then 80s) to avoid slamming the target server.

### B. Dead-Letter Queue (DLQ)
- If a lead fails all 3 retries, the worker catches the exception, updates the lead status in the DB to `failed`, and pushes the raw payload to a **Dead-Letter Queue (DLQ)** inside Redis (`queue:leads_dlq`).
- Pushing to the DLQ preserves the lead data for manual audit rather than discarding it.

### C. Alerts & Operational Fallbacks
- An **Error Trigger Node** in n8n catches any unhandled exception in the pipeline, immediately assembling the error context and sending a Slack message to `#ops-alerts` containing:
  - Lead Email
  - Failed Node Name
  - Error Details
  - Direct Link to the execution log for troubleshooting.
