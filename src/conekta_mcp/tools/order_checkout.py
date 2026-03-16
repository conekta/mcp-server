import json as _json
from typing import Literal, TypeAlias
from typing_extensions import NotRequired, TypedDict

CHECKOUT_TYPE_INTEGRATION = "Integration"
CHECKOUT_TYPE_HOSTED_PAYMENT = "HostedPayment"
INVALID_CHECKOUT_CONFIG_ERROR = (
    '{{"error": true, "message": "Invalid checkout configuration: {}"}}'
)
INVALID_JSON_ERROR = '{{"error": true, "message": "Invalid JSON in {}"}}'
HOSTED_PAYMENT_ONLY_FIELDS = {
    "failure_url",
    "redirection_time",
    "success_url",
}


class BaseCheckout(TypedDict):
    allowed_payment_methods: list[str]
    type: str
    name: str
    exclude_card_networks: NotRequired[list[str]]
    plan_ids: NotRequired[list[str]]
    expires_at: NotRequired[int]
    monthly_installments_enabled: NotRequired[bool]
    monthly_installments_options: NotRequired[list[int]]
    max_failed_retries: NotRequired[int]


class IntegrationCheckout(BaseCheckout):
    type: Literal["Integration"]


class HostedPaymentCheckout(BaseCheckout):
    type: Literal["HostedPayment"]
    failure_url: NotRequired[str]
    redirection_time: NotRequired[int]
    success_url: NotRequired[str]


OrderCheckout: TypeAlias = IntegrationCheckout | HostedPaymentCheckout


def checkout_config_error(message: str) -> str:
    return INVALID_CHECKOUT_CONFIG_ERROR.format(message)


def invalid_json_error(field: str) -> str:
    return INVALID_JSON_ERROR.format(field)


def parse_json_field(field: str, value: str) -> tuple[object | None, str | None]:
    try:
        return _json.loads(value), None
    except _json.JSONDecodeError:
        return None, invalid_json_error(field)


def validate_checkout(checkout: object) -> tuple[OrderCheckout | None, str | None]:
    if not isinstance(checkout, dict):
        return None, checkout_config_error("checkout must be a JSON object")

    checkout_type = checkout.get("type")
    if checkout_type not in {CHECKOUT_TYPE_INTEGRATION, CHECKOUT_TYPE_HOSTED_PAYMENT}:
        return None, checkout_config_error(
            "checkout.type must be Integration or HostedPayment"
        )

    if checkout_type == CHECKOUT_TYPE_INTEGRATION:
        invalid_fields = sorted(HOSTED_PAYMENT_ONLY_FIELDS.intersection(checkout))
        if invalid_fields:
            return None, checkout_config_error(
                f"{', '.join(invalid_fields)} only applies to HostedPayment"
            )

    return checkout, None
