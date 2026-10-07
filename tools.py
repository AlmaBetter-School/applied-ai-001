"""Look up an order in the workshop's hosted dataset."""
import re
from datetime import datetime

import httpx
from pydantic import ValidationError

from models import Order

ORDERS_API_URL = "http://4.186.26.27:8787/ecommerce?dataset=orders"


class OrdersUnavailable(Exception):
    """The API could not supply trustworthy order information."""


def get_order_status(order_id: str) -> Order | None:
    if not re.fullmatch(r"[0-9a-f]{32}", order_id):
        raise ValueError("Invalid order ID")
    try:
        response = httpx.get(ORDERS_API_URL, timeout=30.0)
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("Expected a list of orders")
        matches = [row for row in rows if row.get("order_id") == order_id]
        if not matches:
            return None
        if len(matches) != 1:
            raise ValueError("Duplicate order IDs")
        row = matches[0]
        expected = row["order_estimated_delivery_date"]
        delivered = row["order_delivered_customer_date"]
        delivered_date = datetime.fromisoformat(delivered) if delivered else None
        return Order(
            order_id=row["order_id"], status=row["order_status"],
            expected_delivery=datetime.fromisoformat(expected).date() if expected else None,
            latest_update=(f"Recorded delivery: {delivered_date.isoformat(sep=' ')}."
                           if delivered_date else "No customer delivery timestamp recorded."),
        )
    except (httpx.HTTPError, ValidationError, ValueError, KeyError, TypeError) as exc:
        raise OrdersUnavailable() from exc
