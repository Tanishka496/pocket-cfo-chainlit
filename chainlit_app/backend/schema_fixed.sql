-- AI Pocket CFO - Transaction Management Database Schema
-- PostgreSQL Schema for Supabase (Fixed Version)
-- Run this script step by step in Supabase SQL Editor

-- ============================================================
-- 1. CREATE TRANSACTIONS TABLE
-- ============================================================

CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  description TEXT NOT NULL CHECK (char_length(description) > 0 AND char_length(description) <= 500),
  amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
  type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  category TEXT NOT NULL CHECK (char_length(category) > 0 AND char_length(category) <= 100),
  transaction_date DATE NOT NULL,
  is_personal BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. CREATE INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date DESC);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date DESC);
CREATE INDEX idx_transactions_user_type ON transactions(user_id, type);

-- ============================================================
-- 3. CREATE TRIGGER FOR UPDATED_AT
-- ============================================================

CREATE OR REPLACE FUNCTION update_transactions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_transactions_updated_at
  BEFORE UPDATE ON transactions
  FOR EACH ROW
  EXECUTE FUNCTION update_transactions_updated_at();

-- ============================================================
-- 4. ENABLE ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 5. CREATE RLS POLICIES
-- ============================================================

-- Allow users to view their own transactions
CREATE POLICY "users_can_view_own_transactions" ON transactions
  FOR SELECT
  USING (auth.uid() = user_id);

-- Allow users to insert their own transactions
CREATE POLICY "users_can_insert_own_transactions" ON transactions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Allow users to update their own transactions
CREATE POLICY "users_can_update_own_transactions" ON transactions
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Allow users to delete their own transactions
CREATE POLICY "users_can_delete_own_transactions" ON transactions
  FOR DELETE
  USING (auth.uid() = user_id);

-- ============================================================
-- 6. GRANT PERMISSIONS TO AUTHENTICATED USERS
-- ============================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON transactions TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;

-- ============================================================
-- 7. CREATE VIEW FOR SUMMARIES (OPTIONAL)
-- ============================================================

CREATE OR REPLACE VIEW transaction_summaries AS
SELECT 
  user_id,
  type,
  category,
  DATE_TRUNC('month', transaction_date) AS month,
  COUNT(*) AS transaction_count,
  SUM(amount) AS total_amount,
  AVG(amount) AS average_amount,
  MIN(amount) AS min_amount,
  MAX(amount) AS max_amount
FROM transactions
GROUP BY user_id, type, category, DATE_TRUNC('month', transaction_date);

GRANT SELECT ON transaction_summaries TO authenticated;

-- ============================================================
-- 8. SUCCESS MESSAGE
-- ============================================================

-- If you see this comment, the schema was successfully created!
-- Your transactions table is ready to use.
-- Next: Update your .env file and start the API server
