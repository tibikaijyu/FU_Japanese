#!/usr/bin/env python3
"""Extract only known display fields; never translate asset identifiers."""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from common import read_asset, walk, ptr, unptr, has_words, dump
from append_localization import catalog_row as append_row, matching_paths
from namegen_safety import is_namegen_scope, is_namegen_display_path

try:
    from extra_schemas import EXTRA_EXTS, category as extra_category
except ImportError:
    EXTRA_EXTS = set()
    def extra_category(asset, parts, parent, value):
        return None

ASSET_EXTS = set('object item activeitem consumable augment matitem liqitem head chest legs back tech material raceeffect weaponability instrument thrownitem miningtool harvestingtool flashlight painttool wiretool tillingtool beamaxe inspectiontool coinitem unlock'.split())
OTHER_EXTS = set('config radiomessages questtemplate codex npctype monstertype species biome statuseffect tooltip aimission aicommand cinematic currency collection particle stagehand'.split())
EXCLUDED_DIRS = {'.git', 'a_modders', 'a_notyetadded', 'tests', '_previewimage', 'tilesets'}
DISPLAY_KEYS = {'description', 'shortdescription', 'subtitle', 'title', 'friendlyName', 'displayName', 'senderName'}
UI_TEXT_KEYS = {'caption', 'hint', 'tooltip', 'title', 'subtitle'}


