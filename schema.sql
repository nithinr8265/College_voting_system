-- ============================================================
-- College Online Voting System - Supabase PostgreSQL Schema
-- Run this in Supabase SQL Editor
-- ============================================================

-- TABLE 1: students
CREATE TABLE IF NOT EXISTS students (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  roll_number TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  department TEXT,
  year INT,
  admission_year INT,       -- Calendar year they were admitted (e.g., 2022)
  entry_year INT DEFAULT 1, -- Which year they entered: 1=First, 2=Lateral(2nd), 3=Lateral(3rd)
  photo_base64 TEXT,        -- Base64 encoded student photo for face recognition
  has_voted BOOLEAN DEFAULT FALSE,
  voted_at TIMESTAMP,
  is_approved BOOLEAN DEFAULT FALSE,  -- Admin must approve signup requests
  created_at TIMESTAMP DEFAULT NOW()
);

-- TABLE 2: candidates
CREATE TABLE IF NOT EXISTS candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  roll_number TEXT,
  department TEXT,
  position TEXT NOT NULL,   -- President / Vice President / Secretary / Treasurer
  manifesto TEXT,
  photo_base64 TEXT,        -- Base64 encoded candidate photo for dashboard cards
  vote_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- TABLE 3: votes
CREATE TABLE IF NOT EXISTS votes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES students(id) ON DELETE CASCADE,
  candidate_id uuid REFERENCES candidates(id) ON DELETE CASCADE,
  position TEXT,
  voted_at TIMESTAMP DEFAULT NOW()
);

-- TABLE 4: election_settings (always 1 row, id=1)
CREATE TABLE IF NOT EXISTS election_settings (
  id INT PRIMARY KEY DEFAULT 1,
  start_date TIMESTAMP,         -- Full datetime: when voting opens  (YYYY-MM-DDTHH:MM)
  end_date TIMESTAMP,           -- Full datetime: when voting closes (YYYY-MM-DDTHH:MM)
  result_date DATE,             -- Date results are expected (informational)
  is_active BOOLEAN DEFAULT FALSE,
  results_published BOOLEAN DEFAULT FALSE  -- Admin must explicitly publish results
);
INSERT INTO election_settings (id) VALUES (1) ON CONFLICT DO NOTHING;

-- ── MIGRATION (run once if you already have the table) ───────────────
-- ALTER TABLE election_settings
--   ALTER COLUMN start_date TYPE TIMESTAMP USING start_date::TIMESTAMP,
--   ALTER COLUMN end_date TYPE TIMESTAMP USING end_date::TIMESTAMP,
--   ADD COLUMN IF NOT EXISTS results_published BOOLEAN DEFAULT FALSE;

-- TABLE 5: admins
CREATE TABLE IF NOT EXISTS admins (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SEED DEFAULT ADMIN (password: admin123)
-- Generate hash in Python:
--   import bcrypt
--   bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
-- Then replace the hash below:
-- ============================================================
-- INSERT INTO admins (username, password_hash) 
-- VALUES ('admin', '$2b$12$REPLACE_WITH_REAL_BCRYPT_HASH');

-- ============================================================
-- ELIGIBILITY LOGIC (handled in Python):
-- admission_year = year student joined college (e.g., 2022)
-- entry_year     = 1 (first year), 2 (lateral 2nd yr), 3 (lateral 3rd yr)
-- last_eligible_academic_year = admission_year + (3 - entry_year)
-- 
-- Examples:
--   1st year entry 2022 → eligible 2022, 2023, 2024  (last = 2024)
--   2nd year entry 2022 → eligible 2022, 2023         (last = 2023)
--   3rd year entry 2022 → eligible 2022 only           (last = 2022)
-- ============================================================
