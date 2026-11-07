"""Additional, inspected FU 6.5.8 display schemas.

Only values are translated. Dictionary keys, asset IDs, enum values and event
targets must retain their original spelling. In particular, ``fuelType`` is an
enum despite also appearing on screen; its renderer needs a display lookup.
"""
from pathlib import Path
import re

from common import has_words
from namegen_safety import is_namegen_scope, is_namegen_display_path


EXTRA_EXTS = {
    'sbvn', 'itemdescription', 'ui', 'json', 'liquid', 'monsterskill',
    'animation', 'matmod', 'dungeon', 'projectile', 'structure', 'vehicle',
    'namesource',
}

_DISPLAY = {
    'description', 'shortdescription', 'subtitle', 'subTitle', 'title',
    'friendlyName', 'displayName', 'senderName', 'bookmarkName',
}
_NPC_DIALOG = {
    'dialog', 'Dialog', 'converse', 'hail', 'follow', 'flee', 'encourage',
    'accuse', 'tout', 'rent', 'alert', 'welcome', 'beacon', 'safe', 'helpme',
}
_ITEM_EXTS = set('object item activeitem consumable augment matitem liqitem head chest legs back tech material raceeffect weaponability instrument thrownitem miningtool harvestingtool flashlight painttool wiretool tillingtool beamaxe inspectiontool coinitem unlock'.split())


def display_description(key):
    # FU contains both e.g. floranDescription and florandescription.
    return key.lower().endswith('description')


