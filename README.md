# gql_property - GraphQL Purchase Management System

**Modern GraphQL-based purchase/event management system with advanced RBAC and creator ownership.**

## 🚀 Quick Links

### Essential Documentation
- **[API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)** - ⭐ Complete API usage guide (start here!)
- **[CREATOR_OWNERSHIP_GUIDE.md](CREATOR_OWNERSHIP_GUIDE.md)** - Authorization model explained
- **[ERROR_CODES.md](ERROR_CODES.md)** - Error codes dictionary with UUIDs
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card

### Guides & Reference
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Complete testing guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md)** - Complete technical analysis
- **[IMPLEMENTATION_HISTORY.md](IMPLEMENTATION_HISTORY.md)** - Development history

## 🎯 Key Features

- ✅ **GraphQL API** with Strawberry + FastAPI
- ✅ **Advanced RBAC** with creator ownership model
- ✅ **Apollo Federation** support for microservices
- ✅ **Hierarchical permissions** with group inheritance
- ✅ **Centralized error codes** with UUID tracking
- ✅ **Optimistic locking** for concurrent updates
- ✅ **DataLoader pattern** for N+1 query prevention
- ✅ **Docker Compose** orchestration (8 services)

## 🏗️ Architecture

**Tech Stack:**
- **Backend:** Python 3.11+, FastAPI, Strawberry GraphQL
- **Database:** PostgreSQL with SQLAlchemy
- **Authentication:** JWT tokens via external UG service
- **Federation:** Apollo Gateway for service composition
- **Testing:** pytest with async support

**Services:**
- Purchase/Event Management (this project)
- User/Group Service (UG)
- Apollo Gateway
- PostgreSQL databases
- Frontend UI

## 📦 Installation

```powershell
# Clone and setup
cd E:\PyCharm_Projects\gql_property
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start services
docker compose -f docker-compose.debug.yml up -d

# Run development server
python main.py
```

## 🧪 Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_purchases.py -v
```

## 📖 Documentation Structure

### For API Users
- **[API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)** - Complete usage guide (start here!)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card
- **[ERROR_CODES.md](ERROR_CODES.md)** - Error codes with solutions
- **[CREATOR_OWNERSHIP_GUIDE.md](CREATOR_OWNERSHIP_GUIDE.md)** - Authorization model

### For Developers
- **[PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md)** - Complete technical deep-dive
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing infrastructure and examples
- **[IMPLEMENTATION_HISTORY.md](IMPLEMENTATION_HISTORY.md)** - Development timeline
- **[src/error_codes.py](src/error_codes.py)** - Error code registry module

### For System Admins
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[docker-compose.debug.yml](docker-compose.debug.yml)** - Service orchestration

## 🔑 Key Concepts

### Creator Ownership
**"If you created it, you can always manage it"** - regardless of role changes.

### Role-Based Access
- **Viewer:** Read-only access to group content
- **Editor:** Create and modify group content
- **Admin:** Manage all content in group hierarchy
- **Root Admin:** Universal access to all content

### Error Handling
All errors include UUID codes for machine-readable error tracking. See ERROR_CODES.md for complete reference.

---

## 📚 Evolution Documentation (Historical)

This project evolved from gql_evolution tutorial:

## Technology
FastAPI
Strawberry
SQLAlchemy
Asyncio
AsyncDataLoader

## Initialization
At begin it is stongly recomended to create virtual environment and install all libraries from requirements.txt file.
To run it (in already activated environment) the command

`pip install -r requirements.txt`

should be used.


For each step (aka switching between versions) run

`pip install -r requirements.txt --force`

This enforce full instalation.

## Step 1

https://github.com/hrbolek/gql_evolution/tree/step_01

Hello world FastAPI

## Step 2

https://github.com/hrbolek/gql_evolution/tree/step_02

Hello world GraphQL endpoint

## Step 3

https://github.com/hrbolek/gql_evolution/tree/step_03

GraphQL endpoint with object

## Step 4

https://github.com/hrbolek/gql_evolution/tree/step_04

SQLAlchemy DBModel introduction

## Step 5

https://github.com/hrbolek/gql_evolution/tree/step_05

This step introduce a default data import and reading records from database.

## Step 6

https://github.com/hrbolek/gql_evolution/tree/step_06

This step will extend DBModel and GQLModel.

## Step 7

https://github.com/hrbolek/gql_evolution/tree/step_07

This step will introduce entity relations.

## Step 8

https://github.com/hrbolek/gql_evolution/tree/step_08

This step will introduce C and U operations (from CRUD).

## Step 9

https://github.com/hrbolek/gql_evolution/tree/step_09

Tests introduction
