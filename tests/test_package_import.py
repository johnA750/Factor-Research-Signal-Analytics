from __future__ import annotations


def test_package_imports_from_src_layout() -> None:
    import equity_signal_platform

    assert equity_signal_platform.__version__

