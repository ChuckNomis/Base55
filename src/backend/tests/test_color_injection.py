import pytest
from src.backend.server import inject_colors

def test_inject_colors_prepends_style_block_after_head():
    html = "<!DOCTYPE html><html><head><title>x</title></head><body></body></html>"
    out = inject_colors(html, "#FF6B00", "#1A1A1A", "#0F0F0F")
    expected = "<head><style>:root{--primary-color:#FF6B00;--accent-color:#1A1A1A;--bg-color:#0F0F0F;}</style>"
    assert expected in out

def test_inject_colors_only_replaces_first_head():
    html = "<head><head>"  # pathological double-head
    out = inject_colors(html, "#111111", "#222222", "#333333")
    # Only the first <head> should get the style block
    assert out.count("<style>:root{") == 1

def test_inject_colors_preserves_rest_of_html():
    html = "<html><head></head><body><h1>Hi</h1></body></html>"
    out = inject_colors(html, "#aaa", "#bbb", "#ccc")
    assert "<body><h1>Hi</h1></body></html>" in out
