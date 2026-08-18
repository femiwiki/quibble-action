# Tests for resolve_dependencies.py, which turns the dependencies input, a
# manifest's requires clause or a phan config into Gerrit project paths.
#
# The skin half of it had no coverage at all: no job in the suite runs against
# a skin, so `skins/Bar` normalization and the `requires.skins` clause were
# only ever exercised in production.
import json
import os
import subprocess
import sys
import tempfile

RESOLVER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'resolve_dependencies.py'
)


def resolve(argument='', manifest=None, manifest_name='extension.json', phan=None):
    """Return the project paths the resolver prints, as a list.

    Runs in a scratch directory, since the resolver reads the manifest and the
    phan config relative to the working directory.
    """
    with tempfile.TemporaryDirectory() as directory:
        if manifest is not None:
            with open(os.path.join(directory, manifest_name), 'w') as f:
                json.dump(manifest, f)
        if phan is not None:
            os.mkdir(os.path.join(directory, '.phan'))
            with open(os.path.join(directory, '.phan', 'config.php'), 'w') as f:
                f.write(phan)
        output = subprocess.run(
            [sys.executable, RESOLVER, argument],
            capture_output=True,
            check=True,
            cwd=directory,
            text=True,
        ).stdout
    return output.split()


PHAN_CONFIG = """<?php
$cfg['directory_list'] = [
    '../../extensions/Foo',
    '../../skins/Bar',
];
"""

CASES = [
    (
        'a bare name in the input is an extension',
        {'argument': 'Foo'},
        ['mediawiki/extensions/Foo'],
    ),
    (
        'a skins/ prefix in the input is kept as a skin',
        {'argument': 'skins/Bar'},
        ['mediawiki/skins/Bar'],
    ),
    (
        'an already qualified path is left alone',
        {'argument': 'mediawiki/skins/Bar'},
        ['mediawiki/skins/Bar'],
    ),
    (
        'the input accepts whitespace and commas together',
        {'argument': 'Foo, skins/Bar  Baz'},
        ['mediawiki/extensions/Foo', 'mediawiki/skins/Bar', 'mediawiki/extensions/Baz'],
    ),
    (
        'a repeated dependency is listed once',
        {'argument': 'Foo Foo skins/Bar'},
        ['mediawiki/extensions/Foo', 'mediawiki/skins/Bar'],
    ),
    (
        'no dependencies anywhere resolves to nothing',
        {},
        [],
    ),
    (
        'requires.skins of a skin.json resolves to skins',
        {
            'manifest': {'requires': {'skins': {'Bar': '*'}}},
            'manifest_name': 'skin.json',
        },
        ['mediawiki/skins/Bar'],
    ),
    (
        'requires resolves extensions and skins from one manifest',
        {'manifest': {'requires': {'extensions': {'Foo': '*'}, 'skins': {'Bar': '*'}}}},
        ['mediawiki/extensions/Foo', 'mediawiki/skins/Bar'],
    ),
    (
        'a MediaWiki version constraint is not a dependency',
        {'manifest': {'requires': {'MediaWiki': '>= 1.43'}}},
        [],
    ),
    (
        'the input wins over the requires clause',
        {'argument': 'Baz', 'manifest': {'requires': {'skins': {'Bar': '*'}}}},
        ['mediawiki/extensions/Baz'],
    ),
    (
        'the phan config supplies extensions and skins',
        {'phan': PHAN_CONFIG},
        ['mediawiki/extensions/Foo', 'mediawiki/skins/Bar'],
    ),
    (
        'the requires clause wins over the phan config',
        {'manifest': {'requires': {'extensions': {'Qux': '*'}}}, 'phan': PHAN_CONFIG},
        ['mediawiki/extensions/Qux'],
    ),
]


def main():
    failed = 0
    for name, keywords, expected in CASES:
        actual = resolve(**keywords)
        if actual != expected:
            print(f'FAIL: {name}: expected {expected}, got {actual}')
            failed += 1
        else:
            print(f'ok: {name}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