def category(asset, parts, parent, value):
    if not parts or not has_words(value):
        return None
    ext = Path(asset).suffix[1:]
    key = parts[-1]
    p = '/'.join(parts)
    if is_namegen_scope(asset, parts) and not is_namegen_display_path(asset, parts):
        return None
    # Never interpret image filenames, asset paths or script identifiers as text.
    if re.search(r'\.(png|lua|config|ogg|frames|animation)(?::[^ ]*)?$', value.strip(), re.I):
        return None
    if asset.startswith(('behaviors/', 'vehicles/modularmech/')):
        return None
    if asset.startswith('zb/researchTree/') and parts[0] == 'strings' and len(parts) > 1 and parts[1] in {'trees','research','info','currencies'}:
        return 'research'
    if ext == 'radiomessages' and key in {'text','senderName'}:
        return 'radio'
    if ext == 'codex' and (key in {'title','description'} or parts[0] in {'contentPages','longContentPages'}):
        return 'codex'
    if ext == 'questtemplate':
        if key in {'title','text','completionText','turnInDescription','objectiveDescription','senderName'}:
            return 'quests'
        if 'descriptions' in parts or 'generatedText' in parts or any(x.endswith('Text') or x.endswith('Note') for x in parts):
            return 'quests'
        if key == 'text' and 'radioMessages' in parts:
            return 'radio'
        if any(x in {'parcelName','parcelDescription'} for x in parts):
            return 'quests'
    if asset.startswith('dialog/') and ext == 'config':
        return 'dialogue'
    if ext in {'npctype','monstertype'} and any(x in {'dialog','Dialog'} for x in parts):
        return 'dialogue'
    if ext == 'npctype' and (p.startswith('scriptConfig/crew/role/') and key in {'name','field'} or p.startswith('scriptConfig/crew/ranks/') or key == 'npcname'):
        return 'crew'
    if ext in ASSET_EXTS:
        if key in DISPLAY_KEYS or key.endswith('Description'):
            return 'items'
        if 'tooltipFields' in parts and (key.endswith(('Label','Title','Text')) or key in {'primaryAbility','altAbility'}):
            return 'items'
        if 'chatOptions' in parts:
            return 'dialogue'
        if ext == 'weaponability' and p == 'ability/name' or ext == 'activeitem' and p in {'primaryAbility/name','altAbility/name'}:
            return 'abilities'
        if ext == 'unlock' and key == 'unlockMessage':
            return 'items'
        if ext == 'inspectiontool' and parts[0] in {'outOfRangeText','nothingThereText'}:
            return 'interface'
    if ext == 'statuseffect' and (key == 'label' or parts[0] == 'typerParticleConfig' and 'texts' in parts):
        return 'status'
    if ext == 'biome' and key == 'friendlyName':
        return 'worlds'
    if ext == 'species' and (parts[0] == 'charGenTextLabels' or parts[0] == 'charCreationTooltip' and key in DISPLAY_KEYS):
        return 'species'
    if ext in {'aimission','aicommand'} and (key.endswith('Text') or key == 'text' or key in DISPLAY_KEYS):
        return 'missions'
    if ext == 'cinematic' and key == 'text':
        return 'cinematic'
    if ext in {'currency','collection'} and key in DISPLAY_KEYS:
        return 'interface'
    if isinstance(parent, dict):
        typ = parent.get('type')
        if typ in {'label','textbox'} and key == 'value' or typ == 'button' and key == 'caption' or typ == 'title' and key in {'title','subtitle'}:
            return 'interface'
        if typ in {'textbox','button'} and key in {'hint','tooltip'}:
            return 'interface'
    if ext == 'tooltip' and key == 'value':
        return 'interface'
    # Full context is unavailable for a source patch changing one widget field.
    if ext == 'config' and ('gui' in parts or 'paneLayout' in parts):
        if key in UI_TEXT_KEYS or key == 'value' and any(re.search(r'(lbl|label|title|subtitle|text)', x, re.I) for x in parts[:-1]):
            return 'interface'
    if ext == 'config':
        basename = Path(asset).name
        # FU's custom ship/S.A.I.L. panels use display dictionaries rather than
        # standard widget fields. Keep state names, callbacks and asset paths intact.
        if asset == 'interface/ai/fu_byosai.config':
            if len(parts) == 3 and parts[0] == 'states' and key == 'text':
                return 'interface'
            if len(parts) == 5 and parts[0] == 'states' and parts[2] == 'buttons' and key == 'name':
                return 'interface'
            if parts[0] in {'shipResetConfirmationDialogs','backgroundPresentConfirmation'} and key in {'title','subtitle','message','okCaption','cancelCaption'}:
                return 'interface'
        if asset == 'zb/newSail/data.config':
            if parts[0] == 'GUI' and len(parts) == 2 and key in {'title','subtitle'}:
                return 'interface'
            if parts[0] == 'Speech' and key == 'text':
                return 'interface'
            if len(parts) == 3 and parts[:2] == ('TextData','currencies'):
                return 'interface'
            if len(parts) == 4 and parts[0] == 'Data' and parts[1] in {'misc','miscAdmin'} and key == '1':
                return 'interface'
        if asset == 'zb/questList/data.config' and parts[0] == 'strings':
            return 'quests'
        if asset in {
            'interface/kukagps/biomes.config', 'interface/kukagps/dungeons.config',
            'interface/kukagps/weather.config', 'interface/kukagps/ores.config',
            'interface/kukagps/enviroment.config'
        } and len(parts) == 1:
            return 'worlds'
        if asset == 'interface/scripted/fu_matmodplacer/fu_matmodplacer.config' and len(parts) == 3 and parts[0] == 'matMods' and key in {'name','description'}:
            return 'interface'
        if asset == 'interface/scripted/spaceStation/spaceStationData.config' and len(parts) == 3 and parts[0] in {'medical','military'} and key in {'0','4'}:
            return 'interface'
        if asset == 'interface/scripted/tunableoredetector/tunableoredetector.config' and len(parts) == 2 and parts[0] == 'stringData':
            return 'interface'
        if asset == 'interface/objectcrafting/fu_pethouse/fu_pethouse.config' and parts[0] == 'popupMessages':
            return 'interface'
        if asset == 'interface/objectcrafting/fu_pethouse/fu_pethouse_confirmation.config' and len(parts) == 1 and key in {'title','subtitle','message','okCaption','cancelCaption'}:
            return 'interface'
        if asset == 'interface/scripted/spaceStation/texts.config':
            # These two entries are long third-party film/song quotations.
            if p in {'generic/chat4','generic/chat5'}:
                return None
            if len(parts) == 2 and parts[0] == 'defaultButtonStates':
                return 'interface'
            if len(parts) == 2 and parts[0] in {'generic','apex','avian','floran','glitch','human','hylotl','novakid','cari'} and value != 'deprecated':
                if re.fullmatch(r'(?:chat|cantAfford|questStage)\d+', key) or key in {'welcome','militarySpecial','medicalSpecial','tradingSpecial','tradingSpecialMax','returnSpecial','activeEnhancer','acquireEnhancer','removeEnhancer','medBrochure','hireMerc','noMoreMerc'}:
                    return 'dialogue'
        if basename == 'cockpit.config' and (parts[0] in {'terraformedPlanetDescription','worldTypeDescription','clusterMoons','threatLevelText','visitableTypeDescription','planetTypeNames','starTypeNames','jumpDialog','topLeftButtonTooltips'} or key == 'displayName'):
            return 'worlds'
        if basename in {'system_objects.config','parts.config'} and key == 'displayName':
            return 'worlds'
        if basename == 'quests.config' and parts[0] in {'objectiveDescriptions','pronouns'}:
            return 'quests'
        if basename == 'statuses.config' and parts[0] == 'statuses':
            return 'status'
        if basename == 'extraStatsWindow.config' and key in {'tooltip','defaultTooltip'}:
            return 'interface'
        if basename == 'statWindow.config' and key == 'name':
            return 'interface'
        if key in {'blueprintUnlock','blueprintAlreadyKnown','defaultPetNameLabel','trackLabel','untrackLabel'}:
            return 'interface'
        if 'TextData' in parts and 'strings' in parts or 'fu_text' in parts:
            return 'interface'
        if parts[0] == 'shipStatus' and key == 'text':
            return 'interface'
    return None


