# Employee Management Enhancement Plan

## Current Analysis

### Existing Fields in HREmployee:
- `job_title` (CharField) - Currently just text, needs to be a Position dropdown
- `team` (CharField) - Text field, could link to departments
- `employee_type` (Choice field) - Currently only for role classification (OPERATOR, SUPERVISOR, etc.)
- `status` (Choice field) - ACTIVE, ON_LEAVE, SUSPENDED, TERMINATED
- `hire_date` - When employee joined
- `termination_date` - When employee left

---

## Implementation Plan

### **Phase 1: Create Positions Table** (Day 1)

**New Model: Position**
```python
class Position(models.Model):
    name = CharField(unique=True)  # e.g., "Operator", "Supervisor", "QA Engineer"
    description = TextField  # Role responsibilities
    department = ForeignKey(Department)  # Link to department
    position_level = CharField(choices)  # ENTRY, JUNIOR, SENIOR, LEAD, MANAGER
    salary_grade = CharField  # e.g., "GRADE_A", "GRADE_B"
    created_at, updated_at
```

**Benefits:**
- Standardized job titles across organization
- Link positions to specific departments
- Track salary grades per position
- Define position hierarchies

---

### **Phase 2: Enhance Employee Type to Contract Type** (Day 1-2)

**Rename `employee_type` → `contract_type`** with new choices:

```python
CONTRACT_TYPE = (
    ("PERMANENT", "Permanent Employee"),
    ("FIXED_TERM", "Fixed Term Contract"),
    ("TEMPORARY", "Temporary"),
    ("PART_TIME", "Part-Time"),
    ("INTERN", "Internship"),
    ("CONSULTANT", "Consultant"),
    ("CONTRACTOR", "Contractor"),
)
```

**Why this is useful:**
- Better describes employment relationship
- Enables contract-specific workflows
- Supports compliance & HR policies
- Affects payroll, benefits, termination procedures

---

### **Phase 3: Add Contract-Related Fields** (Day 2)

**New fields needed for full contract description:**

1. **Contract Duration** (for non-permanent):
   - `contract_start_date` - When contract begins
   - `contract_end_date` - When contract ends
   - `contract_renewal_date` - Next review date

2. **Probation Period**:
   - `probation_end_date` - End of probation (if applicable)
   - `probation_status` (choices: PENDING, PASSED, FAILED)

3. **Work Schedule**:
   - `work_days_per_week` - Default 5
   - `hours_per_week` - Default 40
   - `shift_pattern` (choices: DAY, NIGHT, ROTATING)

4. **Compensation & Benefits**:
   - `salary_grade` - Link to position salary grade
   - `monthly_salary` - Base salary
   - `benefits_eligible` - Boolean (health insurance, etc.)
   - `overtime_eligible` - Boolean

5. **Leave Entitlements**:
   - `annual_leave_days` - Days per year
   - `sick_leave_days` - Days per year
   - `special_leave_days` - Days per year

6. **Employment Details**:
   - `employment_category` (REGULAR, SEASONAL, etc.)
   - `report_to` - ForeignKey to supervisor HREmployee
   - `cost_center` - Cost allocation code
   - `employment_status` - Additional to status field

---

### **Phase 4: Link to Departments** (Day 1)

**Add Department ForeignKey to HREmployee:**
```python
department = ForeignKey(Department, null=True, blank=True)
```

**This enables:**
- Automatic department assignment with position
- Department-specific reports
- Team structure visualization
- Cost center allocation

---

## Complete Updated HREmployee Model

```python
class HREmployee(PublicIdMixin, HRAuditMixin, HRSoftDeleteMixin):

    # Existing
    person = OneToOneField(HRPeople, on_delete=models.PROTECT)
    user = OneToOneField(User, on_delete=models.SET_NULL)
    employee_no = CharField(max_length=32, unique=True)
    status = CharField(choices=STATUS)  # ACTIVE, ON_LEAVE, SUSPENDED, TERMINATED

    # ENHANCED: Job Position
    position = ForeignKey(Position)  # REPLACES job_title CharField
    department = ForeignKey(Department)  # NEW

    # RENAMED: employee_type → contract_type
    contract_type = CharField(choices=CONTRACT_TYPE)  # PERMANENT, FIXED_TERM, TEMPORARY, etc.

    # NEW: Contract Duration Fields
    contract_start_date = DateField(null=True, blank=True)
    contract_end_date = DateField(null=True, blank=True)
    contract_renewal_date = DateField(null=True, blank=True)

    # NEW: Probation Fields
    probation_end_date = DateField(null=True, blank=True)
    probation_status = CharField(choices=PROBATION_STATUS, null=True, blank=True)

    # EXISTING
    hire_date = DateField(null=True, blank=True)
    termination_date = DateField(null=True, blank=True)

    # NEW: Work Schedule
    work_days_per_week = IntegerField(default=5)
    hours_per_week = IntegerField(default=40)
    shift_pattern = CharField(choices=SHIFT_CHOICES)

    # NEW: Compensation
    salary_grade = CharField(max_length=32)
    monthly_salary = DecimalField(max_digits=12, decimal_places=2)
    benefits_eligible = BooleanField(default=True)
    overtime_eligible = BooleanField(default=True)

    # NEW: Leave Entitlements
    annual_leave_days = IntegerField(default=20)
    sick_leave_days = IntegerField(default=10)
    special_leave_days = IntegerField(default=3)

    # NEW: Employment Details
    employment_category = CharField(choices=CATEGORY_CHOICES)
    report_to = ForeignKey(self, null=True, blank=True)  # Manager
    cost_center = CharField(max_length=32)
    employment_status = CharField(choices=EMPLOYMENT_STATUS)
```

