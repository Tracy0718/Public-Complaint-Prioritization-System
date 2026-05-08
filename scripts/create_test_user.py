import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_complaints.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth.models import User  # noqa: E402


def main() -> None:
    username = os.environ.get("TEST_USERNAME", "testuser")
    password = os.environ.get("TEST_PASSWORD", "TestPass123!")
    email = os.environ.get("TEST_EMAIL", "testuser@example.com")

    user, created = User.objects.get_or_create(username=username, defaults={"email": email})
    if created:
        user.set_password(password)
        user.email = email
        user.save()
        print(f"Created user '{username}' with password '{password}'")
    else:
        print(f"User '{username}' already exists (not modified).")


if __name__ == "__main__":
    main()

