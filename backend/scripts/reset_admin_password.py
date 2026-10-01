"""
Reset an existing admin_users password. Run from the backend/ directory:

    python -m scripts.reset_admin_password admin@psc.com "NewStrongPassword123"
"""
import sys

from app.database.supabase_client import get_supabase
from app.services.auth_service import hash_password


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.reset_admin_password <email> <new_password>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    supabase = get_supabase()
    existing = (
        supabase.table("admin_users")
        .select("id, email")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    if not existing.data:
        # Fallback for legacy mixed-case emails
        existing = (
            supabase.table("admin_users")
            .select("id, email")
            .ilike("email", email)
            .limit(1)
            .execute()
        )
    if not existing.data:
        print(f"No admin found with email {email}.")
        sys.exit(1)

    admin_id = existing.data[0]["id"]
    supabase.table("admin_users").update(
        {"hashed_password": hash_password(password)}
    ).eq("id", admin_id).execute()
    print(f"Password updated for admin: {existing.data[0]['email']}")


if __name__ == "__main__":
    main()
