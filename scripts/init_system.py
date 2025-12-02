#!/usr/bin/env python3
"""
Cost Melt - System Initialization Script
Initializes all components and verifies setup
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_step(step_num, total, message):
    """Print a step message"""
    print(f"{YELLOW}[{step_num}/{total}]{NC} {message}")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✓{NC} {message}")

def print_error(message):
    """Print error message"""
    print(f"{RED}✗{NC} {message}")

def print_info(message):
    """Print info message"""
    print(f"{BLUE}ℹ{NC} {message}")

def check_env_file():
    """Check if .env file exists"""
    env_path = Path("backend/.env")
    if not env_path.exists():
        print_error(".env file not found in backend/")
        print_info("Copy backend/.env.example to backend/.env and fill in your keys")
        return False
    return True

def check_env_vars():
    """Check required environment variables"""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "OPENAI_API_KEY"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print_error(f"Missing environment variables: {', '.join(missing)}")
        print_info("Set these in backend/.env file")
        return False
    
    return True

def check_redis():
    """Check if Redis is accessible"""
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        print_success("Redis is accessible")
        return True
    except Exception as e:
        print_error(f"Redis not accessible: {e}")
        print_info("Start Redis with: docker run -d -p 6379:6379 redis:7-alpine")
        return False

def check_supabase():
    """Check if Supabase is accessible"""
    try:
        from supabase import create_client, Client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            print_error("Supabase credentials not found")
            return False
        
        supabase: Client = create_client(supabase_url, supabase_key)
        # Try a simple query
        result = supabase.table("requests").select("id").limit(1).execute()
        print_success("Supabase is accessible")
        return True
    except Exception as e:
        print_error(f"Supabase not accessible: {e}")
        print_info("Check your SUPABASE_URL and SUPABASE_SERVICE_KEY")
        return False

def check_openai():
    """Check if OpenAI API key is valid"""
    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Try a simple API call
        response = client.models.list()
        print_success("OpenAI API key is valid")
        return True
    except Exception as e:
        print_error(f"OpenAI API key invalid: {e}")
        print_info("Check your OPENAI_API_KEY in backend/.env")
        return False

def check_dependencies():
    """Check if Python dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import redis
        import supabase
        import openai
        print_success("All Python dependencies installed")
        return True
    except ImportError as e:
        print_error(f"Missing dependency: {e}")
        print_info("Install with: cd backend && pip install -r requirements.txt")
        return False

def main():
    """Main initialization check"""
    print(f"{BLUE}========================================{NC}")
    print(f"{BLUE}Cost Melt - System Initialization{NC}")
    print(f"{BLUE}========================================{NC}")
    print("")
    
    # Change to backend directory
    backend_dir = Path("backend")
    if backend_dir.exists():
        os.chdir(backend_dir)
        sys.path.insert(0, str(Path.cwd()))
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    checks = [
        ("Environment file", check_env_file),
        ("Environment variables", check_env_vars),
        ("Python dependencies", check_dependencies),
        ("Redis connection", check_redis),
        ("Supabase connection", check_supabase),
        ("OpenAI API key", check_openai),
    ]
    
    results = []
    for name, check_func in checks:
        print_step(len(results) + 1, len(checks), f"Checking {name}...")
        result = check_func()
        results.append(result)
        if not result:
            print()
            print_error("Initialization failed. Please fix the errors above.")
            return 1
    
    print()
    print(f"{GREEN}========================================{NC}")
    print(f"{GREEN}All Checks Passed!{NC}")
    print(f"{GREEN}========================================{NC}")
    print()
    print("System is ready. Next steps:")
    print("  1. Start backend: cd backend && uvicorn main:app --reload")
    print("  2. Start dashboard: cd dashboard && npm run dev")
    print("  3. Run tests: ./scripts/test_everything.sh")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

