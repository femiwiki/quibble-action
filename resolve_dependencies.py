# A script to resolve dependencies of a MediaWiki extension/skin for Quibble.
#
# Dependencies are resolved from the first source that yields anything, in this
# priority order:
#
#   1. The `dependencies` action input (passed as the first CLI argument).
#   2. The `requires` clause of extension.json / skin.json.
#   3. The phan configuration (.phan/config.php).
#
# Each resolved dependency is printed as a Gerrit project path, one per line:
#
#   mediawiki/extensions/Foo
#   mediawiki/skins/Bar
import json
import os
import re
import sys


def normalize(name, kind='extensions'):
    """Return a Gerrit project path for a single dependency.

    `name` may be a bare extension/skin name (`Foo`), a short prefixed path
    (`skins/Bar`) or an already-qualified Gerrit path (`mediawiki/...`).
    """
    name = name.strip().strip('/')
    if not name:
        return None
    if name.startswith('mediawiki/'):
        return name
    if '/' in name:
        return 'mediawiki/' + name
    return 'mediawiki/{}/{}'.format(kind, name)


def from_input(raw):
    """Dependencies listed explicitly in the `dependencies` action input."""
    deps = []
    for token in re.split(r'[\s,]+', raw or ''):
        dep = normalize(token)
        if dep:
            deps.append(dep)
    return deps


def from_requires():
    """Dependencies declared in the `requires` clause of the manifest."""
    deps = []
    for filename in ('extension.json', 'skin.json'):
        if not os.path.exists(filename):
            continue
        with open(filename, 'r') as f:
            requires = json.load(f).get('requires', {})
        for name in requires.get('extensions', {}):
            deps.append(normalize(name, 'extensions'))
        for name in requires.get('skins', {}):
            deps.append(normalize(name, 'skins'))
    return deps


def from_phan(path='.phan/config.php'):
    """Dependencies inferred from a MediaWiki phan config's directory list."""
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        content = f.read()
    deps = []
    # Match paths such as '../../extensions/Foo' or '../../skins/Bar' that a
    # MediaWiki phan config adds to its directory_list / file_list.
    for kind, name in re.findall(
        r'\.\./\.\./(extensions|skins)/([A-Za-z0-9_./-]+)', content
    ):
        deps.append(normalize(name.split('/')[0], kind))
    return deps


def main():
    raw_input = sys.argv[1] if len(sys.argv) > 1 else ''

    resolved = []
    for source in (from_input(raw_input), from_requires(), from_phan()):
        if source:
            resolved = source
            break

    # Deduplicate while preserving order.
    seen = set()
    unique = []
    for dep in resolved:
        if dep and dep not in seen:
            seen.add(dep)
            unique.append(dep)

    print('\n'.join(unique))


if __name__ == '__main__':
    main()
