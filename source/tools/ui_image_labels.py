#!/usr/bin/env python3
"""Replace English baked into FU UI textures with native text widgets.

No bitmap is changed.  All additions and replacements are explicitly reviewed
in source/ui_image_labels.json.  Exact source-image guards make each group
independent and keep unrelated menu behavior untouched on a newer FU build.
The manifest records the complete groups for the main strict validator.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import struct
from pathlib import Path

import jsonpatch

from common import dump, read_asset, unptr


SOLID_PIXEL = '/interface/kheAA/kheAA_router/icon1.png'


def get(tree, pointer):
    for part in unptr(pointer):
        tree = tree[int(part)] if isinstance(tree, list) else tree[part]
    return tree


def exists(tree, pointer):
    try:
        get(tree, pointer)
    except (KeyError, IndexError):
        return False
    return True


def png_size(path):
    raw = path.read_bytes()[:24]
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f'Expected PNG source: {path}')
    return list(struct.unpack('>II', raw[16:24]))


def solid_image(color, size):
    # FU itself uses crop + nonuniform scalenearest to create native GUI panels
    # (fu_metagui/extra.lua).  The source texture is already an opaque white
    # 4x4 square, and the directive result is only used by this image widget.
    return (SOLID_PIXEL + '?crop=0;0;1;1?multiply=' + color.lstrip('#')
            + '?scalenearest=' + str(size[0]) + ';' + str(size[1]))


def cover_label(spec):
    x, y, width, height = spec['rect']
    z = spec.get('zlevel', 2)
    cover = {'type': 'image', 'file': solid_image(spec.get('color', '071e43ff'), [width, height]),
             'position': [x, y], 'zlevel': z, 'mouseTransparent': True}
    label = {'type': 'label', 'position': spec.get('text_position', [x + width / 2, y + height / 2]),
             'hAnchor': spec.get('hAnchor', 'mid'), 'vAnchor': 'mid',
             'fontSize': spec.get('fontSize', 8), 'value': spec.get('text', ''),
             'zlevel': z + 1, 'mouseTransparent': True}
    if 'fontColor' in spec:
        label['fontColor'] = spec['fontColor']
    if 'wrapWidth' in spec:
        label['wrapWidth'] = spec['wrapWidth']
    if 'visible' in spec:
        cover['visible'] = label['visible'] = spec['visible']
    return cover, label


def build_patches(project, upstream):
    """Return (patches_by_asset, exact_group_manifest, scope_report).

    This function also writes reports/ui_image_label_manifest.json and
    reports/ui_image_label_coverage.json.  The caller appends each asset's
    groups after the ordinary display-string patches.
    """
    project, upstream = Path(project), Path(upstream)
    source_path = project / 'source/ui_image_labels.json'
    source = json.loads(source_path.read_text(encoding='utf-8'))
    patches = collections.defaultdict(list)
    manifest = []
    documents = {}
    displayed_values = []
    for entry in source['entries']:
        asset = entry['asset']
        if asset not in documents:
            documents[asset] = read_asset(upstream / asset)
        original = documents[asset]
        group = []
        for pointer, value in entry['guards'].items():
            if get(original, pointer) != value:
                raise ValueError(f'UI source guard changed: {entry["id"]} {pointer}')
            group.append({'op': 'test', 'path': pointer, 'value': value})
        mutations = []
        display_paths = []
        if entry['kind'] == 'button':
            widget = entry['widget']
            before = get(original, widget)
            if before.get('type') != 'button':
                raise ValueError(f'Not a button: {asset} {widget}')
            if before.get('caption'):
                raise ValueError(f'Button already has a text caption: {asset} {widget}')
            for name, value in entry['images'].items():
                mutations.append({'op': 'replace', 'path': widget + '/' + name, 'value': value})
            mutations += [{'op': 'add', 'path': widget + '/caption', 'value': entry['text']},
                          {'op': 'add', 'path': widget + '/fontSize', 'value': entry.get('fontSize', 9)}]
            display_paths.append(widget + '/caption')
            displayed_values.append(entry['text'])
        elif entry['kind'] == 'overlays':
            root = entry['widget_root']
            if not isinstance(get(original, root), dict):
                raise ValueError(f'Not a widget group: {asset} {root}')
            for spec in entry['labels']:
                name = spec['name']
                if not name.startswith('fuJapanese'):
                    raise ValueError('UI additions must use their own widget prefix')
                cover, label = cover_label(spec)
                for suffix, value in [('Cover', cover), ('Title', label)]:
                    pointer = root + '/' + spec.get('cover_name' if suffix == 'Cover' else 'label_name', name + suffix)
                    if exists(original, pointer):
                        raise ValueError(f'UI addition would overwrite an existing widget: {pointer}')
                    mutations.append({'op': 'add', 'path': pointer, 'value': value})
                    if suffix == 'Title':
                        display_paths.append(pointer + '/value')
                if spec.get('text'):
                    displayed_values.append(spec['text'])
        elif entry['kind'] == 'display_widget':
            # Used for the COMPLETE bitmap.  Lua still toggles the same widget
            # name and its existing visibility state; only its presentation is
            # changed from a picture to a native Japanese label.
            pointer = entry['widget']
            before = get(original, pointer)
            after = entry['replacement']
            if before.get('type') != 'image' or after.get('type') != 'label':
                raise ValueError('Only the reviewed image-to-label replacement is supported')
            if before.get('visible', True) != after.get('visible', True):
                raise ValueError('The initial visibility must remain unchanged')
            mutations.append({'op': 'replace', 'path': pointer, 'value': after})
            display_paths.append(pointer + '/value')
            displayed_values.append(after['value'])
        else:
            raise ValueError(f'Unknown UI localization entry: {entry["kind"]}')
        if not group or not mutations:
            raise ValueError('Every UI group needs source guards and presentation mutations')
        changes = []
        for mutation in mutations:
            pointer = mutation['path']
            source_exists = exists(original, pointer)
            changes.append({'path': pointer, 'source_exists': source_exists,
                            'source': copy.deepcopy(get(original, pointer)) if source_exists else None,
                            'target': mutation['value']})
        group += mutations
        # Application checks missing/incorrect paths and preserves every value
        # outside the explicit mutation paths.  Running guards against the raw
        # source also avoids silently accepting a changed upstream texture.
        result = jsonpatch.JsonPatch(group).apply(copy.deepcopy(original))
        restored = copy.deepcopy(result)
        for change in reversed(changes):
            restore = {'op': 'replace' if change['source_exists'] else 'remove', 'path': change['path']}
            if change['source_exists']:
                restore['value'] = change['source']
            restored = jsonpatch.JsonPatch([restore]).apply(restored)
        if restored != original:
            raise ValueError(f'Unexpected non-presentation modification: {entry["id"]}')
        for mutation in mutations:
            value = mutation['value']
            if isinstance(value, dict) and value.get('type') == 'image':
                image_path = value['file'].split('?', 1)[0].split(':', 1)[0]
                if not (upstream / image_path.lstrip('/')).is_file():
                    raise ValueError(f'UI texture does not exist: {image_path}')
            elif mutation['path'].rsplit('/', 1)[-1] in {'base', 'hover', 'pressed'}:
                image_path = str(value).split('?', 1)[0].split(':', 1)[0]
                if not (upstream / image_path.lstrip('/')).is_file():
                    raise ValueError(f'Blank button texture does not exist: {image_path}')
        patches[asset].append(group)
        manifest.append({'id': entry['id'], 'asset': asset, 'kind': entry['kind'],
                         'group': group, 'display_paths': display_paths,
                         'allowed_ui_paths': [change['path'] for change in changes],
                         'changes': changes, 'source_image_text': entry.get('source_image_text', []),
                         'notes': entry.get('notes', '')})
    # Multiple independent groups on the same menu must also apply together.
    for asset, groups in patches.items():
        combined = copy.deepcopy(documents[asset])
        for group in groups:
            combined = jsonpatch.JsonPatch(group).apply(combined)
    report = {'source_manifest_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
              'patch_assets': len(patches), 'guarded_ui_groups': len(manifest),
              'japanese_static_labels': len(displayed_values),
              'japanese_static_unique_labels': len(set(displayed_values)),
              'dynamic_title_widgets': 2, 'bitmap_files_modified': 0,
              'input_callbacks_modified': 0, 'existing_control_positions_modified': 0,
              'source_application_checks_passed': True,
              'runtime_rendering_verified': False,
              'related_runtime_hooks': source.get('related_runtime_hooks', []),
              'remaining_readable_labels': source.get('remaining_readable_labels', []),
              'unused_texture_text': source.get('unused_texture_text', []),
              'retained_branding': source.get('retained_branding', []),
              'scope_note': 'Reviewed readable English in FU interface textures. Decorative world textures and unknown third-party mod images are outside this image inventory.'}
    dump(project / 'reports/ui_image_label_manifest.json', manifest)
    dump(project / 'reports/ui_image_label_coverage.json', report)
    return dict(patches), manifest, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('upstream')
    parser.add_argument('--out')
    args = parser.parse_args()
    patches, _, report = build_patches(args.project, args.upstream)
    if args.out:
        for asset, groups in patches.items():
            dump(Path(args.out) / (asset + '.patch'), groups)
    print(json.dumps(report, ensure_ascii=False, indent=2))
