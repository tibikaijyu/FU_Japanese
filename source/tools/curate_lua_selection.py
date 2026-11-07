#!/usr/bin/env python3
"""Reproduce the reviewed Lua display-literal selection for FU 6.5.8.

The broad lexer inventory is reduced by per-file purpose and reviewed negative
rules. The exported manifest records exact literal offsets and upstream hashes;
the release builder never runs these heuristics on an unreviewed FU update.
"""
import collections
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
INVENTORY = [json.loads(line) for line in (PROJECT/'source/lua_inventory.jsonl').read_text().splitlines()]
CANDIDATES = {json.loads(line)['id'] for line in (PROJECT/'source/lua_candidates.jsonl').read_text().splitlines()}

FILES = {
    'bees/beeBuilder.lua', 'bees/beeExaminer.lua', 'bees/beeExaminerITNShell.lua',
    'bees/interface/beeexaminer/beeexaminer.lua', 'fu_metagui/settings/module.lua',
    'interface/ai/fu_byosai.lua', 'interface/catalystfuelrefinery/refinery.lua',
    'interface/chests/ContainerControl.lua', 'interface/games/fossilgame/fossilgame.lua',
    'interface/kheAA/kheAA_router/kheAA_routerGui.lua',
    'interface/kheAA/kheAA_toolforge/kheAA_toolforgegui.lua',
    'interface/kukagps/kukagps.lua', 'interface/mechfuel/mechfuel.lua',
    'interface/mechfuelrefinery/fuelrefinery.lua', 'interface/mechstats/mechstats.lua',
    'interface/objectcrafting/fu_pethouse/fu_pethouse.lua',
    'interface/objectcrafting/fu_petnamer/fu_petnamer.lua',
    'interface/objectcrafting/fu_racializer/fu_racializer_gui.lua',
    'interface/scripted/fm_musicplayer/fm_musicplayer.lua',
    'interface/scripted/fu_craftinfo/fu_craftinfo.lua',
    'interface/scripted/fu_lootbox/fu_lootbox.lua',
    'interface/scripted/fu_matmodplacer/fu_matmodplacer.lua',
    'interface/scripted/fu_upgradetable/fu_upgradetable.lua',
    'interface/scripted/spaceStation/spaceStation.lua',
    'interface/scripted/statWindow/statWindow.lua',
    'interface/scripted/stickynotepadfu/stickynotepadfu.lua',
    'interface/scripted/techshop/techshop.lua',
    'interface/scripted/tunableoredetector/tunableoredetector_gui.lua',
    'interface/scripted/xcustomcodex/xcodexui.lua',
    'interface/shipnameplate/fu_shipnameplate_ui.lua',
    'items/active/unsorted/fu_monsterinspector/inspector.lua',
    'items/active/unsorted/kheAA/pointsensor/pointsensor.lua',
    'items/active/weapons/other/skittlegun/skittlegun.lua',
    'items/active/weapons/other/skittlegun/skittlegunfake.lua',
    'items/active/weapons/ranged/gunammo.lua', 'metagui.lua',
    'objects/augmentextractor/aex.lua',
    'objects/crafting/farmwell/farmwell.lua',
    'objects/crafting/servitorloader/servitorloader.lua',
    'objects/crafting/xiwell/xiwell.lua',
    'objects/generic/extractor_research.lua',
    'objects/generic/fm_musicplayer/fm_musicplayer.lua',
    'objects/generic/pong/pong.lua',
    'objects/generic/timeobelisk/obeliskscan.lua',
    'objects/isn_unifiedgrowingtray.lua',
    'objects/minibiome/elder/cultaltar/cultaltar.lua',
    'objects/minibiome/lush/poptopcavern.lua',
    'objects/pilch_shieldadminconsole/pilch_shieldadminconsole.lua',
    'objects/pilch_shieldadminconsole/pilch_shieldadminconsole_gui.lua',
    'objects/pilch_shieldgenerator/pilch_shieldgenerator.lua',
    'objects/pilch_shieldgenerator/pilch_shieldgeneratorasteroid.lua',
    'objects/portals/extrateleportradar/extrateleportradar.lua',
    'objects/power/fu_liquidcondenser/isn_resource_generator.lua',
    'objects/power/isn_atmoscondenser/isn_resource_generator.lua',
    'objects/power/isn_battery.lua',
    'objects/scanInteractableExample/scaninteractionexample.lua',
    'objects/ship/fu_byospethouse/fu_byospethouse.lua',
    'objects/ship/fu_crewdeed/fu_crewdeed.lua',
    'quests/scripts/items/itemspawn.lua', 'quests/scripts/main.lua',
    'scripts/colonycorefu.lua', 'scripts/companions/capturable.lua',
    'scripts/effectUtil.lua', 'scripts/fu_crewoverflow.lua',
    'scripts/fupesttrap.lua', 'scripts/fuwell.lua',
    'scripts/pandorasbox/objects/pandorasboxfeatures.lua',
    'scripts/pandorasbox/objects/pandorasboxkeepcontent.lua',
    'spawners/fubotspawner.lua', 'spawners/fuminionspawner.lua',
    'stats/effects/fu_weaponeffects/Skittles/timefreezeSkittles.lua',
    'stats/effects/partytime/partytime3.lua',
    'zb/newSail/fr_toggleFunction.lua', 'zb/newSail/fu_customFunctions.lua',
    'zb/newSail/newSail.lua', 'zb/newSail/zb_customFunctions.lua',
    'zb/questList/questList.lua', 'zb/researchTree/researchTree.lua',
    'zb/updateInfoWindow/updateInfoWindow.lua',
    'zb/updateInfoWindow/updateInfoWindowError.lua',
}
PREFIXES = ('items/buildscripts/', 'objects/colonysystem2/addons/')

