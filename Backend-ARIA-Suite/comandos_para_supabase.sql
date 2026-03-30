-- ============================================
-- Tabla de leads por usuario - ARIA Suite
-- Ejecutar en Supabase → SQL Editor
-- ============================================

CREATE TABLE aria_suite_leads_per_user (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES usuarios_scraper(id),
  job_id UUID REFERENCES scraping_jobs(id),
  source TEXT NOT NULL DEFAULT 'maps',
  name TEXT,
  email TEXT,
  phone TEXT,
  website TEXT,
  location TEXT,
  category TEXT,
  raw_data JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_aria_leads_user_id ON aria_suite_leads_per_user(user_id);
CREATE INDEX idx_aria_leads_email ON aria_suite_leads_per_user(email);
