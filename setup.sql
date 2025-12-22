-- Create the bills table
CREATE TABLE IF NOT EXISTS bills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    title TEXT NOT NULL,
    simple_summary TEXT NOT NULL,
    pros JSONB DEFAULT '[]'::jsonb,
    cons JSONB DEFAULT '[]'::jsonb
);

-- Enable Row Level Security (RLS)
ALTER TABLE bills ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow anyone to read bills
CREATE POLICY "Allow public read access" ON bills
    FOR SELECT USING (true);

-- Create a policy to allow inserts (for your Admin tab)
-- Note: In a production app, you'd restrict this to authenticated admins
CREATE POLICY "Allow public insert access" ON bills
    FOR INSERT WITH CHECK (true);

