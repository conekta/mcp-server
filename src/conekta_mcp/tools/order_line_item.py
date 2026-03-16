from typing_extensions import TypedDict


class OrderLineItem(TypedDict):
    name: str
    unit_price: int
    quantity: int
