"""
Verify Test Users Configuration

This script verifies that all required test users are properly configured
and can authenticate with the UG service.

Usage:
    python scripts/verify_test_users.py

Expected Test Users:
    - john.newbie@world.com: Standard user for basic tests
    - Add more as needed for RBAC testing
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.client import createFederationClient, createLiveClient


# Test users configuration
# TODO: Expand this list as more test users are added
TEST_USERS = [
    {
        "username": "john.newbie@world.com",
        "password": "john.newbie@world.com",
        "expected_role": "editor",
        "description": "Standard test user for basic CRUD operations"
    },
]


async def verify_user(username: str, password: str, expected_role: str = None):
    """Verify user can authenticate and has expected roles.

    Args:
        username: User email
        password: User password
        expected_role: Expected role type name (optional)

    Returns:
        bool: True if verification passed, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Testing: {username}")
    print(f"{'='*60}")

    try:
        # Try federation client first (requires UG service)
        client = createFederationClient(username=username, password=password)
        user_info = await client.get_user_info()

        if user_info:
            print(f"✅ Authentication successful")
            print(f"   User ID: {user_info.get('id', 'N/A')}")
            print(f"   Name: {user_info.get('fullname', 'N/A')}")
            print(f"   Email: {user_info.get('email', 'N/A')}")

            # Check roles
            roles = user_info.get('roles', [])
            if roles:
                print(f"   Roles ({len(roles)}):")
                for role in roles:
                    role_name = role.get('roletype', {}).get('name', 'Unknown')
                    group_name = role.get('group', {}).get('name', 'Unknown')
                    valid = role.get('valid', False)
                    status = "✅" if valid else "⚠️"
                    print(f"      {status} {role_name} in {group_name}")

                    # Check expected role
                    if expected_role and role_name == expected_role and valid:
                        print(f"   ✅ Has expected role: {expected_role}")

            else:
                print(f"   ⚠️  No roles assigned")

            return True
        else:
            print(f"❌ Authentication failed - no user info returned")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"   Make sure UG service is running and user exists")
        return False


async def verify_all_users():
    """Verify all test users."""
    print("\n" + "="*60)
    print("VERIFYING TEST USERS")
    print("="*60)
    print("\nThis script verifies that test users can authenticate")
    print("and have the expected roles for RBAC testing.\n")

    results = []
    for user_config in TEST_USERS:
        result = await verify_user(
            username=user_config["username"],
            password=user_config["password"],
            expected_role=user_config.get("expected_role")
        )
        results.append((user_config["username"], result))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    success_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for username, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {username}")

    print(f"\nResults: {success_count}/{total_count} users verified")

    if success_count == total_count:
        print("\n🎉 All test users verified successfully!")
        return 0
    else:
        print(f"\n⚠️  {total_count - success_count} user(s) failed verification")
        print("\nNext steps:")
        print("1. Ensure UG service is running (docker compose up)")
        print("2. Check that users exist in UG database")
        print("3. Verify credentials are correct")
        return 1


async def main():
    """Main entry point."""
    try:
        exit_code = await verify_all_users()
        return exit_code
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification cancelled by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

