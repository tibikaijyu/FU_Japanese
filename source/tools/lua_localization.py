#!/usr/bin/env python3
"""Localize reviewed Lua string literals without changing executable tokens.

This module deliberately does not translate arbitrary Lua strings. Selection is
stored as an explicit source-offset manifest, pinned to the upstream file hash.
The original source is retained byte-for-byte outside selected literal tokens.
"""
from __future__ import annotations

import argparse
import collections
import ctypes
import ctypes.util
import hashlib
import json
import re
from pathlib import Path

EXCLUDED_DIRS = {'.git', 'a_modders', 'a_notyetadded', 'tests', '_previewimage', 'tilesets'}
EXCLUDED_FILES = {'interface/scripted/sbvn/pandorasboxsbvngui.lua', 'zb/zb_textTyper.lua'}
LONG_OPEN = re.compile(r'\[(=*)\[')
WORD = re.compile(r'[A-Za-z]{2}')
COLOR = re.compile(r'\^[^;\n]*;')
FORMAT = re.compile(r'%(?:\d+\$)?[-+ #0]*\d*(?:\.\d*)?[cdiouxXeEfgGaAqs%](?![A-Za-z])')


def decode_literal(raw):
    if raw.startswith('['):
        m = LONG_OPEN.match(raw)
        value = raw[m.end():-(len(m.group(1)) + 2)]
        if value.startswith('\r\n'):
            value = value[2:]
        elif value.startswith(('\n', '\r')):
            value = value[1:]
        return value.replace('\r\n', '\n').replace('\r', '\n')
    source = raw[1:-1]
    out = []
    i = 0
    escapes = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r',
               't': '\t', 'v': '\v', '\\': '\\', '"': '"', "'": "'"}
    while i < len(source):
        c = source[i]
        if c != '\\':
            out.append(c)
            i += 1
            continue
        i += 1
        c = source[i]
        if c in escapes:
            out.append(escapes[c]); i += 1
        elif c in '\r\n':
            if source[i:i+2] == '\r\n': i += 1
            out.append('\n'); i += 1
        elif c == 'z':
            i += 1
            while i < len(source) and source[i].isspace(): i += 1
        elif c == 'x':
            out.append(chr(int(source[i+1:i+3], 16))); i += 3
        elif c == 'u' and source[i+1] == '{':
            end = source.index('}', i+2)
            out.append(chr(int(source[i+2:end], 16))); i = end + 1
        elif c.isdigit():
            end = i + 1
            while end < min(i+3, len(source)) and source[end].isdigit(): end += 1
            out.append(chr(int(source[i:end], 10))); i = end
        else:
            raise ValueError('Unknown Lua escape: \\' + c)
    return ''.join(out)


def quote_lua(value):
    # JSON's standard escapes are Lua-compatible except \u, which is avoided.
    if any(ord(c) < 32 and c not in '\n\r\t\b\f' for c in value):
        raise ValueError('Unsupported control character in display translation')
    return json.dumps(value, ensure_ascii=False).replace('\\/', '/')


def string_tokens(source):
    """Yield real string literals; comments are excluded, including long ones."""
    i = 0
    line = 1
    while i < len(source):
        start = i
        if source.startswith('--', i):
            opening = LONG_OPEN.match(source, i + 2)
            if opening:
                close = ']' + opening.group(1) + ']'
                end = source.find(close, opening.end())
                if end < 0: raise ValueError('Unterminated Lua comment')
                i = end + len(close)
            else:
                end = source.find('\n', i + 2)
                i = len(source) if end < 0 else end
            line += source[start:i].count('\n')
            continue
        if source[i] in '\"\'':
            quote = source[i]
            i += 1
            while i < len(source):
                if source[i] == '\\': i += 2
                elif source[i] == quote:
                    i += 1
                    break
                else: i += 1
            else: raise ValueError('Unterminated quoted Lua string')
        elif (opening := LONG_OPEN.match(source, i)):
            close = ']' + opening.group(1) + ']'
            end = source.find(close, opening.end())
            if end < 0: raise ValueError('Unterminated long Lua string')
            i = end + len(close)
        else:
            if source[i] == '\n': line += 1
            i += 1
            continue
        raw = source[start:i]
        yield {'start': start, 'end': i, 'line': line,
               'raw': raw, 'source': decode_literal(raw)}
        line += raw.count('\n')


