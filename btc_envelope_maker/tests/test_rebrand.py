"""Rebrand contract for the offline generator: bitposta.com replaces the old domains.

Written before the change so it fails on the pre-rebrand tree. Backward
compatibility is deliberately not required: the legacy hosts leave the default
allowlist rather than staying beside the new one.
"""
import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_generator_security import gen  # noqa: E402  (loads the module by path)

BRAND = 'bitposta.com'
PRINTABLE_EMAIL = '09113458375@bitposta.com'
LEGACY = ('btc4.fun', 'btc4.fun', 'bitcoin4.fun', 'b.tc4fun.ir')


def load_config_module():
    path = Path(__file__).resolve().parents[1] / 'btc_envelope_maker.py'
    spec = importlib.util.spec_from_file_location('rebrand_generator', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['rebrand_generator'] = module
    spec.loader.exec_module(module)
    return module


def test_defaults_print_the_new_brand_and_mailbox():
    assert gen.DEFAULTS['brand_name'] == BRAND
    assert PRINTABLE_EMAIL in gen.DEFAULTS['contact']
    assert BRAND in gen.DEFAULTS['contact']
    for legacy in LEGACY:
        assert legacy not in gen.DEFAULTS['brand_name']
        assert legacy not in gen.DEFAULTS['contact']


def test_default_host_allowlist_accepts_only_the_new_hosts():
    assert BRAND in gen.PUBLIC_URL_HOSTS
    assert 'btc.saeb.id.ir' in gen.PUBLIC_URL_HOSTS
    for legacy in ('btc4.fun', 'b.tc4fun.ir'):
        assert legacy not in gen.PUBLIC_URL_HOSTS


def test_config_rejects_a_legacy_host_in_the_site_address_pair(tmp_path):
    module = load_config_module()
    example = Path(__file__).resolve().parents[1] / 'config.example.toml'
    # Insert the pair BEFORE any [table]; a key after a table belongs to it.
    lines = example.read_text().splitlines()
    cut = next(i for i, line in enumerate(lines) if line.lstrip().startswith('['))
    head = [line for line in lines[:cut]
            if not line.startswith(('site_key', 'site_url'))]
    tail = lines[cut:]
    for key, url, allowed in (('bitposta.com', 'https://b.tc4fun.ir/', False),
                              ('bitposta.com', 'https://btc4.fun/', False),
                              ('bitposta.com', 'https://bitposta.com/', True)):
        probe = tmp_path / f"config-{url.split('//')[1].replace('/', '_').replace('.', '-')}.toml"
        probe.write_text('\n'.join(head + [f'site_key = "{key}"', f'site_url = "{url}"'] + tail) + '\n')
        if allowed:
            assert module.load_config(probe)['site_url'] == url
        else:
            with pytest.raises(SystemExit):
                module.load_config(probe)


def test_printed_card_text_uses_the_new_host():
    source = (Path(__file__).resolve().parents[1] / 'btc_envelope_maker.py').read_text()
    assert 'https://bitposta.com' in source
    assert 'https://bitposta.com/s/' in source
    assert 'https://bitposta.com/security' in source
    for legacy in LEGACY:
        assert legacy not in source


def test_example_config_prints_the_new_host_and_mailbox():
    example = (Path(__file__).resolve().parents[1] / 'config.example.toml').read_text()
    assert f'brand_name = "{BRAND}"' in example
    assert PRINTABLE_EMAIL in example
    for legacy in LEGACY:
        assert legacy not in example
