"""Find one order in the shop's historical records."""
from datetime import datetime

import httpx

ORDERS_API_URL = "http://4.186.26.27:8787/ecommerce?dataset=orders"
ORDER_STATUSES = ("approved", "canceled", "created", "delivered",
                  "invoiced", "processing", "shipped", "unavailable")


def readable_date(value):
    """Turn a stored timestamp into a date; missing dates stay missing."""
    if value is None:
        return None
    return datetime.fromisoformat(value).date().isoformat()


def get_order_status(order_id):
    response = httpx.get(ORDERS_API_URL, timeout=30.0)
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Expected a list of order records")

    matches = []
    for row in rows:
        if row.get("order_id") == order_id:
            matches.append(row)
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError("More than one record has this order number")

    row = matches[0]
    if row["order_status"] not in ORDER_STATUSES:
        raise ValueError("Unknown order status")
    # Return only the details needed for support, not the full customer record.
    return {
        "order_id": row["order_id"],
        "status": row["order_status"],
        "expected_delivery": readable_date(row["order_estimated_delivery_date"]),
        "delivered_on": readable_date(row["order_delivered_customer_date"]),
    }
