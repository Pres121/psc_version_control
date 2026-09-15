"""
One-off CLI to create the first admin_users row (there's no public
sign-up endpoint by design). Run from the backend/ directory:

    python -m scripts.create_admin admin@psc.com "Strong Password" "Admin Name" superadmin
"""
import sys

from app.database.supabase_client import get_supabase
from app.services.auth_service import hash_password


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.create_admin <email> <password> [full_name] [role]")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)
    full_name = sys.argv[3] if len(sys.argv) > 3 else None
    role = sys.argv[4] if len(sys.argv) > 4 else "admin"
    if role not in {"admin", "superadmin"}:
        print("Role must be 'admin' or 'superadmin'.")
        sys.exit(1)

    supabase = get_supabase()
    existing = supabase.table("admin_users").select("id").eq("email", email).execute()
    if existing.data:
        print(f"Admin with email {email} already exists.")
        sys.exit(1)

    supabase.table("admin_users").insert(
        {
            "email": email,
            "hashed_password": hash_password(password),
            "full_name": full_name,
            "role": role,
            "is_active": True,
        }
    ).execute()
    print(f"Created admin user: {email} (role={role})")


if __name__ == "__main__":
    main()
