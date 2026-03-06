from conekta_mcp import __main__


def test_build_parser_defaults_stdio(monkeypatch):
    monkeypatch.delenv("CONEKTA_MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)

    args = __main__.build_parser().parse_args([])

    assert args.transport == "stdio"


def test_build_parser_reads_transport_env(monkeypatch):
    monkeypatch.setenv("CONEKTA_MCP_TRANSPORT", "streamable-http")

    args = __main__.build_parser().parse_args([])

    assert args.transport == "streamable-http"


def test_main_runs_selected_transport(monkeypatch):
    call = {}

    def fake_run(*, transport, mount_path=None):
        call["transport"] = transport
        call["mount_path"] = mount_path

    monkeypatch.setattr(__main__.mcp, "run", fake_run)

    __main__.main(["--transport", "streamable-http"])

    assert call == {
        "transport": "streamable-http",
        "mount_path": None,
    }
