"""
Database layer for Python FastAPI scorer.
Uses asyncpg — the fastest async PostgreSQL driver for Python.

Why asyncpg over psycopg2?
  - asyncpg is fully async/await — no thread blocking
  - FastAPI is async-first; asyncpg integrates naturally
  - 3–5x faster than psycopg2 for bulk operations
"""

import asyncpg
import os
import json
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


_pool: Optional[asyncpg.Pool] = None



CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ml_score_logs (
    id                  SERIAL PRIMARY KEY,
    application_id      INT          NOT NULL,
    score_type          VARCHAR(30)  NOT NULL,  -- 'credit_risk' or 'fraud_check'
    ml_credit_score     NUMERIC(6,4),
    risk_band           VARCHAR(20),
    fraud_probability   NUMERIC(6,4),
    risk_factors        JSONB        DEFAULT '[]',
    flags               JSONB        DEFAULT '[]',
    debt_to_income      NUMERIC(6,4),
    confidence          NUMERIC(6,4),
    created_at          TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ml_logs_app_id ON ml_score_logs(application_id);
CREATE INDEX IF NOT EXISTS idx_ml_logs_type   ON ml_score_logs(score_type);
"""


async def get_pool() -> asyncpg.Pool:
    """Returns the shared connection pool, creating it if needed."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool


async def migrate():
    """Create the ml_score_logs table on startup."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)
    print("✅ Python DB migration complete")


async def log_credit_score(
    application_id: int,
    ml_score: float,
    risk_band: str,
    risk_factors: list,
    dti: float,
    confidence: float
):
    """Insert a credit score result into ml_score_logs for audit/analysis."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO ml_score_logs
               (application_id, score_type, ml_credit_score, risk_band,
                risk_factors, debt_to_income, confidence)
               VALUES ($1, 'credit_risk', $2, $3, $4::jsonb, $5, $6)""",
            application_id,
            ml_score,
            risk_band,
            json.dumps(risk_factors),
            dti,
            confidence,
        )


async def log_fraud_check(
    application_id: int,
    fraud_probability: float,
    flags: list
):
    """Insert a fraud check result into ml_score_logs."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO ml_score_logs
               (application_id, score_type, fraud_probability, flags)
               VALUES ($1, 'fraud_check', $2, $3::jsonb)""",
            application_id,
            fraud_probability,
            json.dumps(flags),
        )


async def get_score_history(application_id: int) -> list:
    """Retrieve all ML scores logged for a given application_id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM ml_score_logs WHERE application_id = $1 ORDER BY created_at",
            application_id
        )
        return [dict(row) for row in rows]


async def close_pool():
    """Gracefully close the DB pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = Non
