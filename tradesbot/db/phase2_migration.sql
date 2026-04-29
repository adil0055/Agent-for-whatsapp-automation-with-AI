-- Phase 2 Migration: Quotes, Invoices, Job extensions

-- Extend jobs table
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS location TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS estimated_duration_minutes INT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS reminder_sent BOOLEAN DEFAULT FALSE;

-- Quotes table
CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    customer_id UUID REFERENCES customers(id),
    job_id UUID REFERENCES jobs(id),
    items JSONB NOT NULL DEFAULT '[]',
    labor_total DECIMAL(10,2) DEFAULT 0,
    material_total DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(10,2) DEFAULT 0,
    gst_rate DECIMAL(5,2) DEFAULT 18.00,
    gst_amount DECIMAL(10,2) DEFAULT 0,
    grand_total DECIMAL(10,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'INR',
    status VARCHAR(20) DEFAULT 'draft'
        CHECK (status IN ('draft','sent','accepted','rejected','expired')),
    valid_until DATE,
    notes TEXT,
    pdf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(20) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    customer_id UUID REFERENCES customers(id),
    job_id UUID REFERENCES jobs(id),
    quote_id UUID REFERENCES quotes(id),
    items JSONB NOT NULL DEFAULT '[]',
    subtotal DECIMAL(10,2) DEFAULT 0,
    gst_rate DECIMAL(5,2) DEFAULT 18.00,
    cgst_amount DECIMAL(10,2) DEFAULT 0,
    sgst_amount DECIMAL(10,2) DEFAULT 0,
    igst_amount DECIMAL(10,2) DEFAULT 0,
    grand_total DECIMAL(10,2) DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT 'unpaid'
        CHECK (payment_status IN ('unpaid','partial','paid')),
    payment_method VARCHAR(20),
    paid_amount DECIMAL(10,2) DEFAULT 0,
    due_date DATE,
    pdf_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE SEQUENCE IF NOT EXISTS invoice_seq START 1;

-- Job reminders
CREATE TABLE IF NOT EXISTS job_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id),
    remind_at TIMESTAMPTZ NOT NULL,
    reminder_type VARCHAR(20) DEFAULT 'whatsapp',
    sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
