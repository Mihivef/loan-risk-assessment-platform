# Loan Risk Assessment Platform
### Go (Gin) + Java (Spring Boot) + Python (FastAPI) + PostgreSQL

---

## Database Choice: PostgreSQL 

### Why PostgreSQL for this system?

| Requirement | Why PostgreSQL |
|---|---|
| **Structured financial data** | Loans have fixed schemas — relational is the right fit |
| **ACID transactions** | Money operations must be atomic. PostgreSQL guarantees this. |
| **RBI audit trail** | Regulators require complete, queryable history of every decision |
| **Complex queries** | Dashboard stats, approval rates, risk distribution — SQL handles these cleanly |
| **JSONB support** | `risk_factors` and `flags` are variable-length arrays — stored as JSONB |
| **Industry standard** | Used by HDFC, ICICI, Axis for core banking |

### Why NOT other databases?
- **MySQL** — lacks advanced JSONB, weaker window functions
- **MongoDB** — no transactions, bad for financial data
- **Redis** — in-memory only, not for persistent loan records (use for caching on top)
- **SQLite** — single-writer, can't handle concurrent services

### Database Schema — 3 Tables, 1 per Service

```
┌─────────────────────────────────┐
│   loan_applications             │  ← Go Gateway owns this
│   (Go Gateway writes/reads)     │
│   Columns: id, applicant_name,  │
│   loan_type, status, risk_band, │
│   ml_credit_score, monthly_emi  │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│   policy_decisions              │  ← Java Engine owns this
│   (Java writes on every eval)   │
│   Columns: application_id,      │
│   decision, interest_rate,      │
│   rejection_reason              │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│   ml_score_logs                 │  ← Python Scorer owns this
│   (Python writes every score)   │
│   Columns: application_id,      │
│   score_type, ml_credit_score,  │
│   fraud_probability, flags      │
└─────────────────────────────────┘
```

Each service owns its table — no service writes to another service's table. This is the microservices data isolation pattern.

---

## Project Structure

```
loan-risk/
│
├── docker-compose.yml           ← Start EVERYTHING in one command
├── db-init/
│   └── init.sql                 ← PostgreSQL schema + seed data
│
├── go-gateway/                  ← Port 8080 (public-facing)
│   ├── main.go
│   ├── go.mod
│   ├── Dockerfile
│   ├── models/models.go         ← All structs + inter-service payloads
│   ├── middleware/auth.go       ← JWT-style token auth + RequireRole
│   ├── clients/clients.go       ← HTTP calls to Python + Java
│   ├── db/
│   │   ├── postgres.go          ← pgxpool connection
│   │   └── repository.go        ← SQL queries (replaces in-memory store)
│   ├── handlers/handlers.go     ← Full orchestration logic
│   ├── routes/routes.go         ← Route groups + middleware wiring
│   └── store/store.go           ← In-memory store (dev without DB)
│
├── python-scorer/               ← Port 8000 (internal)
│   ├── main.py                  ← FastAPI app + DB lifecycle
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── models/schemas.py        ← Pydantic request/response models
│   ├── services/
│   │   ├── credit_scorer.py     ← Weighted ML credit risk model
│   │   └── fraud_checker.py     ← Rule-based fraud detection
│   ├── routers/score_router.py  ← FastAPI endpoints + DB logging
│   └── db/database.py           ← asyncpg connection + ml_score_logs
│
└── java-engine/                 ← Port 8081 (internal)
    ├── pom.xml
    ├── Dockerfile
    └── src/main/java/com/loanrisk/
        ├── LoanPolicyEngineApplication.java   ← Spring Boot entry point
        ├── CorsConfig.java                    ← Allow calls from Go
        ├── model/
        │   ├── PolicyEvalRequest.java
        │   ├── PolicyEvalResponse.java
        │   ├── EmiRequest.java
        │   ├── EmiResponse.java
        │   └── PolicyDecisionEntity.java      ← JPA entity → policy_decisions table
        ├── rules/LendingPolicyRules.java       ← All lending policy rules
        ├── service/
        │   ├── PolicyEngineService.java        ← Orchestrates rules + persists to DB
        │   └── PolicyDecisionRepository.java  ← Spring Data JPA repository
        └── controller/
            ├── PolicyEngineController.java     ← REST endpoints
            └── GlobalExceptionHandler.java     ← Clean error responses to Go
```