def patch_ops(value):
    if isinstance(value, list):
        for entry in value:
            yield from patch_ops(entry)
    elif isinstance(value, dict) and 'op' in value:
        yield value


def extract(root, dest, merge_assets=()):
    root, dest = Path(root), Path(dest)
    records = {}
    appends = {}
    report = {'parsed_assets':0,'parse_errors':[],'skipped_append_display_fields':[],
              'resolved_append_display_fields':0, 'deferred_append_display_fields':0,
              'excluded_lua_files':0}
    resolved_documents = {}
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(x in EXCLUDED_DIRS for x in path.relative_to(root).parts):
            continue
        if path.suffix == '.lua':
            report['excluded_lua_files'] += 1
        is_patch = path.suffix == '.patch'
        target = rel[:-6] if is_patch else rel
        ext = Path(target).suffix[1:]
        if ext not in ASSET_EXTS | OTHER_EXTS | set(EXTRA_EXTS):
            continue
        try:
            data = read_asset(path)
        except Exception as e:
            report['parse_errors'].append({'file':rel, 'error':str(e)[:200]})
            continue
        report['parsed_assets'] += 1
        candidates = []
        if is_patch:
            for op in patch_ops(data):
                if op.get('op') not in {'add','replace'} or 'value' not in op:
                    continue
                prefix = tuple(unptr(op.get('path','')))
                for parts, value, parent in walk(op['value']):
                    candidates.append((prefix + parts, value, parent))
        else:
            candidates = walk(data)
        for parts, source, parent in candidates:
            cat = category(target, parts, parent, source) or extra_category(target, parts, parent, source)
            if not cat:
                continue
            if '-' in parts:
                if (root / target).is_file():
                    if target not in resolved_documents:
                        from validate import apply_batches
                        resolved_documents[target] = apply_batches(read_asset(root / target), data)
                    paths = matching_paths(resolved_documents[target], parts, source)
                    if paths:
                        for pointer in paths:
                            identity = target + '\0' + pointer + '\0' + source
                            records[identity] = {
                                'id':hashlib.sha256(identity.encode()).hexdigest()[:20],
                                'asset':target, 'path':pointer, 'source':source,
                                'category':cat, 'origin':rel,
                            }
                        report['resolved_append_display_fields'] += 1
                        continue
                row = append_row(target, ptr(parts), source, cat, rel)
                appends[row['id']] = row
                report['deferred_append_display_fields'] += 1
                continue
            pointer = ptr(parts)
            identity = target + '\0' + pointer + '\0' + source
            records[identity] = {
                'id':hashlib.sha256(identity.encode()).hexdigest()[:20],
                'asset':target, 'path':pointer, 'source':source,
                'category':cat, 'origin':rel,
            }
    result = sorted(records.values(), key=lambda r:(r['asset'],r['path'],r['source']))
    dest.mkdir(parents=True, exist_ok=True)
    merge_assets = set(merge_assets)
    if merge_assets:
        from upstream_overrides import manifest as verify_upstream_overrides
        if merge_assets != {'radiomessages/fu_quests.radiomessages'}:
            raise ValueError('--merge-asset is restricted to the pinned radio asset')
        verify_upstream_overrides(dest.parent)
        expected = dest.parent / 'upstream-overrides/radiomessages/fu_quests.radiomessages'
        if not expected.is_file() or not root.joinpath('radiomessages/fu_quests.radiomessages').is_file():
            raise ValueError('Radio override extraction root must contain the pinned asset')
        override_files = {path.resolve() for path in root.rglob('*') if path.is_file()}
        if override_files != {expected.resolve()}:
            raise ValueError('Radio override extraction root must contain only the pinned asset')
        if root.joinpath('radiomessages/fu_quests.radiomessages').resolve() != expected.resolve():
            raise ValueError('Radio override extraction input differs from the pinned manifest')
        old_catalog = dest/'catalog.jsonl'
        old_appends = dest/'append_catalog.jsonl'
        if not old_catalog.is_file():
            raise ValueError('--merge-asset requires existing catalog.jsonl')
        prior = [json.loads(line) for line in old_catalog.read_text(encoding='utf-8').splitlines()]
        result = [row for row in prior if row['asset'] not in merge_assets] + result
        if old_appends.is_file():
            prior_appends = [json.loads(line) for line in old_appends.read_text(encoding='utf-8').splitlines()]
            appends = {row['id']:row for row in prior_appends if row['asset'] not in merge_assets} | appends
        actual_assets = {row['asset'] for row in records.values()}
        if actual_assets != merge_assets:
            raise ValueError(f'Extracted assets do not match --merge-asset: {sorted(actual_assets)}')
    result = sorted({(row['asset'],row['path'],row['source']):row for row in result}.values(), key=lambda r:(r['asset'],r['path'],r['source']))
    (dest/'catalog.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result), encoding='utf-8', newline='\n')
    (dest/'append_catalog.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in sorted(appends.values(),key=lambda r:r['id'])),encoding='utf-8', newline='\n')
    report['entries'] = len(result)
    if merge_assets:
        report['extraction_scope'] = {'mode':'merge_assets','assets':sorted(merge_assets),'other_catalog_rows':'retained from the existing catalog'}
    report['unique_source_strings'] = len({r['source'] for r in result})
    report['assets_with_display_fields'] = len({r['asset'] for r in result})
    report['by_category'] = dict(collections.Counter(r['category'] for r in result))
    report['source_characters_unique'] = sum(len(x) for x in {r['source'] for r in result})
    report['append_catalog_entries'] = len(appends)
    dump(dest/'extraction_report.json', report)
    # Any catalog regeneration changes the append row set; require a fresh
    # effective-asset capture before append localization can be built again.
    (dest/'append_index_basis.json').unlink(missing_ok=True)
    print(json.dumps({k:v for k,v in report.items() if k not in {'skipped_append_display_fields','parse_errors'}},ensure_ascii=False,indent=2))
    print('parse_errors:',len(report['parse_errors']), 'skipped appends:',len(report['skipped_append_display_fields']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('upstream')
    parser.add_argument('output')
    parser.add_argument('--merge-asset', action='append', default=[], help='Replace only these asset rows in existing catalogs')
    args = parser.parse_args()
    extract(args.upstream,args.output,args.merge_asset)
