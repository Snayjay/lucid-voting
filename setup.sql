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
CREATE POLICY "Allow public insert access" ON bills
    FOR INSERT WITH CHECK (true);

-- Create the profiles table for Voter Identity
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    voter_id TEXT UNIQUE NOT NULL,
    passcode_hash TEXT NOT NULL,
    identity_hash TEXT UNIQUE NOT NULL, -- To prevent duplicate registrations
    full_name TEXT,
    address TEXT,
    dob TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Allow public inserts for new registrations
CREATE POLICY "Allow public insert access" ON profiles
    FOR INSERT WITH CHECK (true);

-- Allow public select for verification
CREATE POLICY "Allow public select access" ON profiles
    FOR SELECT USING (true);