# The following candidates were individually identified as keys, modes, code
# patterns, or image/sound selectors. Some ordinary English labels share these
# spellings elsewhere, so the exclusion is per source file or reviewed context.
EXCLUDED_VALUES = {
    'bees/beeBuilder.lua': {'Label'},
    'bees/beeExaminer.lua': {'ID'},
    'interface/ai/fu_byosai.lua': {'Upgradable','Buildable','Back','Byos'},
    'interface/kheAA/kheAA_router/kheAA_routerGui.lua': {'Filter'},
    'interface/mechstats/mechstats.lua': {'Directives'},
    'interface/objectcrafting/fu_racializer/fu_racializer_gui.lua': {'itemData not set'},
    'interface/scripted/fm_musicplayer/fm_musicplayer.lua': {'Hover'},
    'interface/scripted/fu_upgradetable/fu_upgradetable.lua': {'gun staff'},
    'interface/scripted/statWindow/statWindow.lua': {'Resist','Resistance'},
    'interface/scripted/tunableoredetector/tunableoredetector_gui.lua': {'Scanning'},
    'items/active/weapons/other/skittlegun/skittlegun.lua': {'Ability','Shift'},
    'objects/minibiome/lush/poptopcavern.lua': {'Return'},
    'objects/portals/extrateleportradar/extrateleportradar.lua': {'Return'},
    'scripts/effectUtil.lua': {'Vehicle'},
    'objects/power/isn_battery.lua': {'FF;0.1'},
    'zb/updateInfoWindow/updateInfoWindow.lua': {'Data'},
}
EXCLUDED_IDS = {
    # Sticky-note exception diagnostics are logged, not shown in the pane.
    'a2fabba8a8ea25d5c47a',
    # Codex logging prefix passed to the logger constructor.
    '879324e79c0358802785',
}


def decision(r):
    asset, value, context = r['asset'], r['source'], r['context']
    extra = (
        value == 'unknown' and asset.startswith('items/buildscripts/')
        or value == ' of ' and asset == 'interface/scripted/xcustomcodex/xcodexui.lua'
        or value == "' questline" and asset == 'zb/questList/questList.lua'
        or value in {' am',' pm'} and asset == 'interface/kukagps/kukagps.lua'
    )
    if r['id'] not in CANDIDATES and not extra: return 'outside_broad_candidate_net'
    if re.search(r'\b(?:logInfo|logWarn|logError|debugLog|debugText|setLogMap|error|warn|printfunc|dbg)\s*\(', context):
        return 'log_or_debug_diagnostic'
    if re.fullmatch(r'#?[0-9A-Fa-f]{4,}(?:;[0-9.]+)?', value): return 'color_literal'
    if r['id'] in EXCLUDED_IDS: return 'logging_or_code_selector'
    if value in EXCLUDED_VALUES.get(asset, set()): return 'internal_key_or_mode'
    if asset.startswith('monsters/') and 'monster.setName(' in context: return 'selected'
    if asset not in FILES and not asset.startswith(PREFIXES): return 'internal_or_non_display_context'
    if asset == 'interface/scripted/spaceStation/spaceStation.lua':
        if not any(x in context for x in ('widget.setText(', 'textTyper.init(')):
            return 'command_id_or_state_key'
    # Guards for token kinds that occur in otherwise display-oriented files.
    if 'world.entityQuery(' in context or 'warpAction =' in context: return 'engine_identifier'
    return 'selected'


selected, excluded = [], []
for record in INVENTORY:
    result = decision(record)
    if result == 'selected':
        selected.append(record)
    elif record['id'] in CANDIDATES:
        excluded.append({**record, 'reason': result})

manifest = {
    'upstream_commit':'17868d86c9bb7bc00f92038fb78b48cebd1b41b8',
    'selection_review':'ChatGPT reviewed literal contexts; no automatic arbitrary-string translation',
    'reserved_files':['scripts/actions/npc.lua', 'interface/scripted/sbvn/pandorasboxsbvngui.lua', 'zb/zb_textTyper.lua'],
    'selected':selected,
}
(PROJECT/'source/lua_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(PROJECT/'source/lua_catalog.jsonl').write_text(''.join(json.dumps({
    'id':r['id'],'asset':r['asset'],'path':'/luaLiteral/'+str(r['start']),
    'source':r['source'],'category':'lua','origin':r['asset']
},ensure_ascii=False)+'\n' for r in selected))
(PROJECT/'reports/lua_selection_audit.json').write_text(json.dumps({
    'lua_files_in_upstream':1668,
    'files_with_lexed_strings':len({r['asset'] for r in INVENTORY}),
    'string_literals':len(INVENTORY),'broad_candidates':len(CANDIDATES),
    'selected_literals':len(selected),'selected_unique_sources':len({r['source'] for r in selected}),
    'selected_files':len({r['asset'] for r in selected}),
    'excluded_counts':dict(collections.Counter(r['reason'] for r in excluded)),
    'excluded':excluded,
},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'selected':len(selected),'unique':len({r['source'] for r in selected}),'files':len({r['asset'] for r in selected})}))
