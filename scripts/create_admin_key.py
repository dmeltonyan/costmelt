#!/usr/bin/env python3
"""
Cost Melt - Bootstrap the first admin API key.

POST /auth/api-keys requires an existing admin-role key to call (see
backend/security/rbac.py's @require_role("admin")), so there is no HTTP
endpoint that can mint the very first key. This script creates it directly
against Supabase using the service-role credentials in backend/.env,
bypassing the API layer the same way a one-time database seed would.

Usage:
    python scripts/create_admin_key.py --user-id you@example.com --project-id default

The plaintext key is printed once. Store it somewhere safe (e.g. a
password manager or your deployment's secret store) — it is bcrypt-hashed
before being written to the database and cannot be recovered afterward.
Use it as: Authorization: Bearer <key>  (or the x-api-key header)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Create the first Cost Melt admin API key")
    parser.add_argument("--user-id", required=True, help="Identifier for the key owner (e.g. your email)")
    parser.add_argument("--project-id", default="default", help="Project identifier (default: 'default')")
    parser.add_argument("--role", default="admin", choices=["admin", "write", "read"], help="Access role (default: admin)")
    args = parser.parse_args()

    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    sys.path.insert(0, str(backend_dir))
    os.chdir(backend_dir)

    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("SUPABASE_URL") or not (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")):
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in backend/.env before "
              "you can create API keys. Auth is backed by the api_keys table in Supabase — "
              "see backend/db/migrations/001_api_keys.sql.")
        sys.exit(1)

    from db.supabase_client import SupabaseClient
    from security.api_key_manager import APIKeyManager

    supabase_client = SupabaseClient()
    if not supabase_client.client:
        print("Error: could not connect to Supabase with the configured credentials.")
        sys.exit(1)

    api_key_manager = APIKeyManager(supabase_client.client)

    result = asyncio.run(api_key_manager.create_api_key(
        user_id=args.user_id,
        project_id=args.project_id,
        role=args.role,
    ))

    print()
    print("=" * 60)
    print(f"Created {args.role} API key for user '{args.user_id}', project '{args.project_id}'")
    print("=" * 60)
    print(f"API key: {result['api_key']}")
    print()
    print("This key is shown once and cannot be retrieved again. Store it now.")
    print("Use it as:  Authorization: Bearer <key>   or   x-api-key: <key>")


if __name__ == "__main__":
    main()
