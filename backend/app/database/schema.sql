-- ==========================================================================
-- LocalVest Database Schema (PostgreSQL + PostGIS Extension)
-- Architected for 0-Cost Deployment on Supabase / Render Free PostgreSQL
-- ==========================================================================

-- Enable PostGIS Extension for Geofencing & Location Queries (3-5km Radius)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. AUTH & USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'backer' CHECK (role IN ('backer', 'project_owner', 'admin')),
    kyc_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'approved', 'rejected')),
    is_locked BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. KYC DOCUMENTS TABLE
CREATE TABLE IF NOT EXISTS kyc_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL, -- CCCD / Driver License
    front_image_url TEXT NOT NULL,
    back_image_url TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewer_note TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. CAMPAIGNS (PROJECTS) TABLE
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '🌱',
    cover VARCHAR(100) DEFAULT 'cover-a',
    description TEXT NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(15,2) NOT NULL CHECK (target_amount > 0),
    raised_amount DECIMAL(15,2) DEFAULT 0.00 CHECK (raised_amount >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending_review', 'active', 'funded', 'failed', 'closed')),
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326), -- PostGIS Spatial Geometry Point
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PostGIS Spatial Index for lightning-fast sub-20ms 3-5km radius queries
CREATE INDEX IF NOT EXISTS idx_projects_geom ON projects USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- Automatic Spatial Point Updater Trigger
CREATE OR REPLACE FUNCTION update_project_geom()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom = ST_SetSRID(ST_MakePoint(NEW.lng, NEW.lat), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_update_project_geom
BEFORE INSERT OR UPDATE OF lat, lng ON projects
FOR EACH ROW EXECUTE FUNCTION update_project_geom();

-- 4. MILESTONES TABLE
CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(15,2) NOT NULL CHECK (target_amount > 0),
    released_amount DECIMAL(15,2) DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'locked' CHECK (status IN ('locked', 'pending', 'released')),
    description TEXT,
    order_index INT NOT NULL DEFAULT 1,
    released_at TIMESTAMP WITH TIME ZONE
);

-- 5. PAYMENT & ESCROW INTERNAL LEDGER
CREATE TABLE IF NOT EXISTS ledger (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id),
    user_id UUID REFERENCES users(id),
    milestone_id UUID REFERENCES milestones(id),
    amount DECIMAL(15,2) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('escrow_deposit', 'milestone_release', 'refund')),
    gateway VARCHAR(50) DEFAULT 'momo', -- momo, vnpay, mock
    gateway_txn_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ledger_project ON ledger(project_id);

-- 6. AI-FLAG & ANTI-FRAUD AUDIT TABLE
CREATE TABLE IF NOT EXISTS ai_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    fraud_score INT NOT NULL DEFAULT 0, -- 0 to 100
    is_suspicious BOOLEAN DEFAULT false,
    reasons JSONB, -- Stored image similarity & NLP anomaly checks
    status VARCHAR(20) DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'dismissed', 'confirmed_fraud')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL, -- escrow_deposit, milestone_reached, refund, alert
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