---

## Benefits of This Structure

### **1. Contract Management**
- Track full contract lifecycle
- Know when contracts expire
- Manage renewal dates
- Probation period tracking

### **2. Compliance**
- Meet labor law requirements
- Track work hours & schedules
- Document salary information
- Maintain leave entitlements

### **3. Payroll Integration**
- Link salary to position
- Track overtime eligibility
- Calculate benefits deductions
- Generate payroll reports

### **4. HR Operations**
- Know reporting structure
- Allocate to cost centers
- Track employment categories
- Generate org charts

### **5. Analytics & Reporting**
- By contract type (permanent vs. temporary)
- By department & position
- By salary grade
- By employment status
- Probation success rates

---

## Data Migration Strategy

1. **Add new fields** with defaults/null=True
2. **Create Position model** first
3. **Backfill data**:
   - job_title text → Position references
   - team text → Department references
   - employee_type → contract_type
4. **Add default values** for new fields
5. **Test thoroughly** before going live

---

## Form Updates Required

**HREmployeeForm fields (NEW ORDER):**
1. Personal Info (person, user)
2. Employee Identification (employee_no, status)
3. Job Assignment
   - position (dropdown, replaces job_title)
   - department (dropdown, NEW)
4. Employment Type
   - contract_type (dropdown, renamed from employee_type)
5. Contract Duration (if not permanent)
   - contract_start_date
   - contract_end_date
   - contract_renewal_date
6. Probation (conditional fields)
   - probation_end_date
   - probation_status
7. Work Schedule
   - work_days_per_week
   - hours_per_week
   - shift_pattern
   - report_to (manager selection)
8. Compensation
   - salary_grade
   - monthly_salary
   - benefits_eligible
   - overtime_eligible
9. Leave Entitlements
   - annual_leave_days
   - sick_leave_days
   - special_leave_days
10. Additional Info
    - cost_center
    - employment_category
    - hire_date
    - termination_date

---

## Implementation Steps

### **Step 1: Create Position Model**
- Create `floor_app/hr/models/position.py`
- Add to `__init__.py`
- Create migration

### **Step 2: Update HREmployee Model**
- Add new fields
- Add foreign keys
- Rename fields
- Create migration

### **Step 3: Create Fixtures**
- Pre-populate positions for each department
- Define salary grades

### **Step 4: Update Forms**
- Update HREmployeeForm with new fields
- Add conditional fields (contract duration only for non-permanent)
- Add help text for each field

### **Step 5: Update Templates**
- Update employee form template
- Add new fields with proper grouping
- Add conditional display logic

### **Step 6: Migration & Backfill**
- Run migrations
- Backfill existing data
- Validate data integrity

### **Step 7: Testing**
- Test employee creation
- Test employee editing
- Test all combinations of contract types

---

## Timeline

- **Day 1**: Position model + initial HREmployee updates
- **Day 2**: Complete HREmployee updates + forms
- **Day 3**: Templates + migration + testing
- **Day 4**: Data backfill + validation

---

## Key Changes Summary

| Item | Current | New | Benefit |
|------|---------|-----|---------|
| Job Title | Text field | Position FK | Standardization |
| Department | Team text | Dept FK | Organization |
| Employee Type | OPERATOR, SUPERVISOR, etc. | CONTRACT_TYPE (PERMANENT, FIXED_TERM, etc.) | Better contract management |
| Contract Info | Just hire_date | Full contract lifecycle | Complete tracking |
| Work Schedule | Not tracked | Hours/days/shift | Scheduling & compliance |
| Compensation | Not tracked | Salary/benefits/grade | Payroll ready |
| Leave | Not tracked | Entitlements | HR operations |
| Reporting | Not tracked | report_to FK | Org structure |

---

## Questions to Consider

1. **Salary Management**: Store in Employee or separate Salary History model?
2. **Position Hierarchy**: Define position levels (ENTRY, SENIOR, etc.)?
3. **Cost Centers**: Pre-defined list or free text?
4. **Shift Patterns**: Fixed (DAY, NIGHT, ROTATING) or flexible?
5. **Leave Calculation**: Annual vs. per-contract?

---

**Ready to implement?** Let me know if you want any adjustments to this plan!
