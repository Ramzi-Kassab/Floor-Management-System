"""
Document Numbering Service

Centralized service for generating sequential document numbers.
"""

from django.utils import timezone
from floor_app.operations.purchasing.models import (
    PurchaseRequisition,
    RequestForQuotation,
    PurchaseOrder,
    GoodsReceiptNote,
    PurchaseReturn,
    SupplierInvoice,
    InternalTransferOrder,
    OutboundShipment,
    CustomerReturn,
)


class DocumentNumberingService:
    """
    Service for generating sequential document numbers across purchasing module.
    """

    @staticmethod
    def get_next_pr_number():
        """Generate next Purchase Requisition number"""
        return PurchaseRequisition.generate_pr_number()

    @staticmethod
    def get_next_rfq_number():
        """Generate next RFQ number"""
        return RequestForQuotation.generate_rfq_number()

    @staticmethod
    def get_next_po_number():
        """Generate next Purchase Order number"""
        return PurchaseOrder.generate_po_number()

    @staticmethod
    def get_next_grn_number():
        """Generate next Goods Receipt Note number"""
        return GoodsReceiptNote.generate_grn_number()

    @staticmethod
    def get_next_return_number():
        """Generate next Purchase Return number"""
        return PurchaseReturn.generate_return_number()

    @staticmethod
    def get_next_invoice_reference():
        """Generate next internal invoice reference"""
        return SupplierInvoice.generate_internal_reference()

    @staticmethod
    def get_next_transfer_number():
        """Generate next Transfer Order number"""
        return InternalTransferOrder.generate_transfer_number()

    @staticmethod
    def get_next_shipment_number():
        """Generate next Shipment number"""
        return OutboundShipment.generate_shipment_number()

    @staticmethod
    def get_next_customer_return_number():
        """Generate next Customer Return number"""
        return CustomerReturn.generate_return_number()
