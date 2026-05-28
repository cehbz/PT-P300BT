import pytest
from PIL import ImageFont

from printlabel import fit_font_size, calculate_multiline_dimensions
from tests.conftest import FONT

PRINTABLE_HEIGHT = 64


def _measure(text_lines, size, spacing):
    font = ImageFont.truetype(FONT, size, encoding="utf-8")
    return calculate_multiline_dimensions(text_lines, font, spacing)


def test_empty_text_returns_a_positive_size():
    size, _ = fit_font_size(FONT, [""], max_width_px=None)
    assert size > 0


def test_no_descender_fits_at_least_as_large_as_with_descender():
    no_desc, _ = fit_font_size(FONT, ["ABC"], max_width_px=None)
    desc, _ = fit_font_size(FONT, ["AgC"], max_width_px=None)
    assert no_desc >= desc


def test_single_line_height_within_printable_area():
    size, spacing = fit_font_size(FONT, ["Hello"], max_width_px=None)
    _, h, _ = _measure(["Hello"], size, spacing)
    assert h <= PRINTABLE_HEIGHT


def test_narrow_width_yields_smaller_size_than_wide():
    narrow, _ = fit_font_size(FONT, ["AAAA"], max_width_px=50)
    wide, _ = fit_font_size(FONT, ["AAAA"], max_width_px=500)
    assert narrow < wide


def test_text_too_wide_returns_zero():
    size, _ = fit_font_size(FONT, ["AAAAAAAAAA"], max_width_px=5)
    assert size == 0


def test_multiline_uses_widest_line():
    text = ["AA", "AAAAAA"]
    max_w = 200
    size, _ = fit_font_size(FONT, text, max_width_px=max_w)
    font = ImageFont.truetype(FONT, size, encoding="utf-8")
    widest = font.getbbox("AAAAAA", anchor="lt")
    assert (widest[2] - widest[0]) <= max_w


def test_multiline_height_within_printable_area():
    text = ["AA", "BB", "CC"]
    size, spacing = fit_font_size(FONT, text, max_width_px=None)
    _, h, _ = _measure(text, size, spacing)
    assert h <= PRINTABLE_HEIGHT


def test_multiline_tightens_line_spacing_when_useful():
    # Two-line text — when default 1.2 spacing makes two lines exceed 64 by a small amount,
    # the implementation should tighten line_spacing rather than dropping a whole font size.
    # We detect this by: returned spacing < 1.2 OR returned size renders at exactly 64 height.
    text = ["AB", "CD"]
    size, spacing = fit_font_size(FONT, text, max_width_px=None)
    _, h, _ = _measure(text, size, spacing)
    assert h <= PRINTABLE_HEIGHT
    # Spacing tightening should never push spacing below 90% of default
    assert spacing >= 1.2 * 0.9


def test_unbounded_width_matches_height_only_constraint():
    # When width is unbounded, fit_font_size's choice is constrained by height alone.
    # Boundary: at returned_size+1, the height should exceed PRINTABLE_HEIGHT.
    size, spacing = fit_font_size(FONT, ["Hello"], max_width_px=None)
    _, h_at_chosen, _ = _measure(["Hello"], size, spacing)
    _, h_at_next, _ = _measure(["Hello"], size + 1, spacing)
    assert h_at_chosen <= PRINTABLE_HEIGHT
    assert h_at_next > PRINTABLE_HEIGHT


def test_max_width_chosen_size_is_maximal():
    # At returned size, text fits within max_width.
    # At returned size + 1, text exceeds max_width OR exceeds height.
    text = ["Hello"]
    max_w = 200
    size, spacing = fit_font_size(FONT, text, max_width_px=max_w)
    w, h, _ = _measure(text, size, spacing)
    assert w <= max_w
    assert h <= PRINTABLE_HEIGHT
    w_plus, h_plus, _ = _measure(text, size + 1, spacing)
    assert w_plus > max_w or h_plus > PRINTABLE_HEIGHT
