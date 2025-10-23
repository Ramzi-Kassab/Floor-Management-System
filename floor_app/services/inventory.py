from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError
# from ..models import StockLedger, InventoryBalance, Item, Warehouse, Location, Batch, Serial


@dataclass(frozen=True)
class StockMove:
    item: "Item"; wh: "Warehouse"; loc: "Location"
    qty_in: Decimal = Decimal('0'); qty_out: Decimal = Decimal('0')
    batch: Optional["Batch"] = None; serial: Optional["Serial"] = None
    voucher_type: str = ''; voucher_id: int = 0; remarks: str = ''

# def post_stock_entry(move: StockMove) -> "StockLedger":
#     ...
