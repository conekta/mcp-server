from importlib import import_module

_INITIALIZED = False
_TOOL_MODULES = (
    "balance",
    "charges",
    "checkouts",
    "companies",
    "customers",
    "events",
    "orders",
    "plans",
    "refunds",
    "subscriptions",
)


def initialize() -> None:
    global _INITIALIZED

    if _INITIALIZED:
        return

    for module_name in _TOOL_MODULES:
        import_module(f"conekta_mcp.tools.{module_name}")

    _INITIALIZED = True
