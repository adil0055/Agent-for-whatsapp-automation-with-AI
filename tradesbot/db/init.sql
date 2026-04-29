-- TradesBot Phase 1: Initial Database Schema
-- Run automatically by Postgres on first startup

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- USERS (Tradespeople)
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100),
    trade_type VARCHAR(50),
    language_preference VARCHAR(10) DEFAULT 'en',
    gstin VARCHAR(20),
    hourly_rate DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CUSTOMERS
-- ============================================================
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(15) NOT NULL,
    name VARCHAR(100),
    address TEXT,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, phone_number)
);

-- ============================================================
-- CONVERSATIONS (message log)
-- ============================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    phone_from VARCHAR(30) NOT NULL,
    phone_to VARCHAR(30) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('text', 'voice', 'image', 'document', 'other')),
    message_sid VARCHAR(64),
    content TEXT,
    transcript TEXT,
    media_url TEXT,
    media_stored_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_phone ON conversations(phone_from, created_at DESC);
CREATE INDEX idx_conversations_user ON conversations(user_id, created_at DESC);

-- ============================================================
-- JOBS (placeholder for Phase 2)
-- ============================================================
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'scheduled', 'in_progress', 'completed', 'cancelled')),
    scheduled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed a test user (optional, for dev)
INSERT INTO users (phone_number, name, trade_type, language_preference, hourly_rate)
VALUES ('+918089790055', 'Test Tradesperson', 'plumber', 'en', 300.00)
ON CONFLICT (phone_number) DO NOTHING;
