"""
Django management command to seed the database with sample data.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

# Import models
from floor_app.operations.hr.models import Department, Position, HRPeople, HREmployee
from floor_app.operations.inventory.models import (
    ItemCategory, UnitOfMeasure, Location, ConditionType,
    Item, InventoryStock, SerialUnit, BitDesign
)
from floor_app.operations.production.models import BatchOrder, JobCard, OperationDefinition
from floor_app.operations.evaluation.models import (
    EvaluationSession, CutterEvaluationCode, FeatureCode, BitSection, BitType
)
from floor_app.operations.knowledge.models import (
    Category as KnowledgeCategory, Article, FAQEntry, InstructionRule as BusinessInstruction,
    TrainingCourse, TrainingLesson
)
from floor_app.operations.maintenance.models import (
    Asset, AssetCategory, AssetLocation as MaintenanceLocation, WorkOrder
)
from floor_app.operations.quality.models import (
    NonconformanceReport, CalibratedEquipment, AcceptanceCriteriaTemplate
)
from floor_app.operations.planning.models import ResourceCapacity, ProductionSchedule, KPIDefinition, KPIValue
from floor_app.operations.sales.models import Customer, SalesOpportunity, SalesOrder
from core.models import CostCenter, Currency


class Command(BaseCommand):
    help = 'Seeds the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Starting data seeding...\n')

        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@floormanagement.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user (admin/admin123)'))

        # Create sample users
        users = []
        for username, first, last in [('john', 'John', 'Doe'), ('jane', 'Jane', 'Smith'), ('mike', 'Mike', 'Wilson')]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first, 'last_name': last, 'email': f'{username}@example.com', 'is_staff': True}
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {username}')
            users.append(user)

        # ===== HR DATA =====
        self.stdout.write('\nSeeding HR data...')

        # Departments
        departments = []
        for name in ['Production', 'Quality Assurance', 'Maintenance', 'Human Resources']:
            dept, created = Department.objects.get_or_create(
                name=name, defaults={'description': f'{name} department', 'department_type': 'PRODUCTION'}
            )
            departments.append(dept)
            if created:
                self.stdout.write(f'  Created department: {name}')

        # Positions
        positions = []
        for name in ['Manager', 'Supervisor', 'Technician', 'Operator']:
            pos, created = Position.objects.get_or_create(
                name=name, defaults={'description': f'{name} position', 'department': departments[0] if departments else None}
            )
            positions.append(pos)
            if created:
                self.stdout.write(f'  Created position: {name}')

        # People & Employees
        for first, last, gender in [('Mohammed', 'Al-Rashid', 'M'), ('Fatima', 'Al-Nasser', 'F'), ('Omar', 'Al-Mutairi', 'M')]:
            try:
                person, created = HRPeople.objects.get_or_create(
                    first_name_en=first, last_name_en=last,
                    defaults={'gender': gender, 'date_of_birth': date(1985, 1, 1), 'primary_nationality_iso2': 'SA', 'created_by': admin, 'updated_by': admin}
                )
                if created:
                    emp_no = f'EMP{HREmployee.objects.count() + 1000}'
                    HREmployee.objects.create(
                        person=person, employee_no=emp_no, status='ACTIVE', department=random.choice(departments),
                        position=random.choice(positions), hire_date=timezone.now().date() - timedelta(days=365),
                        created_by=admin, updated_by=admin
                    )
                    self.stdout.write(f'  Created employee: {first} {last}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Skipped employee {first} {last}: {str(e)[:100]}'))

        # ===== INVENTORY DATA =====
        self.stdout.write('\nSeeding Inventory data...')

        # Categories
        categories = []
        for code, name in [('BITS', 'Drill Bits'), ('SPARE', 'Spare Parts'), ('RAW', 'Raw Materials'), ('TOOLS', 'Tools')]:
            try:
                cat, created = ItemCategory.objects.get_or_create(
                    name=name, defaults={'code': code, 'description': f'{name} category', 'created_by': admin, 'updated_by': admin}
                )
                categories.append(cat)
                if created:
                    self.stdout.write(f'  Created category: {name}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Skipped category {name}: {str(e)[:50]}'))

        # UOM
        uoms = []
        for code, name in [('PCS', 'Pieces'), ('KG', 'Kilograms'), ('M', 'Meters')]:
            uom, created = UnitOfMeasure.objects.get_or_create(
                code=code, defaults={'name': name, 'created_by': admin, 'updated_by': admin}
            )
            uoms.append(uom)
            if created:
                self.stdout.write(f'  Created UOM: {name}')

        # Locations
        locations = []
        for name in ['Warehouse A', 'Warehouse B', 'Production Floor']:
            loc, created = Location.objects.get_or_create(
                name=name, defaults={'description': f'{name} storage', 'created_by': admin, 'updated_by': admin}
            )
            locations.append(loc)
            if created:
                self.stdout.write(f'  Created location: {name}')

        # Conditions
        conditions = []
        for name in ['NEW', 'USED', 'REFURBISHED']:
            cond, created = ConditionType.objects.get_or_create(
                name=name, defaults={'description': f'{name} condition', 'created_by': admin, 'updated_by': admin}
            )
            conditions.append(cond)
            if created:
                self.stdout.write(f'  Created condition: {name}')

        # Items
        items = []
        for sku, name in [('PDC-001', 'PDC Drill Bit 8.5"'), ('PDC-002', 'PDC Drill Bit 12.25"'), ('SPR-001', 'Bearing Assembly')]:
            item, created = Item.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name, 'description': f'{name} description', 'category': categories[0] if categories else None,
                    'uom': uoms[0] if uoms else None, 'unit_cost': Decimal('1000'), 'reorder_point': 10,
                    'created_by': admin, 'updated_by': admin
                }
            )
            items.append(item)
            if created:
                InventoryStock.objects.create(
                    item=item, location=locations[0] if locations else None, quantity=50,
                    condition=conditions[0] if conditions else None, created_by=admin, updated_by=admin
                )
                self.stdout.write(f'  Created item: {name}')

        # Serial Units
        serial_units = []
        for i in range(5):
            sn = f'SN2024{str(i+1).zfill(4)}'
            unit, created = SerialUnit.objects.get_or_create(
                serial_number=sn,
                defaults={
                    'item': items[0] if items else None, 'status': 'IN_STOCK',
                    'location': locations[0] if locations else None, 'created_by': admin, 'updated_by': admin
                }
            )
            serial_units.append(unit)
            if created:
                self.stdout.write(f'  Created serial unit: {sn}')

        # ===== PRODUCTION DATA =====
        self.stdout.write('\nSeeding Production data...')

        # Operations
        for code, name in [('TURN', 'Turning'), ('MILL', 'Milling'), ('GRIND', 'Grinding'), ('INSP', 'Inspection')]:
            op, created = OperationDefinition.objects.get_or_create(
                code=code, defaults={'name': name, 'description': f'{name} operation', 'created_by': admin, 'updated_by': admin}
            )
            if created:
                self.stdout.write(f'  Created operation: {name}')

        # Batches
        batches = []
        for i in range(3):
            batch_no = f'BATCH-2024-{str(i+1).zfill(3)}'
            batch, created = BatchOrder.objects.get_or_create(
                batch_number=batch_no,
                defaults={
                    'description': f'Production batch {i+1}', 'status': 'IN_PROGRESS',
                    'planned_start': timezone.now() + timedelta(days=i*7), 'created_by': admin, 'updated_by': admin
                }
            )
            batches.append(batch)
            if created:
                self.stdout.write(f'  Created batch: {batch_no}')

        # Job Cards
        job_cards = []
        for i in range(5):
            jc_no = f'JC-2024-{str(i+1).zfill(4)}'
            jc, created = JobCard.objects.get_or_create(
                job_card_number=jc_no,
                defaults={
                    'batch': batches[i % len(batches)] if batches else None,
                    'serial_unit': serial_units[i] if i < len(serial_units) else None,
                    'status': random.choice(['OPEN', 'IN_PROGRESS', 'EVALUATION']),
                    'priority': random.choice(['LOW', 'MEDIUM', 'HIGH']),
                    'description': f'Job card {i+1}', 'created_by': admin, 'updated_by': admin
                }
            )
            job_cards.append(jc)
            if created:
                self.stdout.write(f'  Created job card: {jc_no}')

        # ===== EVALUATION DATA =====
        self.stdout.write('\nSeeding Evaluation data...')

        # Codes
        for code, name in [('BT', 'Broken Teeth'), ('CT', 'Chipped Teeth'), ('ER', 'Erosion'), ('WT', 'Wear - Teeth')]:
            c, created = CutterEvaluationCode.objects.get_or_create(
                code=code, defaults={'name': name, 'description': f'{name} damage', 'created_by': admin, 'updated_by': admin}
            )
            if created:
                self.stdout.write(f'  Created code: {name}')

        # Features
        for code, name in [('IC', 'Inner Cone'), ('OC', 'Outer Cone'), ('SH', 'Shoulder'), ('GA', 'Gauge')]:
            f, created = FeatureCode.objects.get_or_create(
                code=code, defaults={'name': name, 'description': f'{name} area', 'created_by': admin, 'updated_by': admin}
            )
            if created:
                self.stdout.write(f'  Created feature: {name}')

        # Sections
        sections = []
        for i in range(1, 9):
            s, created = BitSection.objects.get_or_create(
                section_number=i, defaults={'name': f'Section {i}', 'created_by': admin, 'updated_by': admin}
            )
            sections.append(s)
            if created:
                self.stdout.write(f'  Created section: Section {i}')

        # Types
        types = []
        for code, name in [('INIT', 'Initial'), ('INTER', 'Interim'), ('FINAL', 'Final')]:
            t, created = BitType.objects.get_or_create(
                code=code, defaults={'name': name, 'description': f'{name} evaluation', 'created_by': admin, 'updated_by': admin}
            )
            types.append(t)
            if created:
                self.stdout.write(f'  Created type: {name}')

        # Evaluation Sessions
        for i in range(3):
            if job_cards and serial_units:
                sess_no = f'EVAL-2024-{str(i+1).zfill(4)}'
                session, created = EvaluationSession.objects.get_or_create(
                    session_number=sess_no,
                    defaults={
                        'job_card': job_cards[i] if i < len(job_cards) else job_cards[0],
                        'serial_unit': serial_units[i] if i < len(serial_units) else serial_units[0],
                        'evaluation_type': types[i % len(types)] if types else None,
                        'status': random.choice(['DRAFT', 'IN_PROGRESS', 'UNDER_REVIEW']),
                        'evaluator': admin, 'created_by': admin, 'updated_by': admin
                    }
                )
                if created:
                    self.stdout.write(f'  Created evaluation session: {sess_no}')

        # ===== KNOWLEDGE DATA (INCLUDING BUSINESS INSTRUCTIONS!) =====
        self.stdout.write('\nSeeding Knowledge data...')

        # Knowledge Categories
        kb_cats = []
        for name in ['Operations', 'Safety', 'Quality', 'Technical']:
            cat, created = KnowledgeCategory.objects.get_or_create(
                name=name, defaults={'description': f'{name} documentation', 'created_by': admin, 'updated_by': admin}
            )
            kb_cats.append(cat)
            if created:
                self.stdout.write(f'  Created knowledge category: {name}')

        # Articles
        for title in ['Bit Evaluation Procedure', 'Thread Inspection Guidelines', 'Safety Equipment Requirements']:
            article, created = Article.objects.get_or_create(
                title=title,
                defaults={
                    'content': f'# {title}\n\nDetailed content for {title}...',
                    'category': kb_cats[0] if kb_cats else None,
                    'status': 'PUBLISHED', 'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created article: {title}')

        # FAQs
        for question, answer in [
            ('How do I start an evaluation?', 'Navigate to Evaluation > New Session'),
            ('What is the difference between codes?', 'Codes represent damage patterns'),
        ]:
            faq, created = FAQEntry.objects.get_or_create(
                question=question,
                defaults={
                    'answer': answer, 'category': kb_cats[0] if kb_cats else None,
                    'is_published': True, 'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created FAQ: {question[:40]}...')

        # ===== BUSINESS INSTRUCTIONS (KEY FEATURE!) =====
        self.stdout.write('\n  Creating Business Instructions...')
        instructions_data = [
            {
                'name': 'Auto-assign Priority for Critical Damage',
                'description': 'Automatically assigns HIGH priority when critical damage is detected',
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
                'name': 'Low Stock Alert Rule',
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
                'name': 'Quality Hold on NCR',
                'description': 'Places item on quality hold when critical NCR is created',
                'trigger_model': 'quality.NonConformanceReport',
                'trigger_event': 'CREATE',
                'condition_field': 'severity',
                'condition_operator': 'EQUALS',
                'condition_value': 'CRITICAL',
                'action_type': 'SET_FIELD',
                'action_target': 'quality_hold',
                'action_value': 'True',
            },
            {
                'name': 'Notify Manager on Approval',
                'description': 'Sends notification when evaluation is approved',
                'trigger_model': 'evaluation.EvaluationSession',
                'trigger_event': 'UPDATE',
                'condition_field': 'status',
                'condition_operator': 'EQUALS',
                'condition_value': 'APPROVED',
                'action_type': 'NOTIFY',
                'action_target': 'manager',
                'action_value': 'Evaluation session approved',
            },
            {
                'name': 'Auto-create Maintenance Request',
                'description': 'Creates maintenance request for overdue PM',
                'trigger_model': 'maintenance.PreventiveMaintenancePlan',
                'trigger_event': 'SCHEDULE',
                'condition_field': 'due_date',
                'condition_operator': 'PAST_DUE',
                'condition_value': '0',
                'action_type': 'CREATE_RECORD',
                'action_target': 'maintenance.WorkOrder',
                'action_value': 'Overdue PM task',
            },
        ]

        for inst_data in instructions_data:
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
                self.stdout.write(self.style.SUCCESS(f'    Created instruction: {inst_data["name"]}'))

        # Courses
        for title, duration in [('Bit Evaluation Fundamentals', 60), ('Safety Certification', 90)]:
            course, created = TrainingCourse.objects.get_or_create(
                title=title,
                defaults={
                    'description': f'{title} course', 'duration_minutes': duration,
                    'is_published': True, 'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                for i in range(3):
                    TrainingLesson.objects.create(
                        course=course, title=f'{title} - Module {i+1}',
                        content=f'Lesson content...', order=i+1, duration_minutes=duration//3,
                        created_by=admin, updated_by=admin
                    )
                self.stdout.write(f'  Created course: {title}')

        # ===== MAINTENANCE DATA =====
        self.stdout.write('\nSeeding Maintenance data...')

        # Asset Categories
        asset_cats = []
        for name in ['CNC Machine', 'Grinding Machine', 'Inspection Equipment']:
            ac, created = AssetCategory.objects.get_or_create(
                name=name, defaults={'description': f'{name} category', 'created_by': admin, 'updated_by': admin}
            )
            asset_cats.append(ac)
            if created:
                self.stdout.write(f'  Created asset category: {name}')

        # Maintenance Locations
        maint_locs = []
        for name in ['Shop Floor', 'Machine Room', 'Quality Lab']:
            ml, created = MaintenanceLocation.objects.get_or_create(
                name=name, defaults={'description': f'{name} area', 'created_by': admin, 'updated_by': admin}
            )
            maint_locs.append(ml)
            if created:
                self.stdout.write(f'  Created maintenance location: {name}')

        # Assets
        assets = []
        for code, name in [('AST-001', 'CNC Lathe #1'), ('AST-002', 'Vertical Mill #1'), ('AST-003', 'Surface Grinder')]:
            asset, created = Asset.objects.get_or_create(
                asset_code=code,
                defaults={
                    'name': name, 'description': f'{name} machine',
                    'category': asset_cats[0] if asset_cats else None,
                    'location': maint_locs[0] if maint_locs else None,
                    'status': 'OPERATIONAL',
                    'purchase_date': timezone.now().date() - timedelta(days=730),
                    'created_by': admin, 'updated_by': admin
                }
            )
            assets.append(asset)
            if created:
                self.stdout.write(f'  Created asset: {name}')

        # Work Orders
        for i in range(3):
            wo_no = f'WO-2024-{str(i+1).zfill(4)}'
            wo, created = WorkOrder.objects.get_or_create(
                work_order_number=wo_no,
                defaults={
                    'asset': assets[i % len(assets)] if assets else None,
                    'description': f'Maintenance task {i+1}',
                    'priority': random.choice(['LOW', 'MEDIUM', 'HIGH']),
                    'status': random.choice(['OPEN', 'IN_PROGRESS']),
                    'assigned_to': users[i % len(users)] if users else admin,
                    'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created work order: {wo_no}')

        # ===== QUALITY DATA =====
        self.stdout.write('\nSeeding Quality data...')

        # Acceptance Criteria
        for name, min_v, max_v, unit in [('Thread Pitch', -0.001, 0.001, 'inches'), ('Surface Finish', 0, 32, 'microinches')]:
            crit, created = AcceptanceCriteriaTemplate.objects.get_or_create(
                name=name,
                defaults={
                    'description': f'{name} requirement', 'measurement_field': name.lower().replace(' ', '_'),
                    'min_value': Decimal(str(min_v)), 'max_value': Decimal(str(max_v)), 'unit': unit,
                    'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created acceptance criteria: {name}')

        # Calibration Equipment
        for code, name in [('CAL-001', 'Thread Gauge Set'), ('CAL-002', 'Micrometer Set')]:
            eq, created = CalibratedEquipment.objects.get_or_create(
                equipment_code=code,
                defaults={
                    'name': name, 'next_calibration_date': '2025-01-15',
                    'calibration_interval_days': 365, 'status': 'CALIBRATED',
                    'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created calibration equipment: {name}')

        # NCRs
        for i in range(2):
            ncr_no = f'NCR-2024-{str(i+1).zfill(4)}'
            ncr, created = NonconformanceReport.objects.get_or_create(
                ncr_number=ncr_no,
                defaults={
                    'description': f'Non-conformance {i+1}',
                    'severity': random.choice(['MINOR', 'MAJOR', 'CRITICAL']),
                    'status': random.choice(['OPEN', 'UNDER_INVESTIGATION']),
                    'reported_by': admin, 'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created NCR: {ncr_no}')

        # ===== PLANNING DATA =====
        self.stdout.write('\nSeeding Planning data...')

        # Resources
        for code, name, hours in [('CNC-LATHE', 'CNC Lathe Capacity', 8), ('CNC-MILL', 'CNC Mill Capacity', 8)]:
            res, created = ResourceCapacity.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'resource_type': 'MACHINE', 'available_hours_per_day': hours,
                    'efficiency_percent': Decimal('85'), 'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created resource: {name}')

        # KPI Definitions
        kpi_defs = []
        for code, name, unit, target in [('OTD', 'On-Time Delivery', '%', 95), ('FPY', 'First Pass Yield', '%', 98)]:
            kpi_def, created = KPIDefinition.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'unit': unit, 'target_value': Decimal(str(target)),
                    'direction': 'HIGHER_BETTER', 'created_by': admin, 'updated_by': admin
                }
            )
            kpi_defs.append(kpi_def)
            if created:
                for j in range(5):
                    KPIValue.objects.create(
                        kpi_definition=kpi_def,
                        value=Decimal(str(target + random.uniform(-5, 5))),
                        recorded_date=timezone.now().date() - timedelta(days=j*7),
                        recorded_by=admin, created_by=admin, updated_by=admin
                    )
                self.stdout.write(f'  Created KPI: {name}')

        # Schedules
        for i in range(2):
            sched_no = f'SCHED-2024-{str(i+1).zfill(3)}'
            sched, created = ProductionSchedule.objects.get_or_create(
                schedule_number=sched_no,
                defaults={
                    'name': f'Week {i+1} Schedule',
                    'start_date': timezone.now().date() + timedelta(days=i*7),
                    'end_date': timezone.now().date() + timedelta(days=(i+1)*7),
                    'status': 'PUBLISHED' if i == 0 else 'DRAFT',
                    'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created schedule: {sched_no}')

        # ===== SALES DATA =====
        self.stdout.write('\nSeeding Sales data...')

        # Customers
        customers = []
        for code, name in [('CUST-001', 'Saudi Aramco'), ('CUST-002', 'ADNOC'), ('CUST-003', 'Kuwait Oil Company')]:
            cust, created = Customer.objects.get_or_create(
                customer_code=code,
                defaults={'name': name, 'description': f'{name} customer', 'is_active': True, 'created_by': admin, 'updated_by': admin}
            )
            customers.append(cust)
            if created:
                self.stdout.write(f'  Created customer: {name}')

        # Opportunities
        for i in range(3):
            opp, created = SalesOpportunity.objects.get_or_create(
                opportunity_name=f'Opportunity {i+1}',
                defaults={
                    'customer': customers[i % len(customers)] if customers else None,
                    'estimated_value': Decimal(str(random.randint(50000, 500000))),
                    'probability_percent': random.randint(20, 90),
                    'status': random.choice(['PROSPECTING', 'QUALIFICATION', 'PROPOSAL']),
                    'expected_close_date': timezone.now().date() + timedelta(days=random.randint(30, 180)),
                    'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created opportunity: Opportunity {i+1}')

        # Orders
        for i in range(2):
            so_no = f'SO-2024-{str(i+1).zfill(4)}'
            so, created = SalesOrder.objects.get_or_create(
                order_number=so_no,
                defaults={
                    'customer': customers[i % len(customers)] if customers else None,
                    'status': random.choice(['DRAFT', 'CONFIRMED']),
                    'total_amount': Decimal(str(random.randint(10000, 100000))),
                    'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created sales order: {so_no}')

        # ===== CORE DATA =====
        self.stdout.write('\nSeeding Core data...')

        # Cost Centers
        for code, name in [('CC-PROD', 'Production'), ('CC-ADMIN', 'Administration'), ('CC-SALES', 'Sales')]:
            cc, created = CostCenter.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': f'{name} cost center', 'is_active': True, 'created_by': admin, 'updated_by': admin}
            )
            if created:
                self.stdout.write(f'  Created cost center: {name}')

        # Currencies
        for code, name, symbol, rate in [('SAR', 'Saudi Riyal', 'SR', '1.0'), ('USD', 'US Dollar', '$', '3.75')]:
            curr, created = Currency.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'symbol': symbol, 'exchange_rate': Decimal(rate),
                    'is_base': code == 'SAR', 'created_by': admin, 'updated_by': admin
                }
            )
            if created:
                self.stdout.write(f'  Created currency: {name}')

        # ===== SUMMARY =====
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('DATA SEEDING COMPLETED SUCCESSFULLY!'))
        self.stdout.write('='*50)
        self.stdout.write(f'\nLogin credentials:')
        self.stdout.write(f'  Admin: admin / admin123')
        self.stdout.write(f'  Users: john, jane, mike / password123')
        self.stdout.write(f'\nData summary:')
        self.stdout.write(f'  - {User.objects.count()} users')
        self.stdout.write(f'  - {Department.objects.count()} departments')
        self.stdout.write(f'  - {HREmployee.objects.count()} employees')
        self.stdout.write(f'  - {Item.objects.count()} inventory items')
        self.stdout.write(f'  - {SerialUnit.objects.count()} serial units')
        self.stdout.write(f'  - {JobCard.objects.count()} job cards')
        self.stdout.write(f'  - {EvaluationSession.objects.count()} evaluation sessions')
        self.stdout.write(f'  - {Article.objects.count()} knowledge articles')
        self.stdout.write(f'  - {BusinessInstruction.objects.count()} business instructions')
        self.stdout.write(f'  - {TrainingCourse.objects.count()} training courses')
        self.stdout.write(f'  - {Asset.objects.count()} maintenance assets')
        self.stdout.write(f'  - {Customer.objects.count()} customers')
        self.stdout.write(f'  - {KPIDefinition.objects.count()} KPI definitions')
