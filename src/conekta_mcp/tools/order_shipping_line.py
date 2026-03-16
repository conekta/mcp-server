from typing_extensions import NotRequired, TypedDict


class OrderShippingLine(TypedDict):
    amount: int
    carrier: NotRequired[str]
    method: NotRequired[str]
    tracking_number: NotRequired[str]
