-- Phase 4 Migration: Language support extensions

ALTER TABLE users ADD COLUMN IF NOT EXISTS language_auto_detected VARCHAR(10);
ALTER TABLE users ADD COLUMN IF NOT EXISTS language_confirmed BOOLEAN DEFAULT FALSE;

ALTER TABLE customers ADD COLUMN IF NOT EXISTS language_auto_detected VARCHAR(10);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS language_confirmed BOOLEAN DEFAULT FALSE;
