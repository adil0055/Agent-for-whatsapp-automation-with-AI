-- Phase 3 Migration: Follow-ups, Consent, Call logs

-- Follow-ups
CREATE TABLE IF NOT EXISTS follow_ups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    customer_id UUID REFERENCES customers(id),
    reference_type VARCHAR(20) NOT NULL,
    reference_id UUID NOT NULL,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending','sent','responded','cancelled','escalated')),
    reminder_count INT DEFAULT 0,
    max_reminders INT DEFAULT 3,
    next_reminder_at TIMESTAMPTZ,
    last_reminded_at TIMESTAMPTZ,
    escalated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_followups_next ON follow_ups(next_reminder_at) WHERE status = 'pending';

-- Call consents (TRAI compliant)
CREATE TABLE IF NOT EXISTS call_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    customer_id UUID REFERENCES customers(id),
    customer_phone VARCHAR(30) NOT NULL,
    consent_status VARCHAR(20) DEFAULT 'pending'
        CHECK (consent_status IN ('pending','granted','revoked','expired')),
    consented_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    dnd_checked BOOLEAN DEFAULT FALSE,
    dnd_status VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Call logs
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    customer_phone VARCHAR(30) NOT NULL,
    call_sid VARCHAR(64),
    call_type VARCHAR(20) DEFAULT 'followup',
    tts_language VARCHAR(10),
    duration_seconds INT,
    status VARCHAR(20),
    transcript TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Marketing images
CREATE TABLE IF NOT EXISTS marketing_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    prompt TEXT NOT NULL,
    image_url TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