---

## How to Run

### Option A: Docker (Recommended — starts everything)
```bash
docker-compose up --build
# PostgreSQL + Python + Java + Go all start in the right order
# Wait ~60s for Java to compile and start
```

### Option B: Manual (one terminal per service)

**Step 1 — Start PostgreSQL**
```bash
# Using Docker just for the database:
docker run -d \
  --name loan_pg \
  -e POSTGRES_DB=loan_risk_db \
  -e POSTGRES_USER=loan_user \
  -e POSTGRES_PASSWORD=loan_pass \
  -p 5432:5432 \
  postgres:16-alpine
```

**Step 2 — Start Python scorer**
```bash
cd python-scorer
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload
```

**Step 3 — Start Java engine**
```bash
cd java-engine
mvn spring-boot:run
# Takes ~30s to compile
```

**Step 4 — Start Go gateway**
```bash
cd go-gateway
go mod download
go run main.go
```

---

## Test with cURL — Full Flow

### 1. Health checks (all 3 services)
```bash
curl http://localhost:8080/health   # Go
curl http://localhost:8000/health   # Python
curl http://localhost:8081/engine/health  # Java
```

### 2. EMI Calculator (no application needed)
```bash
# Calculate EMI for ₹5,00,000 at 10.5% for 36 months
curl "http://localhost:8080/api/emi?principal=500000&rate=10.5&tenure_months=36" \
  -H "Authorization: token-customer"

# Expected: monthly_emi ≈ ₹16,249
```

### 3. Submit a GOOD loan application (should get APPROVED)
```bash
curl -X POST http://localhost:8080/api/applications \
  -H "Authorization: token-customer" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_name":         "Sneha Iyer",
    "applicant_email":        "sneha.iyer@example.com",
    "applicant_phone":        "9876543220",
    "loan_type":              "personal",
    "requested_amount":       400000,
    "tenure_months":          36,
    "purpose":                "Wedding expenses and travel",
    "annual_income":          960000,
    "existing_monthly_emis":  3000,
    "employment_type":        "salaried",
    "employer_name":          "Infosys",
    "years_employed":         3.5,
    "cibil_score":            760
  }'
# Expected: APPROVED with ~10.5% rate
```

### 4. Submit a HIGH RISK application (should get REJECTED)
```bash
curl -X POST http://localhost:8080/api/applications \
  -H "Authorization: token-customer" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_name":         "Test Applicant",
    "applicant_email":        "test@example.com",
    "applicant_phone":        "9876543221",
    "loan_type":              "personal",
    "requested_amount":       500000,
    "tenure_months":          24,
    "purpose":                "Debt consolidation",
    "annual_income":          300000,
    "existing_monthly_emis":  18000,
    "employment_type":        "self_employed",
    "employer_name":          "Self",
    "years_employed":         0.5,
    "cibil_score":            580
  }'
# Expected: REJECTED — CIBIL too low + high DTI
```

### 5. Submit a FRAUD-flagged application
```bash
curl -X POST http://localhost:8080/api/applications \
  -H "Authorization: token-customer" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_name":         "Suspicious Person",
    "applicant_email":        "test@mailinator.com",
    "applicant_phone":        "9999999999",
    "loan_type":              "personal",
    "requested_amount":       1400000,
    "tenure_months":          60,
    "purpose":                "Investment purposes",
    "annual_income":          100000,
    "existing_monthly_emis":  0,
    "employment_type":        "salaried",
    "employer_name":          "ABC Pvt Ltd",
    "years_employed":         1,
    "cibil_score":            700
  }'
# Expected: REJECTED — fraud flags (disposable email + suspicious phone + blacklisted employer)
```

