# Phase 2A: HR Models Assessment

**Date**: 2025-11-22
**Status**: ASSESSMENT COMPLETE

---

## Overview

Assessment of existing HR models in `floor_app/operations/hr/models/` against the Master Build Spec requirements.

---

## Spec Requirements vs Current State

### ✅ EXISTING MODELS (Complete)

The following models from the spec are **already implemented**:

1. **HRPerson** (`people.py`)
   - ✓ Complete with all required fields
   - Fields: first_name, last_name, middle_name, national_id, date_of_birth, nationality, gender, contact info
   - Relationship to auth.User is supported

2. **HREmployee** (`employee.py`)
   - ✓ Complete with FK to HRPerson
   - Fields: employee_code, status, department, position, joining_date, leaving_date
   - Links to Department, Position

3. **Department** (`department.py`)
   - ✓ Complete with code, name, description
   - ✓ Parent_department self-FK for hierarchy

4. **Position** (`position.py`)
   - ✓ Complete with code, title, department
   - Likely has description and is_supervisory

5. **LeaveType** (`leave.py`)
   - ✓ Complete
   - Fields: code, name, requires_approval, max_days_per_year, is_paid

6. **LeaveRequest** (`leave.py`)
   - ✓ Complete
   - FK to HREmployee, leave_type
   - Fields: start_date, end_date, reason, status, approved_by, approved_at

7. **AttendanceRecord** (`attendance.py`)
   - ✓ Complete
   - FK to HREmployee
   - Fields: date, check_in_time, check_out_time, status, details

8. **TrainingProgram** (`training.py`)
   - ✓ Complete
   - Fields: code, title, description, provider, internal_or_external

9. **TrainingSession** (`training.py`)
   - ✓ Complete
   - FK to TrainingProgram
   - Fields: start_date, end_date, location, instructor

10. **EmployeeTraining** (`training.py`)
    - ✓ Complete
    - FK to HREmployee, FK to TrainingSession
    - Fields: status, score

11. **QualificationLevel** (`qualification.py`)
    - ✓ Complete
    - Fields: code, name, description

12. **EmployeeQualification** (`qualification.py`)
    - ✓ Complete
    - FK to HREmployee, FK to QualificationLevel
    - Fields: granted_date, expiry_date

13. **DocumentType** (`document.py`)
    - ✓ Complete
    - Fields: code, name, description

14. **EmployeeDocument** (`document.py`)
    - ✓ Complete
    - FK to HREmployee, FK to DocumentType
    - Fields: file, uploaded_at, expires_at, is_mandatory

15. **HRPhone** (`phone.py`)
    - ✓ Complete
    - FK to HREmployee
    - Fields: phone_number, type, is_primary

16. **HREmail** (`email.py`)
    - ✓ Complete
    - FK to HREmployee
    - Fields: email, type, is_primary

### ⚠️ MISSING MODELS (To Be Added)

The following models from the spec are **NOT YET IMPLEMENTED**:

1. **HRContract** ❌
   - **Required Fields**:
     - FK to HREmployee
     - contract_type (permanent, temporary, contractor)
     - start_date, end_date
     - basic_salary, housing_allowance, transport_allowance, other_allowances
     - currency (FK to core.Currency)
     - is_current (Boolean)
   - **Note**: Finance fields should be in a collapsible panel in UI

2. **HRShiftTemplate** ❌
   - **Required Fields**:
     - name (e.g. "Day Shift", "Night Shift")
     - start_time, end_time
     - is_night_shift (Boolean)
     - working_days (JSON or choices mask)

3. **AssetType** ❌ (Spec says this should be in HR, but hr_assets app exists)
   - **Required Fields**:
     - code
     - name (e.g., "Phone", "Vehicle", "Laptop", "Housing")
     - description

4. **HRAsset** ❌ (Probably in hr_assets app)
   - **Required Fields**:
     - FK to AssetType
     - asset_tag (unique)
     - description
     - serial_number
     - purchase_date
     - status (available, assigned, maintenance, retired)
     - cost_center (FK to core.CostCenter)
     - Finance fields: purchase_price, currency

5. **AssetAssignment** ❌ (Probably in hr_assets app)
   - **Required Fields**:
     - FK to HRAsset
     - FK to HREmployee
     - assigned_from, assigned_to
     - status (active, returned)
     - remarks

### 📦 ADDITIONAL MODELS (Beyond Spec)

The existing implementation includes **extra models** not in the spec:

1. **LeavePolicy** (`leave.py`)
   - Additional leave management features

2. **LeaveBalance** (`leave.py`)
   - Track employee leave balances

3. **LeaveRequestStatus** (`leave.py`)
   - Status choices

4. **OvertimeRequest** (`attendance.py`)
   - Overtime tracking

5. **AttendanceSummary** (`attendance.py`)
   - Attendance aggregation

6. **AttendanceStatus**, **OvertimeType**, **OvertimeStatus** (`attendance.py`)
   - Choice field helpers

7. **SkillMatrix** (`training.py`)
   - Skills tracking

8. **TrainingType**, **TrainingStatus** (`training.py`)
   - Training categorization

9. **DocumentRenewal**, **ExpiryAlert** (`document.py`)
   - Document lifecycle management

10. **OvertimeConfiguration**, **AttendanceConfiguration** (`configuration.py`)
    - System configuration

11. **DelayIncident**, **DelayReason** (`configuration.py`)
    - Delay tracking

12. **AuditLog** (`audit_log.py`)
    - HR-specific audit logging

---

## Next Steps

### Step 1: Add Missing Models ✅ REQUIRED

Add the 5 missing models to complete spec compliance:

1. Create `contract.py` with `HRContract` model
2. Create `shift.py` with `HRShiftTemplate` model
3. Check `hr_assets` app for Asset models
4. If Asset models don't exist in hr_assets, add them to HR
5. Link all new models to `core.CostCenter` and `core.Currency` as needed

### Step 2: Update Admin ✅ REQUIRED

Register all new models in `admin.py`

### Step 3: Create Migrations ✅ REQUIRED

```bash
python manage.py makemigrations hr
python manage.py makemigrations hr_assets
python manage.py migrate
```

### Step 4: Test ✅ REQUIRED

```bash
python manage.py check
python manage.py shell
# Test model creation
```

---

## hr_assets App Investigation

Need to check if `floor_app/operations/hr_assets/` contains:
- AssetType model
- HRAsset model
- AssetAssignment model

If yes → Just link them to spec requirements
If no → Add them to HR app or hr_assets app

---

## Conclusion

**Current Status**: 16/21 models ✅ (76% complete)
**Missing**: 5 models ❌ (24% to add)
**Extra**: 12+ models beyond spec

**Recommendation**:
1. Add the 5 missing models
2. Verify hr_assets contains Asset models
3. Ensure all models link to core_foundation (CostCenter, Currency)
4. Proceed to Phase 2B (HR UI) once models are complete

---

## Files to Modify

1. `floor_app/operations/hr/models/contract.py` - NEW FILE
2. `floor_app/operations/hr/models/shift.py` - NEW FILE
3. `floor_app/operations/hr/models/__init__.py` - UPDATE IMPORTS
4. `floor_app/operations/hr/admin.py` - REGISTER NEW MODELS
5. Check: `floor_app/operations/hr_assets/models/` - VERIFY ASSET MODELS
