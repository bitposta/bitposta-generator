"""Print readability contracts, using public recovery vectors only."""
from unittest.mock import Mock

from test_generator_security import gen


def test_card_words_and_back_are_larger_and_bold(monkeypatch):
    cfg = dict(gen.DEFAULTS, _logo=None)
    gen.register_fonts(cfg)
    rec = gen.Wallet('0587k45300', gen.TEST_ADDRESS, gen.TEST_MNEMONIC)
    calls = []
    monkeypatch.setattr(gen, 'put', lambda *args, **kwargs: calls.append((args, kwargs)))
    gen.draw_card_secret(Mock(), cfg, rec, 85.6 * gen.mm, 54 * gen.mm)
    words = [(a, k) for a, k in calls if a[1] in rec.mnemonic.split()]
    assert len(words) == 12
    assert all(a[5] >= 8.5 and k.get('bold') for a, k in words)
    serial = next((a, k) for a, k in calls if a[1] == rec.serial)
    assert serial[0][5] >= 8 and serial[1].get('bold')
    calls.clear()
    gen.draw_regency_card_back(Mock(), rec, 0, False)
    assert calls
    assert all(k.get('bold') for a, k in calls)
    assert next(a[5] for a, k in calls if a[1] == rec.serial) >= 9
    assert next(a[5] for a, k in calls if a[1] == 'https://b.tc4fun.ir') >= 10