def inventory(upstream):
    result = []
    for path in sorted(Path(upstream).rglob('*.lua')):
        asset = path.relative_to(upstream).as_posix()
        if set(Path(asset).parts) & EXCLUDED_DIRS or asset in EXCLUDED_FILES:
            continue
        raw = path.read_bytes()
        source = raw.decode('utf-8-sig')
        digest = hashlib.sha256(raw).hexdigest()
        for token in string_tokens(source):
            identity = asset + '\0' + str(token['start']) + '\0' + token['source']
            context_start = source.rfind('\n', 0, token['start']) + 1
            context_end = source.find('\n', token['end'])
            if context_end < 0: context_end = len(source)
            result.append({**token, 'id': hashlib.sha256(identity.encode()).hexdigest()[:20],
                           'asset': asset, 'upstream_sha256': digest,
                           'context': source[context_start:context_end].strip()})
    return result


def is_candidate(record):
    s = COLOR.sub('', record['source'])
    if not WORD.search(s): return False
    if s.startswith(('/', '?', '\\')) or re.search(r'\.(?:lua|config|png|ogg|wav|json|animation|namesource|activeitem|object|frames|ttf|statuseffect)(?::\S*)?$', s):
        return False
    # Broad audit net: no candidate is emitted to the MOD without a reviewed ID.
    return (bool(re.search(r'[A-Za-z]{2}\s+[A-Za-z]', s))
            or bool(re.search(r'^[^A-Za-z]*[A-Z][a-z]+(?:[^A-Za-z]|$)', s))
            or bool(re.search(r'^[^A-Za-z]*[A-Z]{2,}(?:[^A-Za-z]|$)', s))
            or bool('^' in record['source'] and WORD.search(s)))


def load_lua(library_path=None):
    name = str(library_path) if library_path else (
        ctypes.util.find_library('lua5.4') or ctypes.util.find_library('lua5.3'))
    if not name: raise RuntimeError('Lua 5.3/5.4 shared library required')
    lua = ctypes.CDLL(name)
    state = ctypes.c_void_p
    lua.luaL_newstate.restype = state
    lua.luaL_openlibs.argtypes = [state]
    lua.luaL_loadbufferx.argtypes = [state, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]
    lua.luaL_loadbufferx.restype = ctypes.c_int
    lua.lua_pcallk.argtypes = [state, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_void_p]
    lua.lua_pcallk.restype = ctypes.c_int
    lua.lua_tolstring.argtypes = [state, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
    lua.lua_tolstring.restype = ctypes.c_void_p
    lua.lua_getglobal.argtypes = [state, ctypes.c_char_p]
    lua.lua_getglobal.restype = ctypes.c_int
    lua.lua_close.argtypes = [state]
    return lua


def run_lua(lua, source, name, execute=False, result_global=None):
    state = lua.luaL_newstate()
    try:
        lua.luaL_openlibs(state)
        raw = source.encode('utf-8')
        error = lua.luaL_loadbufferx(state, raw, len(raw), name.encode(), b't')
        if error == 0 and execute:
            error = lua.lua_pcallk(state, 0, 0, 0, 0, None)
        if error:
            n = ctypes.c_size_t()
            p = lua.lua_tolstring(state, -1, ctypes.byref(n))
            raise ValueError(ctypes.string_at(p, n.value).decode('utf-8', errors='replace'))
        if result_global is not None:
            lua.lua_getglobal(state, result_global.encode())
            n = ctypes.c_size_t()
            p = lua.lua_tolstring(state, -1, ctypes.byref(n))
            if not p: raise ValueError('Lua result global is not a string')
            return ctypes.string_at(p, n.value).decode('utf-8')
    finally:
        lua.lua_close(state)


def apply_display_hooks(upstream, project, output, lua, report):
    hook_path = project/'source/lua_dynamic_hooks.json'
    if not hook_path.exists(): return
    hooks = json.loads(hook_path.read_text())
    by_asset = {r['asset']:r for r in report['files']}
    count = 0
    for file in hooks['files']:
        asset = file['asset']
        upstream_raw = (upstream/asset).read_bytes()
        digest = hashlib.sha256(upstream_raw).hexdigest()
        if digest != file['upstream_sha256']:
            raise ValueError('Upstream dynamic-hook hash mismatch: '+asset)
        dest = output/asset
        source = dest.read_bytes().decode('utf-8') if dest.exists() else upstream_raw.decode('utf-8-sig')
        for r in file['replacements']:
            if source.count(r['old']) != r['count']:
                raise ValueError('Dynamic display edit mismatch: '+asset+' '+r['old'])
            source = source.replace(r['old'],r['new'])
            count += r['count']
        if file['require_helper']:
            source = 'require "/fujp/lua_display.lua"\n' + source
        run_lua(lua, source, '@localized/'+asset)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.encode('utf-8'))
        entry = by_asset.get(asset)
        if entry is None:
            entry = {'asset':asset, 'literals':0, 'upstream_sha256':digest}
            report['files'].append(entry)
            by_asset[asset] = entry
        entry['display_boundary_edits'] = sum(r['count'] for r in file['replacements'])
        entry['localized_sha256'] = hashlib.sha256(dest.read_bytes()).hexdigest()
    for helper_path, helper_dest in build_display_helpers(project, output, lua):
        report['files'].append({'asset':helper_dest.relative_to(output).as_posix(), 'literals':0,
                                'localized_sha256':hashlib.sha256(helper_path.read_bytes()).hexdigest(),
                                'new_support_module':True})
    dictionaries = json.loads((project/'source/lua_dynamic_translations.json').read_text())
    # Pet mood strings may have been saved before installation. Localize the
    # displayed copy using the same already validated JSON translations.
    inherited_statuses = 0
    catalog = project/'source/translated_catalog.jsonl'
    if catalog.exists():
        for line in catalog.read_text().splitlines():
            r = json.loads(line)
            if r['asset'] == 'monsters/statuses.config':
                dictionaries['labels'][r['source']] = r['translation']
                inherited_statuses += 1
    dictionary_path = output/'fujp/lua_display.config'
    dictionary_path.write_text(json.dumps(dictionaries,ensure_ascii=False,indent=2)+'\n')
    report['support_assets'] = [{'asset':'fujp/lua_display.config',
                                'sha256':hashlib.sha256(dictionary_path.read_bytes()).hexdigest()}]
    report['display_boundary_edits'] = count
    report['display_boundary_files'] = len(hooks['files'])
    report['display_aliases'] = sum(len(v) for v in dictionaries.values())
    report['inherited_validated_pet_status_fields'] = inherited_statuses
    report['non_display_logic_edits'] = 0


