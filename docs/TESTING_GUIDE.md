# Floor Management System - Testing Guide

## Table of Contents
1. [Testing Strategy](#testing-strategy)
2. [Running Tests](#running-tests)
3. [Module Testing](#module-testing)
4. [Integration Testing](#integration-testing)
5. [Performance Testing](#performance-testing)
6. [Security Testing](#security-testing)
7. [User Acceptance Testing](#user-acceptance-testing)
8. [Test Data](#test-data)

## Testing Strategy

### Test Pyramid
```
                    /\
                   /  \
                  / E2E \
                 /______\
                /        \
               /Integration\
              /____________\
             /              \
            /   Unit Tests   \
           /__________________\
```

### Test Levels
1. **Unit Tests**: Individual functions and methods
2. **Integration Tests**: Module interactions
3. **System Tests**: End-to-end workflows
4. **User Acceptance Tests**: Real-world scenarios

## Running Tests

### Setup Test Environment
```bash
# Create test database
createdb floor_mgmt_test

# Set test environment
export DJANGO_SETTINGS_MODULE=floor_mgmt.settings_test

# Install test dependencies
pip install -r requirements-test.txt
```

### Run All Tests
```bash
python manage.py test
```

### Run Specific Module Tests
```bash
# HR module
python manage.py test floor_app.operations.hr

# Inventory module
python manage.py test floor_app.operations.inventory

# Engineering module
python manage.py test floor_app.operations.engineering

# Production module
python manage.py test floor_app.operations.production
```

### Run with Coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Verbose Output
```bash
python manage.py test --verbosity=2
```

### Keep Test Database
```bash
python manage.py test --keepdb
```

## Module Testing

### HR & Administration

#### Employee Management Tests
```python
# Test employee creation
def test_create_employee():
    """Test creating a new employee"""
    1. Create person record
    2. Create employee with valid data
    3. Verify employee created successfully
    4. Check employee number generated
    5. Verify relationships (department, position)

# Test employee update
def test_update_employee():
    """Test updating employee information"""
    1. Create employee
    2. Update employee fields
    3. Save and refresh from database
    4. Verify changes persisted

# Test employee soft delete
def test_soft_delete_employee():
    """Test soft delete functionality"""
    1. Create employee
    2. Mark as deleted
    3. Verify not in active queryset
    4. Verify still in database
```

#### Contract Management Tests
```python
# Test contract creation
def test_create_contract():
    """Test creating employment contract"""
    1. Create employee
    2. Create contract with dates
    3. Verify contract linked to employee
    4. Check validation rules

# Test contract validation
def test_contract_date_validation():
    """Test contract date validation"""
    1. Try to create contract with end before start
    2. Verify validation error raised
    3. Try overlapping contracts
    4. Verify business rules enforced
```

#### Leave Request Tests
```python
# Test leave request workflow
def test_leave_request_workflow():
    """Test complete leave request workflow"""
    1. Employee submits leave request
    2. Verify notification sent to manager
    3. Manager approves request
    4. Verify approval notification to employee
    5. Check leave balance updated

# Test leave rejection
def test_leave_request_rejection():
    """Test leave request rejection"""
    1. Submit leave request
    2. Manager rejects with reason
    3. Verify rejection notification sent
    4. Check leave balance unchanged
```

### Inventory Management

#### Item Management Tests
```python
# Test item creation
def test_create_item():
    """Test creating inventory item"""
    1. Create item category
    2. Create unit of measure
    3. Create item with SKU
    4. Verify unique SKU constraint

# Test stock tracking
def test_stock_movement():
    """Test stock movement tracking"""
    1. Create item
    2. Create location
    3. Add stock
    4. Move stock between locations
    5. Verify quantities accurate
```

### Engineering

#### Bit Design Tests
```python
# Test design creation
def test_create_bit_design():
    """Test creating bit design"""
    1. Create design level
    2. Create design type
    3. Create bit design
    4. Verify design code unique

# Test BOM creation
def test_create_bom():
    """Test BOM creation and validation"""
    1. Create bit design
    2. Create revision
    3. Create BOM header
    4. Add BOM lines
    5. Verify quantities
```

### Production

#### Job Card Tests
```python
# Test job card lifecycle
def test_job_card_lifecycle():
    """Test complete job card workflow"""
    1. Create job card
    2. Add routing steps
    3. Start production
    4. Complete operations
    5. Close job card
    6. Verify status transitions

# Test batch processing
def test_batch_processing():
    """Test batch order processing"""
    1. Create batch order
    2. Add items to batch
    3. Process batch
    4. Verify all items processed
```

### Quality Management

#### NCR Tests
```python
# Test NCR workflow
def test_ncr_workflow():
    """Test NCR complete workflow"""
    1. Create NCR
    2. Add root cause analysis
    3. Define corrective actions
    4. Implement actions
    5. Close NCR
    6. Verify status progression
```

## Integration Testing

### QR Code Integration
```bash
# Test QR generation
1. Create employee
2. Generate QR code
3. Verify QR code contains correct data
4. Test QR code scanning
5. Verify redirect to detail page
```

### Notification System
```bash
# Test notification delivery
1. Create leave request
2. Verify notification created
3. Check notification appears in recipient's feed
4. Test notification marking as read
5. Verify notification count updates
```

### Module Integration
```bash
# Test inventory-production integration
1. Create inventory item
2. Create BOM with item
3. Create job card referencing BOM
4. Verify stock reservation
5. Complete job card
6. Verify stock consumption
```

## Performance Testing

### Load Testing
```bash
# Using locust
pip install locust

# Create locustfile.py
locust -f locustfile.py --host=http://localhost:8000

# Monitor:
- Response times
- Error rates
- Throughput
- Resource usage
```

### Database Performance
```sql
-- Analyze query performance
EXPLAIN ANALYZE
SELECT * FROM hr_employee
WHERE status = 'ACTIVE'
AND department_id = 1;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Find slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Caching Tests
```python
# Test cache hit rates
def test_cache_effectiveness():
    """Test caching effectiveness"""
    1. Clear cache
    2. Load page (cache miss)
    3. Time request
    4. Load page again (cache hit)
    5. Time request
    6. Verify faster on cache hit
```

## Security Testing

### Authentication Tests
```python
# Test login security
def test_login_security():
    """Test login security measures"""
    1. Test with wrong password
    2. Verify account lockout after N attempts
    3. Test password complexity requirements
    4. Verify session timeout

# Test authorization
def test_authorization():
    """Test role-based access control"""
    1. Create user with limited permissions
    2. Try to access restricted page
    3. Verify access denied
    4. Verify proper error message
```

### SQL Injection Tests
```python
# Test SQL injection prevention
def test_sql_injection_prevention():
    """Verify SQL injection protection"""
    1. Try malicious SQL in search
    2. Verify parametrized queries used
    3. Check for proper escaping
    4. Verify no data compromise
```

### XSS Tests
```python
# Test XSS prevention
def test_xss_prevention():
    """Test cross-site scripting prevention"""
    1. Submit script tags in forms
    2. Verify proper escaping
    3. Check templates use safe filters
    4. Verify no script execution
```

### CSRF Tests
```python
# Test CSRF protection
def test_csrf_protection():
    """Test CSRF token validation"""
    1. Submit form without CSRF token
    2. Verify request rejected
    3. Submit with invalid token
    4. Verify request rejected
    5. Submit with valid token
    6. Verify request accepted
```

## User Acceptance Testing

### Test Scenarios

#### Scenario 1: New Employee Onboarding
```
Given: HR manager needs to onboard new employee
When: Manager creates employee record
Then:
- Employee appears in employee list
- QR code generated automatically
- User account created (if enabled)
- Welcome notification sent
```

#### Scenario 2: Leave Request Approval
```
Given: Employee needs vacation time
When: Employee submits leave request
Then:
- Manager receives notification
- Manager can approve/reject
- Employee receives decision notification
- Leave balance updated if approved
```

#### Scenario 3: Production Job Card
```
Given: New bit needs to be manufactured
When: Production creates job card
Then:
- BOM pulled automatically
- Materials reserved
- Routing steps defined
- Operations tracked to completion
```

### UAT Checklist

#### HR Module
- [ ] Create employee
- [ ] Update employee information
- [ ] Generate and download QR code
- [ ] Create contract
- [ ] Assign shift
- [ ] Assign asset
- [ ] Submit leave request
- [ ] Approve/reject leave

#### Inventory Module
- [ ] Create item
- [ ] Add stock
- [ ] Move stock
- [ ] Track serial units
- [ ] View stock levels
- [ ] Generate reports

#### Engineering Module
- [ ] Create bit design
- [ ] Create revision
- [ ] Create BOM
- [ ] View design details
- [ ] Export BOM

#### Production Module
- [ ] Create job card
- [ ] Define routing
- [ ] Track operations
- [ ] Complete job
- [ ] View production metrics

#### Quality Module
- [ ] Create NCR
- [ ] Add analysis
- [ ] Define corrective actions
- [ ] Close NCR
- [ ] View quality reports

## Test Data

### Creating Test Data
```bash
# Load fixtures
python manage.py loaddata fixtures/test_data.json

# Run custom command
python manage.py generate_test_data

# Using factory_boy
python manage.py shell
>>> from floor_app.factories import EmployeeFactory
>>> EmployeeFactory.create_batch(50)
```

### Test Data Sets

#### Minimal Dataset
- 5 departments
- 10 positions
- 20 employees
- 5 leave types
- 10 items

#### Standard Dataset
- 10 departments
- 25 positions
- 100 employees
- 10 leave types
- 50 items
- 20 job cards

#### Large Dataset
- 20 departments
- 50 positions
- 500 employees
- 15 leave types
- 200 items
- 100 job cards
- 50 BOMs

### Cleanup Test Data
```bash
# Clear test data
python manage.py flush --noinput

# Reset sequences
python manage.py sqlsequencereset app_name | python manage.py dbshell
```

## Automated Testing

### Continuous Integration

#### GitHub Actions
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: python manage.py test
      - name: Generate coverage
        run: coverage xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Reporting

### Test Reports

#### Coverage Report
```bash
coverage html
open htmlcov/index.html
```

#### JUnit XML Report
```bash
python manage.py test --testrunner=xmlrunner.extra.djangotestrunner.XMLTestRunner
```

### Defect Tracking
- Document all failed tests
- Create GitHub issues for bugs
- Link issues to test cases
- Track resolution
- Verify fixes with regression tests

## Best Practices

### Writing Tests
- One test per function/feature
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Keep tests independent
- Use fixtures and factories
- Mock external services
- Test edge cases

### Maintaining Tests
- Update tests with code changes
- Remove obsolete tests
- Refactor duplicate code
- Keep test data minimal
- Document complex test logic
- Review test failures promptly

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-23
**For System Version**: 1.0.0
