-- Phase 5 Migration: Monetization and Worker Profile Migration
-- Run this against the existing database

-- Add subscription and credit fields to the existing users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20) DEFAULT 'inactive' CHECK (subscription_status IN ('active', 'past_due', 'canceled', 'inactive')),
ADD COLUMN IF NOT EXISTS credits_balance INT DEFAULT 50, -- Starting credits for new plumbers
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(100);

-- Create services table so plumbers can define their specific offerings
CREATE TABLE IF NOT EXISTS services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    price_type VARCHAR(20) DEFAULT 'fixed' CHECK (price_type IN ('fixed', 'hourly', 'starting_at', 'contact_for_quote')),
    base_price DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast service lookups per user
CREATE INDEX IF NOT EXISTS idx_services_user ON services(user_id);