def category(asset, parts, parent, value):
    """Return a display category for previously uncovered safe JSON fields."""
    if not parts or not has_words(value):
        return None
    ext = Path(asset).suffix[1:]
    key = parts[-1]
    p = '/'.join(parts)
    if is_namegen_scope(asset, parts) and not is_namegen_display_path(asset, parts):
        return None
    if re.search(r'\.(png|lua|config|ogg|frames|animation|wav|json)(?::[^ ]*)?$', value.strip(), re.I):
        return None
    # IDs called `title` in behavior editor graphs are not UI text.
    if asset.startswith(('behaviors/', 'vehicles/modularmech/')):
        return None

    if ext == 'sbvn':
        if parts[0] == 'displayConfig' and key in {'title', 'subtitle'}:
            return 'visual_novel'
        if parts[0] in {'scenes', 'titleScene'}:
            if key == 'text':
                return 'visual_novel'
            if len(parts) >= 3 and parts[-3] == 'options' and key == '0':
                return 'visual_novel'
        return None

    if ext == 'itemdescription':
        if key == 'value' or key in {'title', 'subtitle', 'caption', 'hint', 'tooltip'}:
            return 'interface'
    if ext == 'ui':
        if key in {'title', 'subtitle', 'caption', 'hint', 'tooltip', 'text'}:
            return 'interface'
    if ext in {'liquid', 'matmod'} and (display_description(key) or key in _DISPLAY):
        return 'worlds'
    if ext == 'monsterskill' and key == 'label':
        return 'abilities'
    if ext == 'monstertype':
        if key in {'description', 'shortdescription', 'capturedMonsterName'}:
            return 'monsters'
    if ext in {'particle', 'animation', 'projectile', 'activeitem', 'statuseffect', 'object', 'vehicle'}:
        if key == 'text' and (isinstance(parent, dict) and parent.get('type') == 'text'):
            return 'combat_text'
    if ext == 'statuseffect' and 'typerParticleConfig' in parts and 'texts' in parts:
        return 'status'
    if ext == 'stagehand' and len(parts) == 3 and parts[0] == 'radioMessages' and key in {'0', '2'}:
        return 'radio'

    if ext in _ITEM_EXTS:
        if display_description(key):
            return 'items'
        if any(x in {'dialog', 'Dialog', 'chatStrings', 'grumbleText'} for x in parts):
            return 'dialogue'
        if key in {'failMessage', 'notOnPlanetMessage', 'failureText', 'unlockMessage', 'activationText'}:
            return 'interface'
        if ext == 'augment' and key in {'ammoName', 'reelName'}:
            return 'abilities'
        if ext == 'activeitem' and key == 'shieldPower':
            return 'abilities'
        if asset == 'objects/ship/fu_shipnameplate/fu_shipnameplate.object' and parts[0] == 'text':
            return 'interface'
        if asset == 'objects/minibiome/lush/poptopcavern.object' and parts[0] == 'noTricorderInteractData' and key in {'message', 'okCaption', 'cancelCaption'}:
            return 'interface'
        if asset == 'items/active/unsorted/fu_defaultunlockdiagnoser/fu_defaultunlockdiagnoser.activeitem' and parts[0] == 'strings' and key != 'logString':
            return 'interface'
    if ext == 'npctype' and parts[0] == 'scriptConfig' and any(x in _NPC_DIALOG for x in parts[1:]):
        # A `dialog` scalar in behaviorConfig is a lookup path, not dialogue.
        if key not in _NPC_DIALOG and not value.startswith('dialog.'):
            return 'dialogue'
    if ext in _ITEM_EXTS | {'npctype', 'config', 'dungeon', 'structure'}:
        if any(x in {'paneLayoutOverride', 'paneLayout', 'gui'} for x in parts):
            if key in {'title', 'subtitle', 'caption', 'hint', 'tooltip'}:
                return 'interface'
            if key in {'value', 'text'} and any(re.search(r'(lbl|label|title|subtitle|text)', x, re.I) for x in parts[:-1]):
                return 'interface'

    if ext == 'species' and parts[0] == 'charCreationTooltip' and key == 'subTitle':
        return 'species'
    if ext == 'questtemplate':
        if key in {'bookmarkName', 'shipRepairMessage'}:
            return 'quests'
        if key == 'description' and 'conditions' in parts:
            return 'quests'
        if len(parts) >= 2 and parts[-2:] == ('example', 'name'):
            return 'quests'
    if ext in {'dungeon', 'structure'}:
        if 'parameters' in parts:
            if display_description(key) or key == 'npcname':
                return 'dungeon_text'
            if any(x in {'dialog', 'Dialog', 'chatOptions'} for x in parts) and key not in {'dialog', 'Dialog'} and not value.startswith('dialog.'):
                return 'dungeon_text'
    if ext == 'json':
        if asset == 'quickbar/icons.json' and key == 'label':
            return 'interface'
        if asset.startswith('metagui/themes/') and key in {'name', 'description'} and len(parts) == 1:
            return 'interface'
        # Tiled map object display names are properties; object.name is an editor
        # label and must not be translated. Nested encoded parameters are handled
        # by embedded_json.py, not by this ordinary string field path.
        if asset.startswith('dungeons/') and isinstance(parent, dict):
            if key == 'value' and parent.get('name') == 'npcname':
                return 'dungeon_text'
            if len(parts) >= 2 and parts[-2] == 'properties' and key == 'npcname':
                return 'dungeon_text'

    if ext == 'namesource' and is_namegen_display_path(asset, parts):
        return 'generated_names'
    if ext != 'config':
        return None

    basename = Path(asset).name
    if asset.startswith('interface/') and key == 'description':
        return 'interface'
    # Configuration files referenced by in-game UI, separate from their images.
    if asset in {'_FUversioning.config', '_ZBversioning.config', '_FUcredits.config'} and key in {'changelog', 'welcome', 'credits', 'info'}:
        if value.startswith('/'):
            return None
        return 'information'
    if asset == 'client.config' and key == 'windowTitle':
        return 'interface'
    if asset == 'universe_server.config' and key == 'clientAssetsMismatchMessage':
        return 'interface'
    if asset == 'celestial.config' and (key == 'description' or key == 'regionName'):
        return 'worlds'
    if asset == 'system_objects.config' and key == 'description':
        return 'worlds'
    if asset == 'frackinship/configs/ships.config' and len(parts) == 2 and key == 'name':
        return 'interface'
    if asset == 'frackinship/configs/misc.config':
        if parts[0] == 'shipUnlockMessages':
            return 'interface'
        if parts[0] == 'shipResetSelectionInterfaceData':
            if key == 'text' or key == 'name' and 'buttons' in parts:
                return 'interface'
    if asset == 'interface/ai/ai.config' and key in {'defaultRecruitName', 'defaultRecruitDescription', 'missionBreadcrumbText', 'missionDeployText', 'crewBreadcrumbText'}:
        return 'interface'
    if asset == 'interface/cockpit/cockpit.config':
        if any(x in {'bookmarkButtonCaption', 'objectThreatText', 'exploredLabel'} for x in parts):
            return 'worlds'
        if key in {'newTitle', 'editTitle', 'threatTextPrefix'}:
            return 'worlds'
    if asset in {'interface/kukagps/planets.config', 'interface/kukagps/stars.config'} and len(parts) == 1:
        return 'worlds'
    if asset == 'interface/objectcrafting/fu_racialiser/fu_raceinfo.config':
        if len(parts) == 3 and parts[0] == 'raceInfo' and key in {'name', 'petName'}:
            return 'species'
    if asset == 'interface/objectcrafting/fu_pethouse/fu_pethouse.config' and len(parts) == 3 and parts[0] == 'interactionTypes' and key == 'name':
        return 'interface'
    if asset == 'interface/scripted/fm_musicplayer/musiclist.config' and len(parts) == 3 and key == 'name':
        return 'interface'
    if asset == 'interface/scripted/fu_planetsail/fu_planetsail.config' and p == 'shipStatus':
        return 'interface'
    if asset == 'interface/scripted/mechassembly/mechassemblygui.config' and len(parts) == 1 and key.endswith('Format'):
        return 'interface'
    if asset.startswith('interface/scripted/mmupgrade/') and parts[0] == 'upgrades' and key == 'description':
        return 'interface'
    if asset == 'interface/scripted/spaceStation/spaceStationData.config':
        if parts[0] == 'naming':
            return 'generated_names'
        if parts[0] == 'quests' and key in {'location', 'objective', 'time', 'reward'}:
            return 'quests'
    if asset == 'interface/scripted/spaceStation/texts.config' and len(parts) == 2 and key == 'scientificSpecial':
        return 'dialogue'
    if asset == 'interface/scripted/fu_lootbox/lootboxData.config':
        if key == 'description' or len(parts) == 3 and parts[0] == 'boxes' and key == 'name':
            return 'interface'
        if len(parts) == 4 and parts[:2] == ('loot', 'poolData') and key == 'name':
            return 'interface'
    if asset == 'interface/stats/stats.config' and key == 'label':
        return 'interface'
    if asset.startswith('interface/warping/'):
        if key == 'bookmarkName' or parts[0] == 'destinations' and key == 'name':
            return 'worlds'
    if asset == 'items/categories.config' and parts[0] == 'labels':
        return 'items'
    if asset == 'items/rotting.config' and len(parts) == 3 and parts[0] == 'rotTimeDescriptions' and key == '1':
        return 'items'
    if asset == 'items/buildscripts/buildsaplingfu.config' and len(parts) == 2 and parts[0] in {'stem', 'foliage'}:
        return 'items'
    if asset.startswith('dungeons/space/') and basename == 'parts.config' and key == 'description':
        return 'worlds'
    if asset == 'quests/generated/locations.config' and key == 'name':
        return 'quests'
    if asset.startswith('quests/generated/pools/') and key == 'name':
        return 'quests'
    if asset == 'quests/bounty/bounty.config' and parts[0] in {'prefix', 'suffix'}:
        return 'generated_names'
    if asset == 'quests/bounty/gang.config' and parts[0] in {'prefix', 'suffix', 'genericMid', 'hatPrefix'}:
        return 'generated_names'
    if asset == 'celestial/names.config' and is_namegen_display_path(asset, parts):
        return 'generated_names'
    if asset.startswith(('items/', 'species/')) and is_namegen_display_path(asset, parts):
        return 'generated_names'
    return None
