from conekta_mcp import tools


def test_initialize_imports_all_tool_modules_once(monkeypatch):
    imported_modules = []

    def fake_import_module(module_name):
        imported_modules.append(module_name)
        return object()

    monkeypatch.setattr(tools, "import_module", fake_import_module)
    monkeypatch.setattr(tools, "_INITIALIZED", False)

    tools.initialize()
    tools.initialize()

    assert imported_modules == [
        f"conekta_mcp.tools.{module_name}" for module_name in tools._TOOL_MODULES
    ]
