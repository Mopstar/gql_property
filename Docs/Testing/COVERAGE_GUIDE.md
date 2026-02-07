# Code Coverage Setup Guide

**Project:** gql_property  
**Created:** February 6, 2026  
**Status:** ✅ Configured and Ready

---

## 📋 Quick Start

### Prerequisites

Ensure pytest-cov is installed:
```powershell
pip install pytest-cov
```

Or install all dev dependencies:
```powershell
pip install -r requirements-dev.txt
```

---

## 🚀 Running Coverage

### Basic Coverage Run

```powershell
# Run all tests with coverage
pytest --cov=src --cov-report=html

# View the HTML report
start htmlcov\index.html
```

### Coverage with Terminal Output

```powershell
# Show coverage in terminal with missing lines
pytest --cov=src --cov-report=term-missing --cov-report=html
```

### Run Specific Tests

```powershell
# Only unit tests (fast, no services needed)
pytest tests/test_dbdefinitions.py tests/test_dataloaders.py --cov=src --cov-report=html

# Only GraphQL type tests
pytest tests/test_gt_definitions.py --cov=src --cov-report=html

# Exclude live tests (that need running services)
pytest -m "not live" --cov=src --cov-report=html
```

---

## 📊 Configuration Files

### .coveragerc

Main coverage configuration file:

```ini
[run]
source = src                    # Measure coverage for src/ directory
omit = 
    tests/*                     # Exclude test files
    */__pycache__/*             # Exclude Python cache
    */migrations/*              # Exclude database migrations
    */proxy/*                   # Exclude proxy service
    */.venv/*                   # Exclude virtual environment

[report]
exclude_lines =                 # Don't require coverage for these
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov             # HTML report output directory

[xml]
output = coverage.xml           # XML report for CI/CD tools
```

### pytest.ini

Pytest configuration with test markers:

```ini
[pytest]
testpaths = tests               # Where to find tests
asyncio_mode = auto             # Auto-detect async tests

markers =
    live: tests requiring live services
    unit: unit tests (can run offline)
    integration: integration tests
```

---

## 📈 Understanding Coverage Reports

### HTML Report (Recommended)

After running `pytest --cov=src --cov-report=html`:

1. Open `htmlcov/index.html` in your browser
2. See overall coverage percentage
3. Click on any file to see line-by-line coverage
4. **Green lines** = covered by tests
5. **Red lines** = not covered by tests
6. **Gray lines** = excluded (comments, etc.)

### Terminal Report

```
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src\DBDefinitions\BaseModel.py               45      3    93%   23-25
src\DBDefinitions\EventDBModel.py            32      5    84%   45, 67-70
src\DBDefinitions\purchasemodel.py           51      8    84%   89-96
src\GraphTypeDefinitions\PurchaseGQLModel.py 156     45    71%   Multiple
------------------------------------------------------------------------
TOTAL                                       2341    567    76%
```

**Key Metrics:**
- **Stmts** = Total executable statements
- **Miss** = Statements not covered
- **Cover** = Coverage percentage
- **Missing** = Line numbers not covered

---

## 🎯 Coverage Goals

### Recommended Targets

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| DB Models | 80%+ | High |
| GraphQL Resolvers | 70%+ | High |
| Mutations | 75%+ | High |
| Authorization | 60%+ | Medium |
| Error Handlers | 70%+ | Medium |
| DataLoaders | 80%+ | High |
| Utilities | 60%+ | Low |

### Current Expected Coverage

Based on the test suite (54 tests):
- **Overall:** 60-75%
- **DB Definitions:** 75-85%
- **GraphQL Types:** 60-70%
- **Mutations:** 65-75%

---

## 🔧 Troubleshooting

### Issue: "Module coverage not found"

**Solution:**
```powershell
pip install pytest-cov coverage
```

### Issue: "No data to report"

**Cause:** Tests didn't run or failed before coverage collection

**Solution:**
```powershell
# Run tests first without coverage to see failures
pytest -v

# Then add coverage
pytest --cov=src
```

### Issue: Live tests fail, affecting coverage

**Solution:** Run only unit tests
```powershell
pytest tests/test_dbdefinitions.py tests/test_dataloaders.py --cov=src
```

Or mark and skip live tests:
```powershell
pytest -m "not live" --cov=src
```

### Issue: Coverage includes test files

**Cause:** Incorrect source path

**Solution:** Always use `--cov=src` (not `--cov=.`)

---

## 🎓 Advanced Usage

### Multiple Report Formats

```powershell
# Generate HTML, XML, and terminal reports
pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term
```

### Coverage with Minimum Threshold

```powershell
# Fail if coverage is below 60%
pytest --cov=src --cov-fail-under=60
```

### Coverage for Specific Module

```powershell
# Only measure coverage for PurchaseGQLModel
pytest --cov=src.GraphTypeDefinitions.PurchaseGQLModel --cov-report=html
```

### Parallel Test Execution with Coverage

```powershell
# Install pytest-xdist first: pip install pytest-xdist
pytest -n auto --cov=src --cov-report=html
```

---

## 📦 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests with Coverage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

## 📝 Best Practices

### 1. Run Coverage Regularly

```powershell
# Before committing changes
pytest --cov=src --cov-report=term-missing
```

### 2. Focus on Important Code

Don't obsess over 100% coverage. Focus on:
- ✅ Business logic (mutations, queries)
- ✅ Authorization/security code
- ✅ Data transformations
- ⚠️ Less important: DTOs, simple getters, `__repr__`

### 3. Use Coverage to Find Gaps

Look for:
- Untested error handlers
- Untested edge cases
- Dead code (0% coverage = might be unused)

### 4. Combine with Manual Testing

Coverage shows **if** code runs, not **if** it works correctly!

---

## 🎯 Quick Reference Commands

```powershell
# Basic coverage
pytest --cov=src --cov-report=html

# With missing lines
pytest --cov=src --cov-report=term-missing

# Unit tests only
pytest tests/test_dbdefinitions.py tests/test_dataloaders.py --cov=src

# Skip live tests
pytest -m "not live" --cov=src --cov-report=html

# Minimum threshold
pytest --cov=src --cov-fail-under=60

# View HTML report
start htmlcov\index.html
```

---

## 📚 Additional Resources

- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Testing Guide](TESTING_GUIDE.md) - Complete testing documentation

---

**Last Updated:** February 6, 2026  
**Maintained By:** Development Team