DISPLAY_HELPER_SOURCES = (
    ('compat/fujp/lua_display.lua', 'fujp/lua_display.lua'),
    ('compat/followup_022/fujp/species_display.lua', 'fujp/species_display.lua'),
    ('compat/followup_022/fujp/guide_display.lua', 'fujp/guide_display.lua'),
)


def build_display_helpers(project, output, lua):
    """Generate each reviewed display helper from its compatibility source."""
    project, output = Path(project), Path(output)
    inputs = []
    for source_rel, asset_rel in DISPLAY_HELPER_SOURCES:
        source = project/source_rel
        raw = source.read_bytes()
        run_lua(lua, raw.decode('utf-8-sig'), '@'+asset_rel)
        inputs.append((source, asset_rel, raw))
    generated = []
    for source, asset_rel, raw in inputs:
        destination = output/asset_rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        generated.append((source, destination))
    return generated


def build_helper_only(project, output, lua_library=None):
    """Regenerate only the pinned helper when the FU upstream tree is absent."""
    project, output = Path(project), Path(output)
    lua = load_lua(lua_library)
    generated = build_display_helpers(project, output, lua)
    rows = [{
        'asset': destination.relative_to(output).as_posix(),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'generated_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'source_matches_generated': source.read_bytes() == destination.read_bytes(),
    } for source, destination in generated]
    print(json.dumps({
        'generated_assets': rows,
        'scope': 'display-helper-only source generation; full upstream Lua build not run'
    }, ensure_ascii=False, indent=2))
    return [destination for _, destination in generated]


