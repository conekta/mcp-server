from typing_extensions import TypedDict


class OrderCharge(TypedDict):
    payment_method: dict[str, object]
