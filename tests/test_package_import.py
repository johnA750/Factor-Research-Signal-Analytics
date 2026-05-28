from __future__ import annotations


def test_package_imports_from_src_layout() -> None:
    import equity_signal_platform
    from equity_signal_platform.data import download_adjusted_prices

    assert equity_signal_platform.__version__
    assert callable(download_adjusted_prices)
