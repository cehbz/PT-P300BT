import pytest
from PIL import ImageFont

from printlabel import (
    set_args,
    fit_font_size,
    pick_uniform_font_size,
    calculate_multiline_dimensions,
    render_label,
)
from tests.conftest import FONT

PRINTABLE_HEIGHT = 64


class _DummyParser:
    def __init__(self):
        self.errors = []

    def error(self, msg):
        self.errors.append(msg)
        raise SystemExit(msg)


def _per_label_size(text, max_width_mm, base_spacing=1.2):
    text_lines = (text.replace("\\n", "\n").split('\n')
                  if '\\n' in text else [text])
    size, _ = fit_font_size(
        FONT, text_lines,
        max_width_px=int(max_width_mm / 0.149),
        base_line_spacing=base_spacing,
    )
    return size


def test_pick_uniform_picks_min_across_labels():
    labels = ["A", "Mag\\nWideText"]
    size, _ = pick_uniform_font_size(FONT, labels, max_width_mm=50)
    expected = min(_per_label_size(t, 50) for t in labels)
    assert size == expected


def test_pick_uniform_errors_via_parser_on_unfittable():
    p = _DummyParser()
    with pytest.raises(SystemExit):
        pick_uniform_font_size(FONT, ["A", "X" * 100], max_width_mm=2, p=p)
    assert any("does not fit" in m for m in p.errors)


def test_pick_uniform_raises_valueerror_without_parser():
    with pytest.raises(ValueError):
        pick_uniform_font_size(FONT, ["A", "X" * 100], max_width_mm=2, p=None)


def test_pick_uniform_chosen_size_is_maximal():
    labels = ["AB", "CD", "EFGH"]
    max_w = 50
    size, spacing = pick_uniform_font_size(FONT, labels, max_width_mm=max_w)
    max_w_px = int(max_w / 0.149)
    at_next = []
    for text in labels:
        font = ImageFont.truetype(FONT, size + 1, encoding="utf-8")
        w, h, _ = calculate_multiline_dimensions([text], font, spacing)
        at_next.append((w, h))
    assert any(w > max_w_px or h > PRINTABLE_HEIGHT for w, h in at_next)


def test_pick_uniform_all_labels_fit_at_chosen():
    labels = ["AB", "CD", "EFGHIJ"]
    max_w = 100
    size, spacing = pick_uniform_font_size(FONT, labels, max_width_mm=max_w)
    max_w_px = int(max_w / 0.149)
    for text in labels:
        font = ImageFont.truetype(FONT, size, encoding="utf-8")
        w, h, _ = calculate_multiline_dimensions([text], font, spacing)
        assert w <= max_w_px
        assert h <= PRINTABLE_HEIGHT


def _make_args(**overrides):
    """Build args via the real parser so defaults stay in sync with set_args()."""
    p = set_args()
    args = p.parse_args(["dummy_comport", FONT])
    for k, v in overrides.items():
        setattr(args, k, v)
    return args


def test_render_label_with_fixed_font_size_produces_bytes():
    args = _make_args(fixed_font_size=20)
    p = _DummyParser()
    data = render_label(args, "Hello", p)
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_render_label_with_max_width_returns_bytes():
    args = _make_args(max_width=40)
    p = _DummyParser()
    data = render_label(args, "Hello", p)
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_render_label_errors_when_text_doesnt_fit_max_width():
    args = _make_args(max_width=2)
    p = _DummyParser()
    with pytest.raises(SystemExit):
        render_label(args, "X" * 100, p)
    assert any("does not fit" in m for m in p.errors)
