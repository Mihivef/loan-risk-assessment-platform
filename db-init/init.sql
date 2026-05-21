
CREATE TABLE IF NOT EXISTS loan_applications (
    id                    SERIAL PRIMARY KEY,
    applicant_name        VARCHAR(100)   NOT NULL,
    applicant_email       VARCHAR(100)   NOT NULL,
    applicant_phone       VARCHAR(20)    NOT NULL,
    loan_type             VARCHAR(20)    NOT NULL,   
    requested_amount      NUMERIC(15,2)  NOT NULL,
    tenure_months         INT            NOT NULL,
    purpose               TEXT           NOT NULL,
    annual_income         NUMERIC(15,2)  NOT NULL,
    existing_monthly_emis NUMERIC(10,2)  DEFAULT 0,
    employment_type       VARCHAR(30)    NOT NULL,   
    employer_name         VARCHAR(100)   NOT NULL,
    years_employed        NUMERIC(4,1)   DEFAULT 0,
    cibil_score           INT            NOT NULL,   
    ml_credit_score       NUMERIC(5,4)   DEFAULT 0,  
    risk_band             VARCHAR(20)    DEFAULT 'MEDIUM',
    fraud_probability     NUMERIC(5,4)   DEFAULT 0,
    risk_factors          TEXT[]         DEFAULT '{}',
    status                VARCHAR(20)    DEFAULT 'pending',
    approved_amount       NUMERIC(15,2)  DEFAULT 0,
    interest_rate         NUMERIC(5,2)   DEFAULT 0,
    monthly_emi           NUMERIC(10,2)  DEFAULT 0,
    rejection_reason      TEXT,
    decision_notes        TEXT,
    submitted_by          VARCHAR(100),
    created_at            TIMESTAMPTZ    DEFAULT NOW(),
    updated_at            TIMESTAMPTZ    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_loan_apps_status    ON loan_applications(status);
CREATE INDEX IF NOT EXISTS idx_loan_apps_email     ON loan_applications(applicant_email);
CREATE INDEX IF NOT EXISTS idx_loan_apps_loan_type ON loan_applications(loan_type);
CREATE INDEX IF NOT EXISTS idx_loan_apps_created   ON loan_applications(created_at DESC);
CREATE TABLE IF NOT EXISTS policy_decisions (
    id                  BIGSERIAL      PRIMARY KEY,
    application_id      INT            NOT NULL,
    decision            VARCHAR(20)    NOT NULL,
    loan_type           VARCHAR(20),
    requested_amount    NUMERIC(15,2),
    approved_amount     NUMERIC(15,2),
    interest_rate       NUMERIC(5,2),
    monthly_emi         NUMERIC(10,2),
    risk_band           VARCHAR(20),
    ml_credit_score     NUMERIC(5,4),
    fraud_probability   NUMERIC(5,4),
    rejection_reason    TEXT,
    decision_notes      TEXT,
    created_at          TIMESTAMPTZ    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pd_application_id ON policy_decisions(application_id);
CREATE INDEX IF NOT EXISTS idx_pd_decision        ON policy_decisions(decision);
CREATE INDEX IF NOT EXISTS idx_pd_created_at      ON policy_decisions(created_at DESC);

CREATE TABLE IF NOT EXISTS ml_score_logs (
    id                  SERIAL         PRIMARY KEY,
    application_id      INT            NOT NULL,
    score_type          VARCHAR(30)    NOT NULL,   
    ml_credit_score     NUMERIC(6,4),
    risk_band           VARCHAR(20),
    fraud_probability   NUMERIC(6,4),
    risk_factors        JSONB          DEFAULT '[]',
    flags               JSONB          DEFAULT '[]',
    debt_to_income      NUMERIC(6,4),
    confidence          NUMERIC(6,4),
    created_at          TIMESTAMPTZ    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ml_logs_app_id ON ml_score_logs(application_id);
CREATE INDEX IF NOT EXISTS idx_ml_logs_type   ON ml_score_logs(score_type);

INSERT INTO loan_applications (
    applicant_name, applicant_email, applicant_phone, loan_type,
    requested_amount, tenure_months, purpose, annual_income,
    existing_monthly_emis, employment_type, employer_name, years_employed,
    cibil_score, ml_credit_score, risk_band, fraud_probability, risk_factors,
    status, approved_amount, interest_rate, monthly_emi, submitted_by
) VALUES
(
    'Arjun Sharma', 'arjun@example.com', '9876543210', 'personal',
    500000, 36, 'Home renovation', 1200000,
    5000, 'salaried', 'IDFC Bank', 4,
    780, 0.8200, 'LOW', 0.0300, '{}',
    'approved', 500000, 10.50, 16249, 'customer_1'
),
(
    'Priya Nair', 'priya@example.com', '9876543211', 'home',
    5000000, 240, 'Purchase of 2BHK apartment in Chennai', 1800000,
    15000, 'salaried', 'TCS', 6,
    820, 0.8900, 'LOW', 0.0100, '{}',
    'under_review', 0, 0, 0, 'customer_1'
),
(
    'Rohit Verma', 'rohit@example.com', '9876543212', 'personal',
    300000, 24, 'Medical emergency', 420000,
    12000, 'self_employed', 'Self', 1.5,
    620, 0.4100, 'HIGH', 0.1200,
    ARRAY['high debt-to-income ratio','low employment tenure','below average CIBIL'],
    'rejected', 0, 0, 0, 'customer_1'
)
ON CONFLICT DO NOTHING;


CREATE OR REPLACE VIEW approval_rate_view AS
SELECT
    COUNT(*)                                                 AS total,
    COUNT(*) FILTER (WHERE status = 'approved')              AS approved,
    COUNT(*) FILTER (WHERE status = 'rejected')              AS rejected,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'approved') / NULLIF(COUNT(*), 0),
        2
    )                                                        AS approval_rate_pct,
    ROUND(AVG(requested_amount), 2)                          AS avg_requested,
    ROUND(AVG(approved_amount) FILTER (WHERE status='approved'), 2) AS avg_approved
FROM loan_applications;

CREATE OR REPLACE VIEW risk_band_distribution AS
SELECT
    risk_band,
    COUNT(*)                                              AS total,
    COUNT(*) FILTER (WHERE status = 'approved')           AS approved,
    COUNT(*) FILTER (WHERE status = 'rejected')           AS rejected,
    ROUND(AVG(ml_credit_score), 4)                        AS avg_ml_score
FROM loan_applications
GROUP BY risk_band;