### 6. Submit a HOME LOAN (large amount)
```bash
curl -X POST http://localhost:8080/api/applications \
  -H "Authorization: token-customer" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_name":         "Vikram Singh",
    "applicant_email":        "vikram@example.com",
    "applicant_phone":        "9876543230",
    "loan_type":              "home",
    "requested_amount":       3500000,
    "tenure_months":          240,
    "purpose":                "Purchase of 3BHK apartment in Bangalore",
    "annual_income":          2400000,
    "existing_monthly_emis":  10000,
    "employment_type":        "salaried",
    "employer_name":          "Google",
    "years_employed":         6,
    "cibil_score":            830
  }'
# Expected: APPROVED with best rate + loyalty discount (6 years employed)
```

### 7. List all applications (loan officer)
```bash
curl http://localhost:8080/api/applications \
  -H "Authorization: token-loan-officer"
```

### 8. Filter by status
```bash
curl "http://localhost:8080/api/applications?status=approved" \
  -H "Authorization: token-loan-officer"

curl "http://localhost:8080/api/applications?status=rejected" \
  -H "Authorization: token-loan-officer"
```

### 9. Get single application detail
```bash
curl http://localhost:8080/api/applications/1 \
  -H "Authorization: token-customer"
```

### 10. Manual status override (loan officer)
```bash
curl -X PUT http://localhost:8080/api/applications/2/status \
  -H "Authorization: token-loan-officer" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "notes": "Manual approval after document verification"}'
```

### 11. Dashboard stats (admin only)
```bash
curl http://localhost:8080/api/dashboard/stats \
  -H "Authorization: token-admin"
```

### 12. Get ML scoring factors (explains model)
```bash
curl http://localhost:8000/score/factors/1
```

### 13. Get Java policy for a loan type
```bash
curl http://localhost:8081/engine/policy/home
curl http://localhost:8081/engine/policy/personal
curl http://localhost:8081/engine/policy/vehicle
```

### 14. Try submitting as loan-officer (should get 403)
```bash
curl -X POST http://localhost:8080/api/applications \
  -H "Authorization: token-loan-officer" \
  -H "Content-Type: application/json" \
  -d '{"applicant_name":"X","applicant_email":"x@x.com","applicant_phone":"123","loan_type":"personal","requested_amount":100000,"tenure_months":12,"purpose":"testing","annual_income":500000,"employment_type":"salaried","employer_name":"X","cibil_score":700}'
# Expected: 403 — only customers can apply
```

### 15. No auth (should get 401)
```bash
curl http://localhost:8080/api/applications
```

---

## Token Reference

| Token | Role | Can do |
|---|---|---|
| `token-customer` | customer | Submit applications, view own |
| `token-loan-officer` | loan_officer | List all, update status |
| `token-admin` | admin | Everything + dashboard stats |

---

## The 5-Step Loan Pipeline

```
Customer POSTs application
        │
        ▼
  Go Gateway (:8080)
  ├─ Validates request (binding tags)
  ├─ Saves to loan_applications (PostgreSQL)
        │
        ▼ HTTP POST /score/credit-risk
  Python FastAPI (:8000)
  ├─ Runs weighted ML model (CIBIL 35%, DTI 25%, Employment 15%, ...)
  ├─ Returns: ml_score (0–1), risk_band, risk_factors
  ├─ Logs to ml_score_logs (PostgreSQL)
        │
        ▼ HTTP POST /score/fraud-check
  Python FastAPI (:8000)
  ├─ Checks email domain, phone pattern, employer blacklist, income ratio
  ├─ Returns: fraud_probability, is_suspicious, flags
  ├─ Logs to ml_score_logs (PostgreSQL)
        │
        ▼ HTTP POST /engine/evaluate
  Java Spring Boot (:8081)
  ├─ Runs 7 hard rules (CIBIL min, DTI max, fraud threshold, ...)
  ├─ If pass: prices interest rate by risk band
  ├─ Adjusts approved amount (soft rules)
  ├─ Calculates EMI (reducing balance formula)
  ├─ Returns: APPROVED/REJECTED + rate + EMI + reason
  ├─ Saves to policy_decisions (PostgreSQL)
        │
        ▼
  Go Gateway
  ├─ Updates loan_applications with final decision
  └─ Returns full enriched response to customer
```
