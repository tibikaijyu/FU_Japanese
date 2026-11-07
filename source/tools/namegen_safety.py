"""Keep character-name generation data out of localization patches.

A rule array contains candidate strings and nested rule arrays. Its control
object (mode, source, targetLength, titleCase, etc.) is not display text. A
Markov source is a registry ID matching a .namesource's name. Version 0.2.0
incorrectly translated two such source IDs and crashed before the title screen.
Version 0.2.3 also preserves training samples and species name candidates:
these inputs must stay compatible with their generator and input rules.
"""
import json
import re
from pathlib import Path, PurePosixPath


def retired_character_name_assets(project):
    """Return the reviewed legacy paths that need empty overwrite patches."""
    file = Path(project)/'source/retired_character_name_assets.json'
    assets = json.loads(file.read_text(encoding='utf-8'))
    if not isinstance(assets, list) or len(assets) != len(set(assets)):
        raise ValueError('Invalid retired character-name asset list')
    for asset in assets:
        path = PurePosixPath(asset)
        if (path.is_absolute() or '..' in path.parts or '\\' in asset or
                not (asset.endswith('.namesource') or
                     asset.startswith('species/') and asset.endswith('namegen.config'))):
            raise ValueError('Unsafe retired character-name asset: '+asset)
    return assets


def _index(part):
    return part == '-' or re.fullmatch(r'0|[1-9][0-9]*', str(part)) is not None


def is_namegen_scope(asset, parts):
    asset = str(asset).lstrip('/')
    path = PurePosixPath(asset)
    if path.suffix == '.namesource':
        return True
    if path.suffix == '.species' and parts and parts[0] == 'nameGen':
        return True
    if asset == 'celestial/names.config':
        return True
    if path.suffix == '.config' and asset.startswith(('items/', 'species/')):
        return (path.name.lower().endswith('namegen.config') or
                bool(parts) and parts[0] in {'names', 'nameGen'})
    return False


def is_namegen_display_path(asset, parts):
    asset = str(asset).lstrip('/')
    parts = tuple(str(p) for p in parts)
    # Training inputs and character-name candidates are not display prose.
    if PurePosixPath(asset).suffix == '.namesource' or asset.startswith('species/'):
        return False
    if asset == 'celestial/names.config':
        roots = {'systemNames', 'systemSuffixNames'}
    elif PurePosixPath(asset).suffix == '.config' and asset.startswith(('items/', 'species/')):
        roots = {'names', 'nameGen'}
    else:
        return False
    return len(parts) >= 2 and parts[0] in roots and all(_index(p) for p in parts[1:])


def assert_safe_namegen_translation(asset, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise ValueError('Invalid translation pointer: ' + repr(pointer))
    parts = tuple(p.replace('~1', '/').replace('~0', '~') for p in pointer.split('/')[1:])
    if is_namegen_scope(asset, parts) and not is_namegen_display_path(asset, parts):
        raise ValueError('Protected name-generator control: ' + str(asset) + pointer)


def assert_safe_namegen_patch(asset, operations):
    """Check actual mutations independently of the translation catalog.

    An array index can also select a control object. Require a prior exact
    string test in the same batch so only an existing candidate string changes.
    Guards from conditional child batches must never authorize a later write.
    """
    tested_strings = set()
    for entry in operations if isinstance(operations, list) else [operations]:
        if isinstance(entry, list):
            assert_safe_namegen_patch(asset, entry)
            tested_strings.clear()
            continue
        if not isinstance(entry, dict):
            continue
        pointer = entry.get('path', '')
        if entry.get('op') == 'test':
            if isinstance(entry.get('value'), str) and not entry.get('inverse', False):
                tested_strings.add(pointer)
            continue
        parts = tuple(p.replace('~1', '/').replace('~0', '~') for p in pointer.split('/')[1:])
        if is_namegen_scope(asset, parts):
            assert_safe_namegen_translation(asset, pointer)
            if (entry.get('op') != 'replace' or
                    not isinstance(entry.get('value'), str) or
                    pointer not in tested_strings):
                raise ValueError('Name localization requires an exact string test then replace: ' + str(asset) + pointer)
        tested_strings.clear()
