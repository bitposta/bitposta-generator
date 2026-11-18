"""Card-envelope guide and text placement, measured not eyeballed.

The owner's requirements, stated twice now:
  1. Fold (hatch) lines must NOT run edge to edge. Only the corners carry them,
     so a fold line can never be confused with the solid cut border and the
     middle of an edge stays clean.
  2. Inside the card, the serial sits further from the hatch line.
  3. On the paper's top area (the flap with the guidance text), the text is
     centred and kept clear of both hatch lines.
  4. The recovery words are bold.

Written before the change so every assertion below fails on the old geometry.
"""
import math

import pytest

from test_generator_security import gen  # noqa: E402  (loads the module by path)


def guides(monkeypatch):
    """Capture every line draw_leaf_guides strokes, as (x1, y1, x2, y2) in mm."""
    calls = []

    class FakeCanvas:
        def saveState(self): pass
        def restoreState(self): pass
        def setStrokeColor(self, *a): pass
        def setLineWidth(self, *a): pass
        def setDash(self, *a, **k): pass
        def rect(self, *a, **k): calls.append(('rect', a))
        def line(self, x1, y1, x2, y2): calls.append(('line', (x1, y1, x2, y2)))

    import unittest.mock as mock
    monkeypatch.setattr(gen, 'FOLD', gen.FOLD)
    gen.draw_leaf_guides(FakeCanvas(), gen.CARD_LEAF_W * gen.mm, gen.CARD_LEAF_H * gen.mm)
    return [c for c in calls if c[0] == 'line']


def fold_segments(monkeypatch):
    """Only the hatch (fold) lines: the seal-tab line is red and drawn last."""
    calls = []

    class FakeCanvas:
        def __init__(self): self.color = None
        def saveState(self): pass
        def restoreState(self): pass
        def setStrokeColor(self, color): self.color = color
        def setLineWidth(self, *a): pass
        def setDash(self, *a, **k): pass
        def rect(self, *a, **k): pass
        def line(self, x1, y1, x2, y2): calls.append((self.color, (x1, y1, x2, y2)))

    gen.draw_leaf_guides(FakeCanvas(), gen.CARD_LEAF_W * gen.mm, gen.CARD_LEAF_H * gen.mm)
    return [seg for color, seg in calls if color is gen.FOLD]


def test_fold_creases_never_run_edge_to_edge(monkeypatch):
    """A fold line that spans the whole edge reads like the cut border."""
    W = gen.CARD_LEAF_W * gen.mm
    H = gen.CARD_LEAF_H * gen.mm
    folds = fold_segments(monkeypatch)
    assert folds, 'the leaf must still show fold creases'
    for x1, y1, x2, y2 in folds:
        vertical = abs(x1 - x2) < 0.01
        length = abs(y2 - y1) if vertical else abs(x2 - x1)
        full = (H if vertical else W)
        assert length < full * 0.75, (
            'every fold crease must be a corner tick, not a full-length line')
        # and never starting flush against the cut border
        if vertical:
            assert min(y1, y2) >= 2 * gen.mm, 'ticks must clear the cut border'
            assert max(y1, y2) <= H - 2 * gen.mm
        else:
            assert min(x1, x2) >= 2 * gen.mm
            assert max(x1, x2) <= W - 2 * gen.mm


def test_fold_creases_are_symmetric_at_both_ends(monkeypatch):
    """Both ends of a crease carry a tick, so the operator sees the mark either way."""
    folds = fold_segments(monkeypatch)
    verticals = [s for s in folds if abs(s[0] - s[2]) < 0.01]
    horizontals = [s for s in folds if abs(s[1] - s[3]) < 0.01]
    assert len(verticals) == 4, 'two vertical creases x two corner ticks each'
    assert len(horizontals) == 4, 'two horizontal creases x two corner ticks each'
    H = gen.CARD_LEAF_H * gen.mm
    W = gen.CARD_LEAF_W * gen.mm
    # Group the ticks per crease: each crease must have one at each end.
    for x in {round(s[0], 3) for s in verticals}:
        ends = sorted(min(s[1], s[3]) for s in verticals if abs(s[0] - x) < 0.01)
        assert len(ends) == 2, 'each vertical crease needs two ticks'
        assert ends[0] < H * 0.35 and ends[1] > H * 0.65, 'one near the bottom, one near the top'
    for y in {round(s[1], 3) for s in horizontals}:
        ends = sorted(min(s[0], s[2]) for s in horizontals if abs(s[1] - y) < 0.01)
        assert len(ends) == 2, 'each horizontal crease needs two ticks'
        assert ends[0] < W * 0.35 and ends[1] > W * 0.65, 'one near the left, one near the right'


