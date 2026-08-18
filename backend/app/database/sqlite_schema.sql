-- ==========================================================================
-- LocalVest Database Schema (SQLite version)
-- ==========================================================================

-- 1. AUTH & USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'backer',
    kyc_status TEXT NOT NULL DEFAULT 'pending',
    is_locked BOOLEAN DEFAULT 0,
    alt_emails TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- 2. KYC DOCUMENTS TABLE
CREATE TABLE IF NOT EXISTS kyc_documents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    doc_number TEXT,
    front_image_url TEXT NOT NULL,
    back_image_url TEXT,
    status TEXT DEFAULT 'pending',
    reviewer_note TEXT,
    submitted_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. CAMPAIGNS (PROJECTS) TABLE
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    icon TEXT DEFAULT '🌱',
    cover TEXT DEFAULT 'cover-a',
    images TEXT DEFAULT '[]',
    description TEXT NOT NULL,
    location_name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    raised_amount REAL DEFAULT 0.00,
    status TEXT NOT NULL DEFAULT 'draft',
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    creator_name TEXT,
    creator_verified BOOLEAN DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

-- 4. MILESTONES TABLE
CREATE TABLE IF NOT EXISTS milestones (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    released_amount REAL DEFAULT 0.00,
    status TEXT NOT NULL DEFAULT 'locked',
    description TEXT,
    order_index INTEGER NOT NULL DEFAULT 1,
    released_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- 5. PAYMENT & ESCROW INTERNAL LEDGER
CREATE TABLE IF NOT EXISTS ledger (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    user_id TEXT,
    milestone_id TEXT,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    gateway TEXT DEFAULT 'momo',
    gateway_txn_id TEXT,
    status TEXT DEFAULT 'completed',
    description TEXT,
    user_name TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (milestone_id) REFERENCES milestones(id)
);

-- 6. AI-FLAG & ANTI-FRAUD AUDIT TABLE
CREATE TABLE IF NOT EXISTS ai_flags (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    fraud_score INTEGER NOT NULL DEFAULT 0,
    is_suspicious BOOLEAN DEFAULT 0,
    reasons TEXT,
    status TEXT DEFAULT 'pending_review',
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- 7. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    created_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);