-- AI Pocket CFO - Transaction Management Database Schema
-- PostgreSQL Schema for Supabase

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Foreign key to auth.users
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Transaction data
  description TEXT NOT NULL CHECK (char_length(description) > 0 AND char_length(description) <= 500),
  amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
  type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  category TEXT NOT NULL CHECK (char_length(category) > 0 AND char_length(category) <= 100),
  transaction_date DATE NOT NULL,
  
  -- Flags
  is_personal BOOLEAN DEFAULT FALSE,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  
  -- Ensure uniqueness of ID
  UNIQUE(id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_user_id 
  ON transactions(user_id);

CREATE INDEX IF NOT EXISTS idx_transactions_date 
  ON transactions(transaction_date DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_type 
  ON transactions(type);

CREATE INDEX IF NOT EXISTS idx_transactions_category 
  ON transactions(category);

CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
  ON transactions(user_id, transaction_date DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_user_type 
  ON transactions(user_id, type);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_transactions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to call the function
DROP TRIGGER IF EXISTS set_transactions_updated_at ON transactions;
CREATE TRIGGER set_transactions_updated_at
  BEFORE UPDATE ON transactions
  FOR EACH ROW
  EXECUTE FUNCTION update_transactions_updated_at();

-- Enable Row Level Security (RLS) for multi-tenant safety
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their own transactions
CREATE POLICY "Users can view their own transactions" ON transactions
  FOR SELECT USING (auth.uid() = user_id);

-- Create policy: Users can insert their own transactions
CREATE POLICY "Users can insert their own transactions" ON transactions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can update their own transactions
CREATE POLICY "Users can update their own transactions" ON transactions
  FOR UPDATE USING (auth.uid() = user_id);

-- Create policy: Users can delete their own transactions
CREATE POLICY "Users can delete their own transactions" ON transactions
  FOR DELETE USING (auth.uid() = user_id);

-- Create a view for transaction summaries (optional - useful for analytics)
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

-- Sample data for testing (optional - remove for production)
-- INSERT INTO transactions (user_id, description, amount, type, category, transaction_date, is_personal)
-- VALUES
--   ('550e8400-e29b-41d4-a716-446655440000', 'Office supplies', 150.50, 'expense', 'Supplies', '2024-02-27', false),
--   ('550e8400-e29b-41d4-a716-446655440000', 'Client payment', 5000.00, 'income', 'Revenue', '2024-02-25', false),
--   ('550e8400-e29b-41d4-a716-446655440000', 'Medical expense', 200.00, 'expense', 'Personal', '2024-02-20', true),
--   ('550e8400-e29b-41d4-a716-446655440000', 'Rent payment', 2000.00, 'expense', 'Rent', '2024-02-01', false);

-- Grant permissions (if needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON transactions TO authenticated;
-- GRANT SELECT ON transaction_summaries TO authenticated;
