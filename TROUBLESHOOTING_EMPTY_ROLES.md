# Troubleshooting: Empty Roles Array

## Problem
When querying `me { roles }`, the response shows empty roles array:
```json
{
  "data": {
    "me": {
      "fullname": "Ludvík Kilik",
      "id": "a0506cc4-5d53-4fdb-a989-c06a97e527fd",
      "roles": []
    }
  }
}
```

## Root Cause
The **User-Group (UG) service** is not returning roles. This can happen for several reasons:

### 1. UG Service Not Running
The UG service must be running on `http://localhost:33001` (configured in `environment.txt`).

**Check if running:**
```powershell
# Test if UG service responds
curl http://localhost:33001/api/gql -Method POST -Body '{"query":"{ __schema { types { name } } }"}' -ContentType "application/json"
```

**Start UG service:**
```powershell
# Using Docker Compose
docker-compose -f docker-compose.debug.yml up frontend

# Check logs
docker-compose -f docker-compose.debug.yml logs frontend
```

### 2. Roles Data Not Loaded Into UG Database
The UG service has its own PostgreSQL database that needs the roles data from `systemdata.rnd.json`.

**Verify data loading:**
1. Check Docker logs: `docker-compose logs frontend`
2. Look for: `"initializing system structures"` and `"all done"`
3. Check if `systemdata.rnd.json` is mounted correctly in docker-compose

### 3. Using `rolesOn` Instead of `roles`
Some implementations filter roles by date validity using `rolesOn`. See [test_roles_fix.py](test_roles_fix.py).

**Solution:** Ensure the UG service query uses `roles` not `rolesOn`:
```graphql
query {
  me {
    roles {  # ← Use 'roles', not 'rolesOn'
      group { id name mastergroupId }
      roletype { id name }
    }
  }
}
```

### 4. Authentication Token Issue
The JWT token might not be valid or might be for a different user.

**Check token:**
```javascript
// Decode JWT to see which user it's for
// Use https://jwt.io or similar
```

## Solutions

### Option A: Start Full Stack with Docker
```powershell
# Start all services including UG service
docker-compose -f docker-compose.debug.yml up

# Verify UG service is running
curl http://localhost:33001/health
```

### Option B: Use Mock/Test Mode (Recommended for Development)
If you don't need the full UG service, modify [main.py](main.py) to use mock roles for testing:

```python
# In get_context() function, after line 227:
if roles_count == 0:
    logging.warning(f"User {me.get('fullname')} has NO roles assigned!")
    # TEMPORARY: Add mock roles for testing
    if me.get('email') == 'Ludvik.Kilik@world.com':
        me['roles'] = [
            {
                'group': {
                    'id': 'd75d64a4-bf5f-43c5-9c14-8fda7aff6c09',
                    'name': 'Univerzita',
                    'mastergroupId': None
                },
                'roletype': {
                    'id': 'ced46aa4-3217-4fc1-b79d-f6be7d21c6b6',
                    'name': 'administrátor'
                }
            }
        ]
        result['user'] = me
        logging.info(f"Applied mock roles for testing")
```

### Option C: Check systemdata.rnd.json Loading
Verify that Ludvík Kilik's role is in the data file:

```powershell
# Search for Ludvík's role assignment
Select-String -Path systemdata.rnd.json -Pattern 'a0506cc4-5d53-4fdb-a989-c06a97e527fd' | Select-Object -First 20
```

Expected to find:
- User record with ID `a0506cc4-5d53-4fdb-a989-c06a97e527fd`
- Role assignment with that user_id and roletype "administrátor"

## Verification Steps

### 1. Test UG Service Directly
```powershell
# Query user by email
$query = @"
{
  "query": "query { userPage(email: \"Ludvik.Kilik@world.com\") { id fullname roles { roletype { name } group { name } } } }"
}
"@

curl http://localhost:33001/api/gql -Method POST -Body $query -ContentType "application/json"
```

### 2. Check Application Logs
Look for these log messages in your application:
```
User authenticated: a0506cc4... - Ludvík Kilik with 0 roles
User Ludvík Kilik has NO roles assigned!
```

If you see this, the UG service is returning empty roles.

### 3. Verify Database Content
```sql
-- Connect to UG service database
SELECT u.fullname, r.roletype_id, rt.name as role_name, g.name as group_name
FROM users u
JOIN roles r ON u.id = r.user_id  
JOIN roletypes rt ON r.roletype_id = rt.id
JOIN groups g ON r.group_id = g.id
WHERE u.email = 'Ludvik.Kilik@world.com';
```

## Expected Result After Fix

```json
{
  "data": {
    "me": {
      "fullname": "Ludvík Kilik",
      "id": "a0506cc4-5d53-4fdb-a989-c06a97e527fd",
      "roles": [
        {
          "group": {
            "id": "d75d64a4-bf5f-43c5-9c14-8fda7aff6c09",
            "name": "Univerzita",
            "mastergroupId": null
          },
          "roletype": {
            "id": "ced46aa4-3217-4fc1-b79d-f6be7d21c6b6",
            "name": "administrátor"
          }
        }
      ]
    }
  }
}
```

## Related Files
- [main.py](main.py) - Context setup and UG client
- [docker-compose.debug.yml](docker-compose.debug.yml) - UG service configuration
- [systemdata.rnd.json](systemdata.rnd.json) - User and role data
- [USER_ROLES_BY_DEPARTMENT.md](USER_ROLES_BY_DEPARTMENT.md) - Expected roles reference
- [test_roles_fix.py](test_roles_fix.py) - Role loading diagnostic script