def build(upstream, project, output, machine=None):
    upstream, project, output = Path(upstream), Path(project), Path(output)
    manifest = json.loads((project/'source/lua_manifest.json').read_text())
    translated = json.loads((project/'source/lua_translations.json').read_text())
    if machine:
        merged = json.loads(Path(machine).read_text()); merged.update(translated); translated = merged
    grouped = collections.defaultdict(list)
    for record in manifest['selected']: grouped[record['asset']].append(record)
    if output.exists():
        # Avoid cleaning unrelated paths or the main MOD output directory.
        if output.name != 'lua-build': raise ValueError('Output directory must be lua-build')
        import shutil
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    lua = load_lua()
    report = {'selected_literals': len(manifest['selected']), 'files': [], 'untranslated': [],
              'nonliteral_edits_during_literal_translation': 0, 'syntax_errors': [], 'runtime_tested': False,
              'validation': 'Pinned hash, exact literal selection, unchanged nonselected source, Lua syntax, color/format tokens'}
    for asset, records in sorted(grouped.items()):
        original_raw = (upstream/asset).read_bytes()
        original = original_raw.decode('utf-8-sig')
        digest = hashlib.sha256(original_raw).hexdigest()
        tokens = {t['start']: t for t in string_tokens(original)}
        edits = []
        for r in records:
            if digest != r['upstream_sha256']: raise ValueError('Upstream hash mismatch: '+asset)
            token = tokens.get(r['start'])
            if not token or token['end'] != r['end'] or token['source'] != r['source']:
                raise ValueError('Literal manifest mismatch: '+r['id'])
            target = translated.get(r['source'])
            connector = r['source'] == ' of ' and target == ' / '
            if not isinstance(target, str) or target == r['source'] or (not connector and not re.search(r'[\u3040-\u30ff\u3400-\u9fff]', target)):
                report['untranslated'].append({'asset':asset, 'id':r['id'], 'source':r['source']})
                continue
            if COLOR.findall(r['source']) != COLOR.findall(target):
                raise ValueError('Changed color tags: '+r['source'])
            if FORMAT.findall(r['source']) != FORMAT.findall(target):
                raise ValueError('Changed Lua format specifiers: '+r['source'])
            if r['source'].count('\n') != target.count('\n'):
                raise ValueError('Changed display line breaks: '+r['source'])
            edits.append((r['start'], r['end'], quote_lua(target)))
        chunks, cursor = [], 0
        for start, end, replacement in sorted(edits):
            if start < cursor: raise ValueError('Overlapping Lua literal selections')
            chunks.extend([original[cursor:start], replacement]); cursor = end
        chunks.append(original[cursor:])
        patched = ''.join(chunks)
        # Reconstruct the unlocalized file by replacing approved output tokens
        # with their exact original tokens; catches accidental nonstring edits.
        old_tokens = list(string_tokens(original)); new_tokens = list(string_tokens(patched))
        if len(old_tokens) != len(new_tokens): raise ValueError('Lua token count changed')
        selected_starts = {start for start, _, _ in edits}
        old_cursor = new_cursor = 0
        for a, b in zip(old_tokens, new_tokens):
            if original[old_cursor:a['start']] != patched[new_cursor:b['start']]:
                raise ValueError('Nonliteral Lua source changed: '+asset)
            if a['start'] not in selected_starts and a['raw'] != b['raw']:
                raise ValueError('Nonselected Lua string changed: '+asset)
            old_cursor, new_cursor = a['end'], b['end']
        if original[old_cursor:] != patched[new_cursor:]: raise ValueError('Trailing Lua code changed')
        try:
            run_lua(lua, original, '@upstream/'+asset)
            run_lua(lua, patched, '@localized/'+asset)
        except ValueError as e:
            report['syntax_errors'].append({'asset':asset, 'error':str(e)})
            raise
        if edits:
            dest = output/asset; dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(patched.encode('utf-8'))
            report['files'].append({'asset':asset, 'literals':len(edits), 'upstream_sha256':digest,
                                    'localized_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    apply_display_hooks(upstream, project, output, lua, report)
    report['translated_literals'] = sum(x['literals'] for x in report['files'])
    report['file_count'] = len(report['files'])
    (project/'reports/lua_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'}, ensure_ascii=False, indent=2))
    if report['untranslated']: raise SystemExit('Some selected Lua display literals lack translations')
    return report


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('inventory'); a.add_argument('--upstream', required=True); a.add_argument('--project', required=True)
    a = sub.add_parser('build'); a.add_argument('--upstream', required=True); a.add_argument('--project', required=True); a.add_argument('--output', required=True); a.add_argument('--machine')
    a = sub.add_parser('helper'); a.add_argument('--project', required=True); a.add_argument('--output', required=True); a.add_argument('--lua-library', type=Path)
    args = p.parse_args()
    if args.command == 'inventory':
        records = inventory(Path(args.upstream)); candidates = [r for r in records if is_candidate(r)]
        dest = Path(args.project)/'source'; dest.mkdir(exist_ok=True, parents=True)
        (dest/'lua_inventory.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
        (dest/'lua_candidates.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in candidates))
        (dest/'lua_candidates.txt').write_text(''.join(f"{r['id']} {r['asset']}:{r['line']} {json.dumps(r['source'],ensure_ascii=False)}\n  {r['context']}\n" for r in candidates))
        print(json.dumps({'files':len({r['asset'] for r in records}), 'literals':len(records), 'candidates':len(candidates)}))
    elif args.command == 'helper':
        build_helper_only(args.project, args.output, args.lua_library)
    else:
        build(args.upstream, args.project, args.output, args.machine)


if __name__ == '__main__': main()
