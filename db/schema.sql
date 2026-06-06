-- PostgreSQL DB Schema for AI Lead Automation System (Aviara Labs)

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Lead status enum type
CREATE TYPE lead_status AS ENUM ('pending', 'enriching', 'enriched', 'classifying', 'classified', 'failed');

-- Create Leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    company VARCHAR(255),
    linkedin_url VARCHAR(500),
    company_size VARCHAR(100),
    industry VARCHAR(150),
    lead_message TEXT,
    intent VARCHAR(100),
    confidence DECIMAL(5, 4),
    status lead_status DEFAULT 'pending',
    raw_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for searching/deduplicating by email (highly recommended for performance & unique check)
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

-- Index for sorting leads by creation time
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);

-- Index for filtering by status
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);

-- Auto-update updated_at column on modifications
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
