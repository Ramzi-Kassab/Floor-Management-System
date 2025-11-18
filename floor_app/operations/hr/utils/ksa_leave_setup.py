"""
Saudi Arabia Labor Law - Default Leave Policies Setup
Based on KSA Labor Law regulations
"""
from floor_app.operations.hr.models import LeavePolicy, LeaveType


def create_ksa_leave_policies():
    """
    Create default leave policies compliant with Saudi Arabia Labor Law

    This function sets up all required leave types with their default entitlements
    as per KSA labor regulations.
    """

    policies = [
        # Annual Leave - KSA: 21 days after 1 year, increases to 30 days after 5 years
        {
            'name': 'KSA Annual Leave',
            'code': 'KSA_ANNUAL',
            'leave_type': LeaveType.ANNUAL,
            'description': 'Annual paid leave as per KSA Labor Law. 21 days after first year of service, '
                          'increases to 30 days after 5 years of service.',
            'annual_entitlement_days': 21,
            'max_accumulation_days': 60,
            'carry_forward_days': 10,
            'carry_forward_expiry_months': 12,
            'requires_approval': True,
            'min_notice_days': 30,
            'max_consecutive_days': 21,
            'is_paid': True,
            'affects_salary': False,
            'is_active': True,
        },

        # Sick Leave - KSA: 30 days full pay, 60 days 75% pay, 30 days unpaid
        {
            'name': 'KSA Sick Leave',
            'code': 'KSA_SICK',
            'leave_type': LeaveType.SICK,
            'description': 'Sick leave as per KSA Labor Law. First 30 days at full pay, '
                          'next 60 days at 75% pay, following 30 days unpaid. '
                          'Medical certificate required for absences > 2 days.',
            'annual_entitlement_days': 120,  # Total 120 days (30+60+30)
            'max_accumulation_days': 120,
            'carry_forward_days': 0,  # Sick leave doesn't carry forward
            'requires_approval': False,  # Can take without prior approval but needs medical cert
            'requires_documentation': True,
            'min_notice_days': 0,
            'max_consecutive_days': 120,
            'is_paid': True,
            'affects_salary': True,  # 75% pay for days 31-90
            'is_active': True,
        },

        # Maternity Leave - KSA: 10 weeks (70 days), 4 weeks must be after delivery
        {
            'name': 'KSA Maternity Leave',
            'code': 'KSA_MATERNITY',
            'leave_type': LeaveType.MATERNITY,
            'description': 'Maternity leave as per KSA Labor Law. 10 weeks (70 days) fully paid. '
                          'Minimum 4 weeks must be taken after delivery. '
                          'Employee can start leave up to 4 weeks before expected delivery date.',
            'annual_entitlement_days': 70,  # 10 weeks
            'max_accumulation_days': 70,
            'carry_forward_days': 0,
            'requires_approval': True,
            'requires_documentation': True,  # Medical certificate required
            'min_notice_days': 14,
            'max_consecutive_days': 70,
            'is_paid': True,
            'affects_salary': False,
            'is_active': True,
        },

        # Newborn Care Leave - KSA: 3 days for father
        {
            'name': 'KSA Newborn Care Leave',
            'code': 'KSA_NEWBORN',
            'leave_type': LeaveType.NEWBORN,
            'description': 'Leave for father upon birth of child. 3 days fully paid as per KSA Labor Law. '
                          'Must be taken within 30 days of birth.',
            'annual_entitlement_days': 3,
            'max_accumulation_days': 3,
            'carry_forward_days': 0,
            'requires_approval': True,
            'requires_documentation': True,  # Birth certificate
            'min_notice_days': 1,
            'max_consecutive_days': 3,
            'is_paid': True,
            'affects_salary': False,
            'is_active': True,
        },

        # Bereavement - Spouse/Parent/Child - KSA: 5 days
        {
            'name': 'KSA Bereavement Leave - Close Relative',
            'code': 'KSA_BEREAVEMENT_CLOSE',
            'leave_type': LeaveType.BEREAVEMENT_SPOUSE,
            'description': 'Bereavement leave for death of spouse, parent, or child. '
                          '5 days fully paid as per KSA Labor Law.',
            'annual_entitlement_days': 5,
            'max_accumulation_days': 5,
            'carry_forward_days': 0,
            'requires_approval': False,  # Immediate leave
            'requires_documentation': True,  # Death certificate
            'min_notice_days': 0,
            'max_consecutive_days': 5,
            'is_paid': True,
            'affects_salary': False,
            'is_active': True,
        },

        # Bereavement - Sibling/Grandparent - KSA: 3 days
        {
            'name': 'KSA Bereavement Leave - Extended Family',
            'code': 'KSA_BEREAVEMENT_EXTENDED',
            'leave_type': LeaveType.BEREAVEMENT_SIBLING,
            'description': 'Bereavement leave for death of sibling or grandparent. '
                          '3 days fully paid as per KSA Labor Law.',
            'annual_entitlement_days': 3,
            'max_accumulation_days': 3,
            'carry_forward_days': 0,
            'requires_approval': False,
            'requires_documentation': True,
            'min_notice_days': 0,
            'max_consecutive_days': 3,
            'is_paid': True,
            'affects_salary': False,
            'is_active': True,
        },

        # Hajj Leave - KSA: Once during employment, typically unpaid unless using annual leave
        {
            'name': 'KSA Hajj Pilgrimage Leave',
            'code': 'KSA_HAJJ',
            'leave_type': LeaveType.HAJJ,
            'description': 'Hajj pilgrimage leave as per KSA Labor Law. '
                          'Granted once during employment period. Duration typically 2-3 weeks. '
                          'Can be paid if employee uses annual leave entitlement, otherwise unpaid. '
                          'Subject to manager approval and work requirements.',
            'annual_entitlement_days': 0,  # One-time, not annual
            'max_accumulation_days': 0,
            'carry_forward_days': 0,
            'requires_approval': True,
            'requires_documentation': True,  # Hajj visa/permit
            'min_notice_days': 90,  # 3 months advance notice
            'max_consecutive_days': 21,  # Typically 2-3 weeks
            'is_paid': False,  # Unpaid unless using annual leave
            'affects_salary': True,
            'is_active': True,
        },

        # Omra Leave - KSA: Unpaid, subject to approval
        {
            'name': 'KSA Omra Pilgrimage Leave',
            'code': 'KSA_OMRA',
            'leave_type': LeaveType.OMRA,
            'description': 'Omra (Umrah) pilgrimage leave. Unpaid leave subject to manager approval '
                          'and business requirements. Typically 7-10 days. '
                          'Can be paid if employee uses annual leave entitlement.',
            'annual_entitlement_days': 0,
            'max_accumulation_days': 0,
            'carry_forward_days': 0,
            'requires_approval': True,
            'requires_documentation': False,
            'min_notice_days': 30,
            'max_consecutive_days': 10,
            'is_paid': False,
            'affects_salary': True,
            'is_active': True,
        },

        # Exit/Re-entry Leave - KSA: Tied to visa regulations
        {
            'name': 'KSA Exit/Re-entry Visa Leave',
            'code': 'KSA_EXIT_REENTRY',
            'leave_type': LeaveType.EXIT_REENTRY,
            'description': 'Exit/Re-entry visa leave for expatriate employees. '
                          'Allows employee to travel outside Saudi Arabia and return. '
                          'Duration and payment terms subject to company policy and visa regulations. '
                          'Typically used in combination with annual leave.',
            'annual_entitlement_days': 0,  # Depends on visa and company policy
            'max_accumulation_days': 0,
            'carry_forward_days': 0,
            'requires_approval': True,
            'requires_documentation': True,  # Visa copy required
            'min_notice_days': 14,
            'max_consecutive_days': 60,  # Typically 1-2 months
            'is_paid': False,  # Usually unpaid unless combined with annual leave
            'affects_salary': True,
            'is_active': True,
        },

        # Unpaid Leave - KSA: Employer discretion, typically max 20-30 days/year
        {
            'name': 'KSA Unpaid Leave',
            'code': 'KSA_UNPAID',
            'leave_type': LeaveType.UNPAID,
            'description': 'Unpaid leave at employer discretion as per KSA Labor Law. '
                          'Maximum duration typically 20-30 days per year. '
                          'Subject to manager approval and business requirements. '
                          'Does not affect service period calculation.',
            'annual_entitlement_days': 0,  # No automatic entitlement
            'max_accumulation_days': 0,
            'carry_forward_days': 0,
            'requires_approval': True,
            'requires_documentation': False,
            'min_notice_days': 30,
            'max_consecutive_days': 30,
            'is_paid': False,
            'affects_salary': True,
            'is_active': True,
        },

        # Marriage Leave - KSA: 3-5 days paid (common practice)
        {
            'name': 'KSA Marriage Leave',
            'code': 'KSA_MARRIAGE',
            'leave_type': LeaveType.MARRIAGE,
            'description': 'Marriage leave as per company policy (KSA common practice). '
                          '5 days fully paid. Granted once per employment. '
                          'Marriage certificate required.',
            'annual_entitlement_days': 5,
            'max_accumulation_days': 5,
            'carry_forward_days': 0,
            'requires_approval': True,
            'requires_documentation': True,  # Marriage certificate
            'min_notice_days': 14,
            'max_consecutive_days': 5,
            'is_paid': True,
            'affects_salary': False,
            'is_active': True,
        },

        # Compensatory Leave - From weekend overtime work
        {
            'name': 'Compensatory Time Off',
            'code': 'KSA_COMP_OFF',
            'leave_type': LeaveType.COMPENSATORY,
            'description': 'Compensatory time off earned from weekend (Friday) work. '
                          'As per KSA Labor Law, weekend work requires compensatory day off '
                          'in addition to overtime pay. Accumulated comp time must be used within 3 months.',
            'annual_entitlement_days': 0,  # Earned based on weekend work
            'max_accumulation_days': 12,  # Max 12 days accumulation
            'carry_forward_days': 0,
            'requires_approval': True,
            'requires_documentation': False,
            'min_notice_days': 3,
            'max_consecutive_days': 5,
            'is_paid': True,  # Already compensated through overtime
            'affects_salary': False,
            'is_active': True,
        },
    ]

    created_policies = []
    updated_policies = []

    for policy_data in policies:
        code = policy_data['code']

        # Check if policy already exists
        try:
            policy = LeavePolicy.objects.get(code=code)
            # Update existing policy
            for key, value in policy_data.items():
                if key != 'code':  # Don't update the code
                    setattr(policy, key, value)
            policy.save()
            updated_policies.append(policy)
        except LeavePolicy.DoesNotExist:
            # Create new policy
            policy = LeavePolicy.objects.create(**policy_data)
            created_policies.append(policy)

    return {
        'created': len(created_policies),
        'updated': len(updated_policies),
        'total': len(policies),
        'created_policies': created_policies,
        'updated_policies': updated_policies,
    }


