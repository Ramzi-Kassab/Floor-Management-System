#!/usr/bin/env python
"""
Seed script to populate the Floor Management System with sample data.
Run with: python manage.py shell < seed_data.py
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'floor_mgmt.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

# Import all models
from floor_app.operations.hr.models import (
    HRPeople, HREmployee, Department, Position, HRPhone, HREmail
)
from floor_app.operations.inventory.models import (
    Item, ItemCategory, UnitOfMeasure, Location, ConditionType,
    InventoryStock, SerialUnit, BitDesign, BitDesignRevision, BOM
)
from floor_app.operations.production.models import (
    Batch, JobCard, Operation, ChecklistTemplate
)
from floor_app.operations.evaluation.models import (
    EvaluationSession, Code, Feature, Section, Type
)
from floor_app.operations.purchasing.models import (
    Supplier, PurchaseRequest, PurchaseOrder
)
from floor_app.operations.knowledge.models import (
    Category as KnowledgeCategory, Article, FAQ, Document,
    BusinessInstruction, Course, Lesson
)
from floor_app.operations.maintenance.models import (
    Asset, AssetCategory, MaintenanceLocation, WorkOrder, PreventiveMaintenancePlan
)
from floor_app.operations.quality.models import (
    NonConformanceReport, CalibrationEquipment, AcceptanceCriteria
)
from floor_app.operations.planning.models import (
    Resource, ProductionSchedule, KPIDefinition, KPIValue
)
from floor_app.operations.sales.models import (
    Customer, Rig, Well, SalesOpportunity, SalesOrder
)
from core.models import CostCenter, Currency

print("Starting data seeding...")

# Create superuser if not exists
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@floormanagement.com',
        password='admin123',
        first_name='System',
        last_name='Administrator'
    )
    print("Created admin user (admin/admin123)")
else:
    admin = User.objects.get(username='admin')
    print("Admin user already exists")

# Create additional users
users = []
user_data = [
    ('john.doe', 'John', 'Doe', 'john@example.com'),
    ('jane.smith', 'Jane', 'Smith', 'jane@example.com'),
    ('mike.wilson', 'Mike', 'Wilson', 'mike@example.com'),
    ('sarah.johnson', 'Sarah', 'Johnson', 'sarah@example.com'),
    ('ahmed.ali', 'Ahmed', 'Ali', 'ahmed@example.com'),
]

for username, first, last, email in user_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': first,
            'last_name': last,
            'email': email,
            'is_staff': True
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"Created user: {username}")
    users.append(user)

# =====================
# HR Module Data
# =====================
print("\nSeeding HR data...")

# Departments
departments = []
dept_names = [
    ('PROD', 'Production', 'Manufacturing and production operations'),
    ('QA', 'Quality Assurance', 'Quality control and assurance'),
    ('MAINT', 'Maintenance', 'Equipment maintenance and repairs'),
    ('HR', 'Human Resources', 'Employee management and HR'),
    ('IT', 'Information Technology', 'IT systems and support'),
    ('SALES', 'Sales', 'Sales and customer relations'),
    ('ENG', 'Engineering', 'Product design and engineering'),
]

for code, name, desc in dept_names:
    dept, created = Department.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'description': desc,
            'is_active': True,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    departments.append(dept)
    if created:
        print(f"  Created department: {name}")

# Positions
positions = []
position_data = [
    ('MGR', 'Manager', 'Department Manager'),
    ('SUPV', 'Supervisor', 'Team Supervisor'),
    ('TECH', 'Technician', 'Technical Specialist'),
    ('OPR', 'Operator', 'Machine Operator'),
    ('ENG', 'Engineer', 'Professional Engineer'),
    ('INSP', 'Inspector', 'Quality Inspector'),
]

for code, name, desc in position_data:
    pos, created = Position.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'description': desc,
            'is_active': True,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    positions.append(pos)
    if created:
        print(f"  Created position: {name}")

# People and Employees
people_data = [
    ('Mohammed', 'Ahmed', 'Al-Rashid', 'M', '1985-03-15', 'SA'),
    ('Fatima', 'Hassan', 'Al-Nasser', 'F', '1990-07-22', 'SA'),
    ('Omar', 'Khalid', 'Al-Mutairi', 'M', '1988-11-08', 'SA'),
    ('Noura', 'Ibrahim', 'Al-Qahtani', 'F', '1992-04-30', 'SA'),
    ('Abdullah', 'Saleh', 'Al-Dosari', 'M', '1983-09-12', 'SA'),
]

employees = []
for i, (first_en, middle_en, last_en, gender, dob, nationality) in enumerate(people_data):
    person, created = HRPeople.objects.get_or_create(
        first_name_en=first_en,
        last_name_en=last_en,
        defaults={
            'middle_name_en': middle_en,
            'gender': gender,
            'date_of_birth': dob,
            'primary_nationality_iso2': nationality,
            'created_by': admin,
            'updated_by': admin,
        }
    )

    if created:
        print(f"  Created person: {first_en} {last_en}")

        # Create employee record
        emp = HREmployee.objects.create(
            person=person,
            user=users[i] if i < len(users) else None,
            employee_no=f'EMP{1000 + i}',
            status='ACTIVE',
            department=random.choice(departments),
            position=random.choice(positions),
            hire_date=timezone.now().date() - timedelta(days=random.randint(100, 1000)),
            created_by=admin,
            updated_by=admin,
        )
        employees.append(emp)
        print(f"  Created employee: {emp.employee_no}")

# =====================
# Inventory Module Data
# =====================
print("\nSeeding Inventory data...")

# Categories
categories = []
cat_names = ['Drill Bits', 'Spare Parts', 'Raw Materials', 'Consumables', 'Tools']
for name in cat_names:
    cat, created = ItemCategory.objects.get_or_create(
        name=name,
        defaults={'description': f'{name} category', 'created_by': admin, 'updated_by': admin}
    )
    categories.append(cat)
    if created:
        print(f"  Created category: {name}")

# Units of Measure
uoms = []
uom_data = [('PCS', 'Pieces'), ('KG', 'Kilograms'), ('M', 'Meters'), ('L', 'Liters'), ('SET', 'Sets')]
for code, name in uom_data:
    uom, created = UnitOfMeasure.objects.get_or_create(
        code=code, defaults={'name': name, 'created_by': admin, 'updated_by': admin}
    )
    uoms.append(uom)
    if created:
        print(f"  Created UOM: {name}")

# Locations
locations = []
loc_names = ['Warehouse A', 'Warehouse B', 'Production Floor', 'Quality Lab', 'Shipping Area']
for name in loc_names:
    loc, created = Location.objects.get_or_create(
        name=name, defaults={'description': f'{name} storage', 'created_by': admin, 'updated_by': admin}
    )
    locations.append(loc)
    if created:
        print(f"  Created location: {name}")

# Condition Types
conditions = []
cond_names = ['NEW', 'USED', 'REFURBISHED', 'SCRAP']
for name in cond_names:
    cond, created = ConditionType.objects.get_or_create(
        name=name, defaults={'description': f'{name} condition', 'created_by': admin, 'updated_by': admin}
    )
    conditions.append(cond)
    if created:
        print(f"  Created condition: {name}")

# Items
items = []
item_data = [
    ('PDC-001', 'PDC Drill Bit 8.5"', 'PDC drill bit for soft to medium formations'),
    ('PDC-002', 'PDC Drill Bit 12.25"', 'PDC drill bit for directional drilling'),
    ('TCI-001', 'Tricone Bit 17.5"', 'Roller cone bit for hard formations'),
    ('SPR-001', 'Bearing Assembly', 'High-precision bearing for drill bits'),
    ('SPR-002', 'Seal Kit', 'Complete seal kit for bit maintenance'),
    ('RAW-001', 'Tungsten Carbide Powder', 'High-grade tungsten carbide for cutters'),
    ('CON-001', 'Cutting Fluid', 'Coolant for machining operations'),
    ('TOL-001', 'Thread Gauge Set', 'API thread inspection gauges'),
]

for sku, name, desc in item_data:
    item, created = Item.objects.get_or_create(
        sku=sku,
        defaults={
            'name': name,
            'description': desc,
            'category': random.choice(categories),
            'uom': random.choice(uoms),
            'unit_cost': Decimal(str(random.randint(100, 10000))),
            'reorder_point': random.randint(5, 20),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    items.append(item)
    if created:
        print(f"  Created item: {name}")

        # Create stock record
        InventoryStock.objects.create(
            item=item,
            location=random.choice(locations),
            quantity=random.randint(10, 100),
            condition=random.choice(conditions),
            created_by=admin,
            updated_by=admin,
        )

# Bit Designs
bit_designs = []
design_data = [
    ('BD-001', 'Matrix PDC 8.5"', 'Standard matrix body PDC design'),
    ('BD-002', 'Steel Body PDC 12.25"', 'High ROP steel body design'),
    ('BD-003', 'Hybrid Bit 17.5"', 'Combined PDC and roller cone design'),
]

for code, name, desc in design_data:
    design, created = BitDesign.objects.get_or_create(
        design_code=code,
        defaults={
            'name': name,
            'description': desc,
            'bit_type': 'PDC',
            'size_inches': Decimal('8.5'),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    bit_designs.append(design)
    if created:
        print(f"  Created bit design: {name}")

# Serial Units (for bit tracking)
serial_units = []
for i in range(5):
    sn = f'SN{2024}{str(i+1).zfill(4)}'
    unit, created = SerialUnit.objects.get_or_create(
        serial_number=sn,
        defaults={
            'item': random.choice([i for i in items if 'Drill Bit' in i.name]) if any('Drill Bit' in i.name for i in items) else items[0],
            'status': random.choice(['IN_STOCK', 'IN_USE', 'MAINTENANCE']),
            'location': random.choice(locations),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    serial_units.append(unit)
    if created:
        print(f"  Created serial unit: {sn}")

# =====================
# Production Module Data
# =====================
print("\nSeeding Production data...")

# Operations
operations = []
op_data = [
    ('TURN', 'Turning', 'CNC turning operation'),
    ('MILL', 'Milling', 'CNC milling operation'),
    ('GRIND', 'Grinding', 'Precision grinding'),
    ('WELD', 'Welding', 'TIG/MIG welding'),
    ('ASSY', 'Assembly', 'Final assembly'),
    ('INSP', 'Inspection', 'Quality inspection'),
]

for code, name, desc in op_data:
    op, created = Operation.objects.get_or_create(
        code=code,
        defaults={'name': name, 'description': desc, 'created_by': admin, 'updated_by': admin}
    )
    operations.append(op)
    if created:
        print(f"  Created operation: {name}")

# Batches
batches = []
for i in range(3):
    batch_no = f'BATCH-{2024}-{str(i+1).zfill(3)}'
    batch, created = Batch.objects.get_or_create(
        batch_number=batch_no,
        defaults={
            'description': f'Production batch {i+1}',
            'status': random.choice(['PLANNED', 'IN_PROGRESS', 'COMPLETED']),
            'planned_start': timezone.now() + timedelta(days=i*7),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    batches.append(batch)
    if created:
        print(f"  Created batch: {batch_no}")

# Job Cards
job_cards = []
for i in range(5):
    jc_no = f'JC-{2024}-{str(i+1).zfill(4)}'
    jc, created = JobCard.objects.get_or_create(
        job_card_number=jc_no,
        defaults={
            'batch': random.choice(batches) if batches else None,
            'serial_unit': random.choice(serial_units) if serial_units else None,
            'status': random.choice(['OPEN', 'IN_PROGRESS', 'EVALUATION', 'COMPLETED']),
            'priority': random.choice(['LOW', 'MEDIUM', 'HIGH', 'URGENT']),
            'description': f'Manufacturing job card {i+1}',
            'created_by': admin,
            'updated_by': admin,
        }
    )
    job_cards.append(jc)
    if created:
        print(f"  Created job card: {jc_no}")

# =====================
# Evaluation Module Data
# =====================
print("\nSeeding Evaluation data...")

# Codes
codes = []
code_data = [
    ('BT', 'Broken Teeth', 'Damaged or broken cutter teeth'),
    ('CT', 'Chipped Teeth', 'Chipped cutter surfaces'),
    ('ER', 'Erosion', 'Material erosion from fluid flow'),
    ('WT', 'Wear - Teeth', 'Normal wear on cutting structure'),
    ('JD', 'Junk Damage', 'Damage from downhole junk'),
]

for code, name, desc in code_data:
    c, created = Code.objects.get_or_create(
        code=code, defaults={'name': name, 'description': desc, 'created_by': admin, 'updated_by': admin}
    )
    codes.append(c)
    if created:
        print(f"  Created code: {name}")

# Features
features = []
feat_names = ['Inner Cone', 'Outer Cone', 'Shoulder', 'Gauge', 'Nose']
for name in feat_names:
    f, created = Feature.objects.get_or_create(
        name=name, defaults={'description': f'{name} area of bit', 'created_by': admin, 'updated_by': admin}
    )
    features.append(f)
    if created:
        print(f"  Created feature: {name}")

# Sections
sections = []
for i in range(1, 9):
    s, created = Section.objects.get_or_create(
        number=i, defaults={'name': f'Section {i}', 'created_by': admin, 'updated_by': admin}
    )
    sections.append(s)
    if created:
        print(f"  Created section: Section {i}")

# Types
types = []
type_names = ['Initial', 'Interim', 'Final', 'Re-evaluation']
for name in type_names:
    t, created = Type.objects.get_or_create(
        name=name, defaults={'description': f'{name} evaluation type', 'created_by': admin, 'updated_by': admin}
    )
    types.append(t)
    if created:
        print(f"  Created type: {name}")

# Evaluation Sessions
for i in range(3):
    if job_cards and serial_units:
        session, created = EvaluationSession.objects.get_or_create(
            session_number=f'EVAL-{2024}-{str(i+1).zfill(4)}',
            defaults={
                'job_card': job_cards[i] if i < len(job_cards) else job_cards[0],
                'serial_unit': serial_units[i] if i < len(serial_units) else serial_units[0],
                'evaluation_type': random.choice(types) if types else None,
                'status': random.choice(['DRAFT', 'IN_PROGRESS', 'UNDER_REVIEW', 'APPROVED']),
                'evaluator': admin,
                'created_by': admin,
                'updated_by': admin,
            }
        )
        if created:
            print(f"  Created evaluation session: EVAL-{2024}-{str(i+1).zfill(4)}")

# =====================
# Knowledge Module Data
# =====================
print("\nSeeding Knowledge data...")

# Knowledge Categories
kb_categories = []
kb_cat_names = [
    ('Operations', 'Operational procedures and guidelines'),
    ('Safety', 'Safety protocols and requirements'),
    ('Quality', 'Quality standards and procedures'),
    ('Training', 'Training materials and courses'),
    ('Technical', 'Technical documentation'),
]

for name, desc in kb_cat_names:
    cat, created = KnowledgeCategory.objects.get_or_create(
        name=name, defaults={'description': desc, 'created_by': admin, 'updated_by': admin}
    )
    kb_categories.append(cat)
    if created:
        print(f"  Created knowledge category: {name}")

# Articles
articles_data = [
    ('Bit Evaluation Procedure', 'Standard operating procedure for drill bit evaluation', 'operations'),
    ('Thread Inspection Guidelines', 'API thread inspection requirements and methods', 'quality'),
    ('NDT Testing Procedures', 'Non-destructive testing procedures for bit inspection', 'technical'),
    ('Safety Equipment Requirements', 'Required PPE for shop floor operations', 'safety'),
    ('Quality Control Checklist', 'Daily quality control verification checklist', 'quality'),
]

for title, desc, cat_name in articles_data:
    cat = next((c for c in kb_categories if c.name.lower() == cat_name), kb_categories[0])
    article, created = Article.objects.get_or_create(
        title=title,
        defaults={
            'content': f'# {title}\n\n{desc}\n\n## Overview\n\nThis document provides comprehensive guidance...',
            'category': cat,
            'status': 'PUBLISHED',
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created article: {title}")

# FAQs
faq_data = [
    ('How do I start an evaluation?', 'Navigate to Evaluation > New Session and select the job card.'),
    ('What is the difference between codes?', 'Codes represent different types of damage or wear patterns.'),
    ('How to request maintenance?', 'Use Maintenance > New Request to submit a maintenance request.'),
]

for question, answer in faq_data:
    faq, created = FAQ.objects.get_or_create(
        question=question,
        defaults={
            'answer': answer,
            'category': random.choice(kb_categories),
            'is_published': True,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created FAQ: {question[:50]}...")

# Business Instructions (THE KEY FEATURE!)
print("\n  Creating Business Instructions...")
instruction_data = [
    {
        'name': 'Auto-assign Priority for Damaged Bits',
        'description': 'Automatically assigns HIGH priority when bit has critical damage codes',
        'trigger_model': 'evaluation.EvaluationSession',
        'trigger_event': 'CREATE',
        'condition_field': 'status',
        'condition_operator': 'EQUALS',
        'condition_value': 'IN_PROGRESS',
        'action_type': 'SET_FIELD',
        'action_target': 'priority',
        'action_value': 'HIGH',
    },
    {
        'name': 'Notify Manager on Evaluation Complete',
        'description': 'Sends notification to department manager when evaluation is completed',
        'trigger_model': 'evaluation.EvaluationSession',
        'trigger_event': 'UPDATE',
        'condition_field': 'status',
        'condition_operator': 'EQUALS',
        'condition_value': 'APPROVED',
        'action_type': 'NOTIFY',
        'action_target': 'manager',
        'action_value': 'Evaluation session has been approved',
    },
    {
        'name': 'Low Stock Alert',
        'description': 'Creates alert when inventory falls below reorder point',
        'trigger_model': 'inventory.InventoryStock',
        'trigger_event': 'UPDATE',
        'condition_field': 'quantity',
        'condition_operator': 'LESS_THAN',
        'condition_value': '10',
        'action_type': 'CREATE_ALERT',
        'action_target': 'purchasing',
        'action_value': 'Low stock alert - reorder needed',
    },
    {
        'name': 'Auto-create Maintenance Request',
        'description': 'Automatically creates maintenance request for overdue PM',
        'trigger_model': 'maintenance.PreventiveMaintenancePlan',
        'trigger_event': 'SCHEDULE',
        'condition_field': 'due_date',
        'condition_operator': 'PAST_DUE',
        'condition_value': '0',
        'action_type': 'CREATE_RECORD',
        'action_target': 'maintenance.WorkOrder',
        'action_value': 'Overdue PM task',
    },
    {
        'name': 'Quality Hold on NCR',
        'description': 'Places item on quality hold when NCR is created',
        'trigger_model': 'quality.NonConformanceReport',
        'trigger_event': 'CREATE',
        'condition_field': 'severity',
        'condition_operator': 'EQUALS',
        'condition_value': 'CRITICAL',
        'action_type': 'SET_FIELD',
        'action_target': 'quality_hold',
        'action_value': 'True',
    },
]

for inst_data in instruction_data:
    inst, created = BusinessInstruction.objects.get_or_create(
        name=inst_data['name'],
        defaults={
            'description': inst_data['description'],
            'trigger_model': inst_data['trigger_model'],
            'trigger_event': inst_data['trigger_event'],
            'condition_field': inst_data['condition_field'],
            'condition_operator': inst_data['condition_operator'],
            'condition_value': inst_data['condition_value'],
            'action_type': inst_data['action_type'],
            'action_target': inst_data['action_target'],
            'action_value': inst_data['action_value'],
            'is_active': True,
            'priority': random.randint(1, 10),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"    Created instruction: {inst_data['name']}")

# Courses
courses_data = [
    ('Bit Evaluation Fundamentals', 'Learn the basics of drill bit evaluation', 60),
    ('Advanced NDT Techniques', 'Advanced non-destructive testing methods', 120),
    ('Safety Certification', 'Complete safety certification course', 90),
]

courses = []
for title, desc, duration in courses_data:
    course, created = Course.objects.get_or_create(
        title=title,
        defaults={
            'description': desc,
            'duration_minutes': duration,
            'is_published': True,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    courses.append(course)
    if created:
        print(f"  Created course: {title}")

        # Create lessons for each course
        for i in range(3):
            Lesson.objects.create(
                course=course,
                title=f'{title} - Module {i+1}',
                content=f'Lesson content for module {i+1}...',
                order=i+1,
                duration_minutes=duration // 3,
                created_by=admin,
                updated_by=admin,
            )

# =====================
# Purchasing Module Data
# =====================
print("\nSeeding Purchasing data...")

# Suppliers
suppliers = []
supplier_data = [
    ('SUP-001', 'Tungsten Carbide Corp', 'contact@tcc.com', '+1-555-0101'),
    ('SUP-002', 'Steel Solutions Ltd', 'sales@steelsol.com', '+1-555-0102'),
    ('SUP-003', 'Industrial Bearings Inc', 'orders@indbear.com', '+1-555-0103'),
]

for code, name, email, phone in supplier_data:
    sup, created = Supplier.objects.get_or_create(
        supplier_code=code,
        defaults={
            'name': name,
            'email': email,
            'phone': phone,
            'is_active': True,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    suppliers.append(sup)
    if created:
        print(f"  Created supplier: {name}")

# Purchase Requests
for i in range(3):
    pr_no = f'PR-{2024}-{str(i+1).zfill(4)}'
    pr, created = PurchaseRequest.objects.get_or_create(
        pr_number=pr_no,
        defaults={
            'requester': admin,
            'department': random.choice(departments) if departments else None,
            'status': random.choice(['DRAFT', 'SUBMITTED', 'APPROVED']),
            'priority': random.choice(['LOW', 'MEDIUM', 'HIGH']),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created purchase request: {pr_no}")

# =====================
# Maintenance Module Data
# =====================
print("\nSeeding Maintenance data...")

# Asset Categories
asset_categories = []
ac_names = ['CNC Machine', 'Grinding Machine', 'Inspection Equipment', 'Hand Tools']
for name in ac_names:
    ac, created = AssetCategory.objects.get_or_create(
        name=name, defaults={'description': f'{name} category', 'created_by': admin, 'updated_by': admin}
    )
    asset_categories.append(ac)
    if created:
        print(f"  Created asset category: {name}")

# Maintenance Locations
maint_locations = []
ml_names = ['Shop Floor', 'Machine Room', 'Quality Lab', 'Tool Room']
for name in ml_names:
    ml, created = MaintenanceLocation.objects.get_or_create(
        name=name, defaults={'description': f'{name} area', 'created_by': admin, 'updated_by': admin}
    )
    maint_locations.append(ml)
    if created:
        print(f"  Created maintenance location: {name}")

# Assets
assets = []
asset_data = [
    ('AST-001', 'CNC Lathe #1', 'Haas ST-10 CNC Lathe'),
    ('AST-002', 'Vertical Mill #1', 'Haas VF-2 Vertical Mill'),
    ('AST-003', 'Surface Grinder', 'Okamoto ACC-8-20ST'),
    ('AST-004', 'CMM Machine', 'Zeiss Contura Coordinate Measuring Machine'),
]

for code, name, desc in asset_data:
    asset, created = Asset.objects.get_or_create(
        asset_code=code,
        defaults={
            'name': name,
            'description': desc,
            'category': random.choice(asset_categories) if asset_categories else None,
            'location': random.choice(maint_locations) if maint_locations else None,
            'status': 'OPERATIONAL',
            'purchase_date': timezone.now().date() - timedelta(days=random.randint(365, 1825)),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    assets.append(asset)
    if created:
        print(f"  Created asset: {name}")

# Work Orders
for i in range(3):
    wo_no = f'WO-{2024}-{str(i+1).zfill(4)}'
    wo, created = WorkOrder.objects.get_or_create(
        work_order_number=wo_no,
        defaults={
            'asset': random.choice(assets) if assets else None,
            'description': f'Maintenance work order {i+1}',
            'priority': random.choice(['LOW', 'MEDIUM', 'HIGH', 'EMERGENCY']),
            'status': random.choice(['OPEN', 'IN_PROGRESS', 'COMPLETED']),
            'assigned_to': random.choice(users) if users else admin,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created work order: {wo_no}")

# =====================
# Quality Module Data
# =====================
print("\nSeeding Quality data...")

# Acceptance Criteria
criteria_data = [
    ('Thread Pitch', 'API thread pitch tolerance', 'pitch_deviation', -0.001, 0.001, 'inches'),
    ('Surface Finish', 'Surface roughness requirement', 'roughness_ra', 0, 32, 'microinches'),
    ('Hardness', 'Material hardness range', 'hardness_hrc', 58, 62, 'HRC'),
]

for name, desc, field, min_val, max_val, unit in criteria_data:
    crit, created = AcceptanceCriteria.objects.get_or_create(
        name=name,
        defaults={
            'description': desc,
            'measurement_field': field,
            'min_value': Decimal(str(min_val)),
            'max_value': Decimal(str(max_val)),
            'unit': unit,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created acceptance criteria: {name}")

# Calibration Equipment
calib_data = [
    ('CAL-001', 'Thread Gauge Set', '2025-01-15'),
    ('CAL-002', 'Micrometer Set', '2025-02-20'),
    ('CAL-003', 'Surface Roughness Tester', '2025-03-10'),
]

for code, name, cal_date in calib_data:
    eq, created = CalibrationEquipment.objects.get_or_create(
        equipment_code=code,
        defaults={
            'name': name,
            'next_calibration_date': cal_date,
            'calibration_interval_days': 365,
            'status': 'CALIBRATED',
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created calibration equipment: {name}")

# Non-Conformance Reports
for i in range(2):
    ncr_no = f'NCR-{2024}-{str(i+1).zfill(4)}'
    ncr, created = NonConformanceReport.objects.get_or_create(
        ncr_number=ncr_no,
        defaults={
            'description': f'Non-conformance issue {i+1}',
            'severity': random.choice(['MINOR', 'MAJOR', 'CRITICAL']),
            'status': random.choice(['OPEN', 'UNDER_INVESTIGATION', 'CLOSED']),
            'reported_by': admin,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created NCR: {ncr_no}")

# =====================
# Planning Module Data
# =====================
print("\nSeeding Planning data...")

# Resources
resources = []
resource_data = [
    ('CNC-LATHE', 'CNC Lathe Capacity', 'MACHINE', 8),
    ('CNC-MILL', 'CNC Mill Capacity', 'MACHINE', 8),
    ('GRIND-CAP', 'Grinding Capacity', 'MACHINE', 8),
    ('OPER-SHIFT', 'Operator Shift', 'LABOR', 8),
]

for code, name, res_type, hours in resource_data:
    res, created = Resource.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'resource_type': res_type,
            'available_hours_per_day': hours,
            'efficiency_percent': Decimal('85'),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    resources.append(res)
    if created:
        print(f"  Created resource: {name}")

# KPI Definitions
kpi_defs = []
kpi_data = [
    ('OTD', 'On-Time Delivery', '%', Decimal('95'), 'HIGHER_BETTER'),
    ('FPY', 'First Pass Yield', '%', Decimal('98'), 'HIGHER_BETTER'),
    ('OEE', 'Overall Equipment Effectiveness', '%', Decimal('85'), 'HIGHER_BETTER'),
    ('MTTR', 'Mean Time To Repair', 'hours', Decimal('4'), 'LOWER_BETTER'),
    ('SCRAP', 'Scrap Rate', '%', Decimal('2'), 'LOWER_BETTER'),
]

for code, name, unit, target, direction in kpi_data:
    kpi_def, created = KPIDefinition.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'unit': unit,
            'target_value': target,
            'direction': direction,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    kpi_defs.append(kpi_def)
    if created:
        print(f"  Created KPI definition: {name}")

        # Add sample KPI values
        for i in range(5):
            KPIValue.objects.create(
                kpi_definition=kpi_def,
                value=target + Decimal(str(random.uniform(-5, 5))),
                recorded_date=timezone.now().date() - timedelta(days=i*7),
                recorded_by=admin,
                created_by=admin,
                updated_by=admin,
            )

# Production Schedules
for i in range(2):
    sched_no = f'SCHED-{2024}-{str(i+1).zfill(3)}'
    sched, created = ProductionSchedule.objects.get_or_create(
        schedule_number=sched_no,
        defaults={
            'name': f'Production Schedule Week {i+1}',
            'start_date': timezone.now().date() + timedelta(days=i*7),
            'end_date': timezone.now().date() + timedelta(days=(i+1)*7),
            'status': 'DRAFT' if i > 0 else 'PUBLISHED',
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created schedule: {sched_no}")

# =====================
# Sales Module Data
# =====================
print("\nSeeding Sales data...")

# Customers
customers = []
customer_data = [
    ('CUST-001', 'Saudi Aramco', 'Oil & Gas Operator'),
    ('CUST-002', 'ADNOC', 'National Oil Company'),
    ('CUST-003', 'Kuwait Oil Company', 'Oil Producer'),
]

for code, name, desc in customer_data:
    cust, created = Customer.objects.get_or_create(
        customer_code=code,
        defaults={
            'name': name,
            'description': desc,
            'is_active': True,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    customers.append(cust)
    if created:
        print(f"  Created customer: {name}")

# Rigs
rigs = []
for i, cust in enumerate(customers[:2]):
    rig, created = Rig.objects.get_or_create(
        rig_name=f'Rig {i+1}',
        defaults={
            'customer': cust,
            'rig_type': 'LAND',
            'location': 'Saudi Arabia',
            'is_active': True,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    rigs.append(rig)
    if created:
        print(f"  Created rig: Rig {i+1}")

# Wells
wells = []
for i, rig in enumerate(rigs):
    well, created = Well.objects.get_or_create(
        well_name=f'Well {chr(65+i)}-{i+1}',
        defaults={
            'rig': rig,
            'well_type': 'VERTICAL',
            'depth_target': Decimal(str(random.randint(5000, 15000))),
            'status': 'DRILLING',
            'created_by': admin,
            'updated_by': admin,
        }
    )
    wells.append(well)
    if created:
        print(f"  Created well: Well {chr(65+i)}-{i+1}")

# Sales Opportunities
for i in range(3):
    opp, created = SalesOpportunity.objects.get_or_create(
        opportunity_name=f'Opportunity {i+1}',
        defaults={
            'customer': random.choice(customers),
            'estimated_value': Decimal(str(random.randint(50000, 500000))),
            'probability_percent': random.randint(20, 90),
            'status': random.choice(['PROSPECTING', 'QUALIFICATION', 'PROPOSAL', 'NEGOTIATION']),
            'expected_close_date': timezone.now().date() + timedelta(days=random.randint(30, 180)),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created opportunity: Opportunity {i+1}")

# Sales Orders
for i in range(2):
    so_no = f'SO-{2024}-{str(i+1).zfill(4)}'
    so, created = SalesOrder.objects.get_or_create(
        order_number=so_no,
        defaults={
            'customer': random.choice(customers),
            'status': random.choice(['DRAFT', 'CONFIRMED', 'IN_PRODUCTION']),
            'total_amount': Decimal(str(random.randint(10000, 100000))),
            'created_by': admin,
            'updated_by': admin,
        }
    )
    if created:
        print(f"  Created sales order: {so_no}")

# =====================
# Core Module Data
# =====================
print("\nSeeding Core data...")

# Cost Centers
cost_centers = []
cc_data = [
    ('CC-PROD', 'Production', 'Manufacturing cost center'),
    ('CC-ADMIN', 'Administration', 'Administrative overhead'),
    ('CC-SALES', 'Sales', 'Sales and marketing'),
    ('CC-RD', 'R&D', 'Research and development'),
]

for code, name, desc in cc_data:
    cc, created = CostCenter.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'description': desc,
            'is_active': True,
            'created_by': admin,
            'updated_by': admin,
        }
    )
    cost_centers.append(cc)
    if created:
        print(f"  Created cost center: {name}")

# Currency
currencies = []
curr_data = [
    ('SAR', 'Saudi Riyal', 'ر.س', Decimal('1.0000')),
    ('USD', 'US Dollar', '$', Decimal('3.7500')),
    ('EUR', 'Euro', '€', Decimal('4.0500')),
]

for code, name, symbol, rate in curr_data:
    curr, created = Currency.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'symbol': symbol,
            'exchange_rate': rate,
            'is_base': code == 'SAR',
            'created_by': admin,
            'updated_by': admin,
        }
    )
    currencies.append(curr)
    if created:
        print(f"  Created currency: {name}")

print("\n" + "="*50)
print("DATA SEEDING COMPLETED SUCCESSFULLY!")
print("="*50)
print(f"\nLogin credentials:")
print(f"  Admin: admin / admin123")
print(f"  Users: john.doe, jane.smith, etc. / password123")
print(f"\nCreated data summary:")
print(f"  - {User.objects.count()} users")
print(f"  - {Department.objects.count()} departments")
print(f"  - {HREmployee.objects.count()} employees")
print(f"  - {Item.objects.count()} inventory items")
print(f"  - {SerialUnit.objects.count()} serial units")
print(f"  - {JobCard.objects.count()} job cards")
print(f"  - {EvaluationSession.objects.count()} evaluation sessions")
print(f"  - {Article.objects.count()} knowledge articles")
print(f"  - {BusinessInstruction.objects.count()} business instructions")
print(f"  - {Course.objects.count()} training courses")
print(f"  - {Asset.objects.count()} maintenance assets")
print(f"  - {Customer.objects.count()} customers")
print(f"  - {KPIDefinition.objects.count()} KPI definitions")
