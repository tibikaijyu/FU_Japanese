#!/usr/bin/env python3
"""Freeze narrowly scoped display-boundary edits against reviewed FU sources."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
UPSTREAM = PROJECT.parent/'fu-upstream'
rules = {}


def add(asset, old, new, count=1, reason='Display alias only; original gameplay value retained'):
    rules.setdefault(asset, []).append({'old':old,'new':new,'count':count,'reason':reason})


for i in range(1,7):
    for expr in (f'b{i}[1]', f'b{i}'):
        add('interface/scripted/spaceStation/spaceStation.lua',
            f'widget.setText("button{i}", tostring({expr}))',
            f'widget.setText("button{i}", fujpDisplay.text(tostring({expr})))')

add('interface/mechfuel/mechfuel.lua',
    '.. textColor .. ";" .. type)',
    '.. textColor .. ";" .. fujpDisplay.text(type))')
add('bees/beeBuilder.lua', '..subtype', '..fujpDisplay.beeSubtype(subtype)')
add('zb/newSail/newSail.lua', '..crew.config.species..', '..fujpDisplay.species(crew.config.species)..')
add('items/buildscripts/buildsapling.lua', '..(parameters.foliageName or ', '..(foliageName or ')
add('items/buildscripts/buildsapling.lua', '..(parameters.stemName or ', '..(stemName or ')
add('interface/objectcrafting/fu_pethouse/fu_pethouse.lua',
    'widget.setText(listItem .. ".name", pet)',
    'widget.setText(listItem .. ".name", fujpDisplay.monster(pet))')
add('interface/objectcrafting/fu_pethouse/fu_pethouse.lua',
    '.. world.getObjectParameter(containerId, "shipPetType") .. "."',
    '.. fujpDisplay.monster(world.getObjectParameter(containerId, "shipPetType")) .. "."')
add('objects/power/isn_atmoscondenser/isn_resource_generator.lua',
    '..firstToUpper(weight)..', '..fujpDisplay.text(firstToUpper(weight))..', count=3)
add('scripts/companions/capturable.lua',
    'monster.setName(petName .. "\\n ^white;" .. storage.statusText)',
    'monster.setName(petName .. "\\n ^white;" .. fujpDisplay.text(storage.statusText))',
    reason='Translate cached built-in pet mood only when drawing; petName and saved status remain unchanged')

# The original questline headings are bitmap text. The config overlay supplies
# label/cover widgets; retain each image and quest ID and draw its existing
# localized data.config title above the covered text area.
quest_asset = 'zb/questList/questList.lua'
for frame in ('default', 'unavailable'):
    anchor = 'widget.setImage(path..".banner", "/zb/questList/banners/"..tbl.id..".png:'+frame+'")'
    title = 'tostring(QD.strings.questlines[tbl.id].title)'
    if frame == 'unavailable': title = '"^gray;"..'+title+'.."^reset;"'
    add(quest_asset, anchor,
        anchor+'\n\t\t\twidget.setText(path..".fuJapaneseBannerTitle", '+title+')',
        reason='Draw localized questline title over bitmap text; retain quest data and image IDs')
anchor = 'widget.setImage("questlineBanner", "/zb/questList/banners/"..questline..".png:default")'
add(quest_asset, anchor,
    anchor+'\n\t\t\twidget.setText("fuJapaneseQuestlineTitle", tostring(QD.strings.questlines[questline].title))'
          +'\n\t\t\twidget.setVisible("fuJapaneseQuestlineTitle", true)'
          +'\n\t\t\twidget.setVisible("fuJapaneseQuestlineCover", true)',
    reason='Show localized title and bitmap cover when entering a questline')
anchor = 'widget.setImage("questlineBanner", "/assetmissing.png")'
add(quest_asset, anchor,
    anchor+'\n\twidget.setText("fuJapaneseQuestlineTitle", "")'
          +'\n\twidget.setVisible("fuJapaneseQuestlineTitle", false)'
          +'\n\twidget.setVisible("fuJapaneseQuestlineCover", false)',
    reason='Clear and hide localized title and cover on returning to the questline list')

element_builders = ['buildboomerang','buildweapon','neb-buildrandombow','buildunrandweapon',
                    'neb-buildbow','fubuildmagnorb','fubuildchakram','buildfuoverheatweapon','buildbow']
for stem in element_builders:
    add(f'items/buildscripts/{stem}.lua',
        'replacePatternInData(config, nil, "<elementalName>", elementalType:gsub("^%l", string.upper))',
        'replacePatternInData(config, nil, "<elementalName>", fujpDisplay.text(elementalType:gsub("^%l", string.upper)))',
        reason='Only the display <elementalName> placeholder; <elementalType>, image names, damage IDs stay original')

category_builders = ['buildboomerang','neb-buildrandombow','neb-buildbow','fubuildmagnorb',
                     'fubuildchakram','buildfist','buildwhip','buildbow']
for stem in category_builders:
    add(f'items/buildscripts/{stem}.lua',
        'config.tooltipFields.subtitle = parameters.category',
        'config.tooltipFields.subtitle = fujpDisplay.text(parameters.category)')

records = []
for asset, replacements in sorted(rules.items()):
    source = (UPSTREAM/asset).read_bytes()
    decoded = source.decode('utf-8-sig')
    for r in replacements:
        if decoded.count(r['old']) != r['count']:
            raise ValueError(f"Hook selection count mismatch in {asset}: {r['old']}")
    records.append({'asset':asset,'upstream_sha256':hashlib.sha256(source).hexdigest(),
                    'require_helper':asset != quest_asset,'replacements':replacements})
(PROJECT/'source/lua_dynamic_hooks.json').write_text(json.dumps({
    'upstream_commit':'17868d86c9bb7bc00f92038fb78b48cebd1b41b8',
    'scope':'Display arguments and <elementalName> only; not gameplay IDs or saved values',
    'files':records
},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(records),'replacements':sum(r['count'] for rs in rules.values() for r in rs)}))
