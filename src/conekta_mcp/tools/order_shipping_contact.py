from typing_extensions import NotRequired, TypedDict


class OrderShippingContactAddress(TypedDict):
    street1: str
    postal_code: str
    city: str
    state: str
    country: str
    street2: NotRequired[str]
    residential: NotRequired[bool]


class OrderShippingContact(TypedDict):
    address: OrderShippingContactAddress
    phone: NotRequired[str]
    receiver: NotRequired[str]
    between_streets: NotRequired[str]