def test_seal_tab_line_is_also_a_corner_mark_not_full_width():
    """The red perforation ran the whole leaf width, which is the same problem.

    It is the only red guide and it still has to read as a mark, not a cut.
    """
    calls = []

    class FakeCanvas:
        def __init__(self): self.color = None
        def saveState(self): pass
        def restoreState(self): pass
        def setStrokeColor(self, color): self.color = color
        def setLineWidth(self, *a): pass
        def setDash(self, *a, **k): pass
        def rect(self, *a, **k): pass
        def line(self, x1, y1, x2, y2): calls.append((self.color, (x1, y1, x2, y2)))

    gen.draw_leaf_guides(FakeCanvas(), gen.CARD_LEAF_W * gen.mm, gen.CARD_LEAF_H * gen.mm)
    red = [seg for color, seg in calls if color is gen.RED]
    assert red, 'the seal-tab boundary must still be marked'
    W = gen.CARD_LEAF_W * gen.mm
    for x1, y1, x2, y2 in red:
        assert abs(x2 - x1) < W * 0.75, 'the seal-tab line must be a corner mark, not full width'


def test_a4_fold_instructions_are_centred_on_the_sheet():
    """The Method-3 guidance block must sit on the sheet's centre axis.

    It was laid out from x=58 mm with width 94 mm, which centres at 105 mm only
    by coincidence of those two numbers; assert the CENTRE, so a later width
    tweak cannot silently push it off axis.
    """
    calls = []
    import unittest.mock as mock
    with mock.patch.object(gen, 'draw_block', lambda c, t, x, top, w, h, *a, **k: calls.append((x, w, k)) or top), \
         mock.patch.object(gen, 'draw_private', lambda *a, **k: None), \
         mock.patch.object(gen, 'watermark', lambda *a, **k: None), \
         mock.patch.object(gen, 'put', lambda *a, **k: None):
        gen.draw_regency_inside(mock.MagicMock(), dict(gen.DEFAULTS, _logo=None),
                                gen.Wallet('0587k45300', gen.TEST_ADDRESS, gen.TEST_MNEMONIC), False)
    guidance = next((c for c in calls if c[2].get('align') == 'center' and abs(c[1] / gen.mm - 94) < 0.01), None)
    assert guidance is not None, 'the Method-3 guidance block must still be drawn'
    centre_mm = (guidance[0] + guidance[1] / 2) / gen.mm
    assert abs(centre_mm - 105.0) < 0.6, f'guidance block centres at {centre_mm:.1f} mm, not 105 mm'
    # and clear of both vertical creases at 52.5 and 157.5 mm
    left_mm = guidance[0] / gen.mm
    right_mm = (guidance[0] + guidance[1]) / gen.mm
    assert left_mm > 52.5 + 3, 'guidance must clear the left crease'
    assert right_mm < 157.5 - 3, 'guidance must clear the right crease'


def test_card_serial_is_pushed_away_from_the_fold_line():
    """The serial must not hug the right crease. Measure it, do not trust the number."""
    cfg = dict(gen.DEFAULTS, _logo=None)
    gen.register_fonts(cfg)
    rec = gen.Wallet('0587k45300', gen.TEST_ADDRESS, gen.TEST_MNEMONIC)
    calls = []
    import unittest.mock as mock
    with mock.patch.object(gen, 'put', lambda *a, **k: calls.append((a, k))), \
         mock.patch.object(gen, 'draw_qr', lambda *a, **k: None), \
         mock.patch.object(gen, 'draw_block', lambda *a, **k: a[3]), \
         mock.patch.object(gen, 'text_width', lambda *a, **k: 1.0), \
         mock.patch.object(gen, 'fit_size', lambda s, f, w, size, minimum=4.0: size), \
         mock.patch.object(gen, 'shape', lambda s: s):
        gen.draw_card_secret(mock.MagicMock(), cfg, rec, gen.CARD_ENV_W * gen.mm, gen.CARD_ENV_H * gen.mm)
    serial = next((c for c in calls if c[0][1] == rec.serial), None)
    assert serial is not None, 'the serial must still be printed'
    args, kwargs = serial
    x = args[2]
    right_crease = (gen.CARD_PANEL_X + gen.CARD_ENV_W) * gen.mm
    clearance_mm = (right_crease - x) / gen.mm
    # It used to sit 3 mm from the panel edge; require a visibly larger inset.
    assert clearance_mm >= 5.5, f'serial is only {clearance_mm:.1f} mm from the fold line'
    assert kwargs.get('align') in ('right', 'center')


def k_align(serial_call):
    args, kwargs = serial_call if isinstance(serial_call, tuple) else (serial_call, {})
    return kwargs.get('align', 'left')


def test_recovery_words_are_bold_on_both_layouts():
    """Bold must be requested for the printed words, not only the numbering."""
    source = (__import__('pathlib').Path(__file__).resolve().parents[1] / 'btc_envelope_maker.py').read_text()
    card = source.split('def draw_card_secret', 1)[1].split('def draw_leaf_guides', 1)[0]
    body = card.split('for i, word in enumerate', 1)[1]
    word_line = next(line for line in body.splitlines() if 'put(c, word' in line)
    assert 'bold=True' in word_line, 'card-envelope recovery words must be bold'
    private = source.split('def draw_private', 1)[1].split('def place_card', 1)[0]
    priv_body = private.split('for i, word in enumerate', 1)[1]
    priv_word = next(line for line in priv_lines(priv_body) if 'put(c, word' in line)
    assert 'bold=True' in priv_word, 'paper recovery words must be bold'


def priv_lines(body):
    return [line for line in body.splitlines() if 'put(c, word' in line]
