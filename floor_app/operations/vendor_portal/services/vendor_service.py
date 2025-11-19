"""Vendor Service - Vendor portal business logic"""

from typing import Dict, Any, List
from datetime import date
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from floor_app.operations.vendor_portal.models import Vendor, RFQ, Quotation, PurchaseOrder

User = get_user_model()


class VendorService:
    """Service for vendor management."""

    @classmethod
    def generate_rfq_number(cls) -> str:
        year = timezone.now().year
        prefix = f"RFQ-{year}-"
        last_rfq = RFQ.objects.filter(rfq_number__startswith=prefix).order_by('-rfq_number').first()
        new_number = 1 if not last_rfq else int(last_rfq.rfq_number.split('-')[-1]) + 1
        return f"{prefix}{new_number:04d}"

    @classmethod
    @transaction.atomic
    def create_rfq(cls, requested_by: User, data: Dict[str, Any]) -> RFQ:
        rfq = RFQ.objects.create(
            rfq_number=cls.generate_rfq_number(),
            requested_by=requested_by,
            title=data['title'],
            description=data['description'],
            issue_date=data['issue_date'],
            submission_deadline=data['submission_deadline'],
            required_delivery_date=data.get('required_delivery_date'),
            department=data.get('department', ''),
            project=data.get('project', ''),
            priority=data.get('priority', 'MEDIUM'),
            line_items=data.get('line_items', []),
            payment_terms=data.get('payment_terms', ''),
            delivery_terms=data.get('delivery_terms', ''),
            terms_and_conditions=data.get('terms_and_conditions', ''),
            published_publicly=data.get('published_publicly', False),
            status='DRAFT'
        )
        if 'vendor_ids' in data:
            rfq.invited_vendors.set(Vendor.objects.filter(id__in=data['vendor_ids']))
        return rfq

    @classmethod
    @transaction.atomic
    def publish_rfq(cls, rfq_id: int) -> RFQ:
        rfq = RFQ.objects.get(id=rfq_id)
        rfq.status = 'PUBLISHED'
        rfq.save()
        return rfq

    @classmethod
    @transaction.atomic
    def submit_quotation(cls, rfq_id: int, vendor: Vendor, data: Dict[str, Any]) -> Quotation:
        rfq = RFQ.objects.get(id=rfq_id)

        quotation = Quotation.objects.create(
            quotation_number=f"QT-{rfq.rfq_number}-{vendor.vendor_code}",
            rfq=rfq,
            vendor=vendor,
            submitted_date=timezone.now(),
            line_items=data['line_items'],
            subtotal=data['subtotal'],
            tax_amount=data.get('tax_amount', 0),
            shipping_cost=data.get('shipping_cost', 0),
            total_amount=data['total_amount'],
            currency=data.get('currency', 'USD'),
            payment_terms=data.get('payment_terms', ''),
            delivery_timeframe=data.get('delivery_timeframe', ''),
            warranty=data.get('warranty', ''),
            validity_days=data.get('validity_days', 30),
            status='SUBMITTED'
        )
        return quotation

    @classmethod
    @transaction.atomic
    def award_rfq(cls, rfq_id: int, quotation_id: int, awarded_by: User) -> RFQ:
        rfq = RFQ.objects.get(id=rfq_id)
        quotation = Quotation.objects.get(id=quotation_id)

        rfq.status = 'AWARDED'
        rfq.awarded_vendor = quotation.vendor
        rfq.awarded_quotation = quotation
        rfq.award_date = timezone.now().date()
        rfq.save()

        quotation.status = 'ACCEPTED'
        quotation.save()

        # Reject other quotations
        rfq.quotations.exclude(id=quotation_id).update(status='REJECTED')

        return rfq

    @classmethod
    @transaction.atomic
    def create_po_from_quotation(cls, quotation_id: int) -> PurchaseOrder:
        quotation = Quotation.objects.get(id=quotation_id)

        po = PurchaseOrder.objects.create(
            po_number=f"PO-{quotation.rfq.rfq_number}",
            quotation=quotation,
            vendor=quotation.vendor,
            po_date=timezone.now().date(),
            expected_delivery_date=quotation.rfq.required_delivery_date,
            line_items=quotation.line_items,
            subtotal=quotation.subtotal,
            tax_amount=quotation.tax_amount,
            shipping_cost=quotation.shipping_cost,
            total_amount=quotation.total_amount,
            currency=quotation.currency,
            payment_terms=quotation.payment_terms,
            delivery_terms=quotation.rfq.delivery_terms,
            shipping_address=quotation.rfq.requested_by.profile.address if hasattr(quotation.rfq.requested_by, 'profile') else '',
            billing_address='',
            contact_person=quotation.rfq.requested_by.get_full_name(),
            contact_phone='',
            status='DRAFT'
        )
        return po
