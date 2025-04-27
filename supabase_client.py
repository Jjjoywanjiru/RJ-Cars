from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
url = os.environ.get("https://krxhfokngnugmuvnqcgl.supabase.co")
key = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtyeGhmb2tuZ251Z211dm5xY2dsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3NjI1NjUsImV4cCI6MjA2MTMzODU2NX0.3-mZywCLDT_w3SxXcZH_bqMzQhfpXG7oiiDpb2qcPyw")

# Check if variables are available
if not url or not key:
    print("ERROR: Supabase environment variables not found!")
    print(f"SUPABASE_URL: {'SET' if url else 'NOT SET'}")
    print(f"SUPABASE_KEY: {'SET' if key else 'NOT SET'}")

# Create Supabase client
supabase: Client = create_client(url, key)