def get_ksa_leave_policy_summary():
    """
    Return a summary of KSA leave policies for reference
    """
    return {
        'Annual Leave': {
            'entitlement': '21 days (first year), 30 days (after 5 years)',
            'carry_forward': '10 days to next year',
            'advance_notice': '30 days',
            'payment': 'Fully paid',
        },
        'Sick Leave': {
            'entitlement': '120 days total (30 full pay + 60 at 75% pay + 30 unpaid)',
            'documentation': 'Medical certificate required for > 2 days',
            'payment': 'First 30 days: 100%, Next 60 days: 75%, Final 30 days: 0%',
        },
        'Maternity Leave': {
            'entitlement': '10 weeks (70 days)',
            'rules': 'Minimum 4 weeks after delivery',
            'payment': 'Fully paid',
        },
        'Newborn Care': {
            'entitlement': '3 days for father',
            'timing': 'Within 30 days of birth',
            'payment': 'Fully paid',
        },
        'Bereavement': {
            'spouse/parent/child': '5 days paid',
            'sibling/grandparent': '3 days paid',
            'payment': 'Fully paid',
        },
        'Hajj': {
            'entitlement': 'Once during employment',
            'duration': 'Typically 2-3 weeks',
            'payment': 'Unpaid (unless using annual leave)',
            'advance_notice': '90 days',
        },
        'Omra': {
            'entitlement': 'Subject to approval',
            'duration': '7-10 days typically',
            'payment': 'Unpaid (unless using annual leave)',
        },
        'Exit/Re-entry': {
            'entitlement': 'For expatriates, subject to visa regulations',
            'payment': 'Usually unpaid (can combine with annual leave)',
        },
        'Unpaid Leave': {
            'max_duration': '20-30 days per year',
            'approval': 'Manager discretion',
        },
        'Marriage': {
            'entitlement': '5 days (once per employment)',
            'payment': 'Fully paid',
        },
        'Compensatory Off': {
            'source': 'Earned from weekend (Friday) work',
            'accumulation': 'Max 12 days',
            'validity': 'Use within 3 months',
        },
    }
