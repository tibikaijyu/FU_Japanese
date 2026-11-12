-- Execute actual upstream/localized functions with small engine API fixtures.
-- Tests exercise saved IDs, callbacks, resource output, and numerical stats.
local assertions = 0
local cases = 0
local names = {}
local displayFallbackOnly = displayFallbackOnly == true
local function check(value, message)
  assertions = assertions + 1
  assert(value, message)
end
local function equal(a,b,message)
  check(a == b, (message or "not equal") .. ": " .. tostring(a) .. " ~= " .. tostring(b))
end
local function deepEqual(a,b,path)
  path = path or "value"
  equal(type(a),type(b),path.." type")
  if type(a) ~= "table" then equal(a,b,path); return end
  for k,v in pairs(a) do deepEqual(v,b[k],path.."."..tostring(k)) end
  for k in pairs(b) do check(a[k] ~= nil,path.." extra key "..tostring(k)) end
end
local function clone(t)
  if type(t) ~= "table" then return t end
  local out = {}
  for k,v in pairs(t) do out[k] = clone(v) end
  return out
end
local function contains(text, part)
  check(type(text) == "string" and text:find(part,1,true) ~= nil,"missing display text "..part)
  check(utf8.len(text) ~= nil,"invalid UTF-8 display text")
end
local function case(name, fn)
  if displayFallbackOnly and not name:match("^fallback_") then return end
  fn()
  cases = cases + 1
  names[#names+1] = name
end

local function environment(localized, overrides)
  local e = setmetatable({}, {__index=_G})
  e._G = e
  e.self = {}
  e.storage = {}
  e.root = {
    assetJson = function(path)
      if path == "/fujp/lua_display.config" then return clone(displayDictionaries) end
      error("unexpected fixture asset " .. tostring(path))
    end
  }
  e.util = {
    round = function(x,p) return math.floor(x*10^(p or 0)+0.5)/10^(p or 0) end,
    absolutePath = function(dir,p) return dir .. p end,
    mergeTable = function(a,b) for k,v in pairs(b) do a[k]=v end return a end
  }
  e.vec2 = {add=function(a,b) return {a[1]+b[1],a[2]+b[2]} end}
  e.copy = clone
  e.jarray = function() return {} end
  e.widget = {}
  e.world = {}
  e.object = {}
  e.config = {}
  e.sb = { logInfo=function()end, logWarn=function()end, logError=function()end }
  e.sb.replaceTags = function(text,tags)
    return (text:gsub("<([^>]+)>",function(key) return tags[key] or "<"..key..">" end))
  end
  e.require = function(path)
    if path == "/fujp/lua_display.lua" then
      if not e.fujpDisplay then
        local fn = assert(loadfile(localizedRoot..path,"t",e))
        fn()
      end
    end
  end
  if overrides then for k,v in pairs(overrides) do e[k]=v end end
  return e
end

local function loadScript(asset,localized,e)
  e = e or environment(localized)
  local path = (localized and localizedRoot or upstreamRoot).."/"..asset
  assert(loadfile(path,"t",e))()
  return e
end

case("fallback_apis_pending_then_recover_without_poisoning_cache",function()
  local e=environment(true)
  local warnings, dictionaryCalls = 0, 0
  e.sb.logWarn=function()warnings=warnings+1 end
  e.root=nil
  e.require("/fujp/lua_display.lua")
  equal(e.fujpDisplay.text("Oil"),"Oil")
  equal(e.fujpDisplay.beeSubtype("Honey"),"Honey")
  equal(e.fujpDisplay.species("human"),"human")
  equal(e.fujpDisplay.monster("petcat"),"petcat")
  equal(warnings,0,"missing root must not warn")

  e.root={}
  equal(e.fujpDisplay.text("Oil"),"Oil")
  equal(e.fujpDisplay.beeSubtype("Honey"),"Honey")
  equal(e.fujpDisplay.species("human"),"human")
  equal(e.fujpDisplay.monster("petcat"),"petcat")
  equal(warnings,0,"missing API functions must not warn")

  e.root={
    assetJson=function(path)
      if path=="/fujp/lua_display.config" then
        dictionaryCalls=dictionaryCalls+1
        return clone(displayDictionaries)
      elseif path=="/species/human.species" then
        return {charCreationTooltip={title="ヒューマン"}}
      end
      error("unexpected asset "..path)
    end,
    monsterParameters=function(id)
      if id=="petcat" then return {shortdescription="Cat"} end
      error("unknown monster")
    end
  }
  equal(e.fujpDisplay.text("Oil"),"石油")
  equal(e.fujpDisplay.species("human"),"ヒューマン")
  equal(e.fujpDisplay.monster("petcat"),"ネコ")
  equal(dictionaryCalls,1,"dictionary should load once after API appears")
  equal(warnings,0,"normal recovery must not warn")
end)

case("fallback_malformed_dictionaries_fail_once_and_fall_back",function()
  local malformed={}
  local broken=clone(displayDictionaries); broken.labels="not a table"; malformed[#malformed+1]=broken
  broken=clone(displayDictionaries); broken.bee_subtypes=false; malformed[#malformed+1]=broken
  broken=clone(displayDictionaries); broken.labels=nil; malformed[#malformed+1]=broken
  broken=clone(displayDictionaries); broken.labels[17]="numeric key"; malformed[#malformed+1]=broken
  broken=clone(displayDictionaries); broken.labels.Oil={"table value"}; malformed[#malformed+1]=broken
  broken=clone(displayDictionaries); broken.bee_subtypes[false]="boolean key"; malformed[#malformed+1]=broken
  broken=clone(displayDictionaries); broken.bee_subtypes.Honey=42; malformed[#malformed+1]=broken

  for index, dictionary in ipairs(malformed) do
    local e=environment(true)
    local warnings, calls = 0, 0
    e.sb.logWarn=function()warnings=warnings+1 end
    e.root.assetJson=function(path)
      calls=calls+1
      equal(path,"/fujp/lua_display.config")
      return clone(dictionary)
    end
    e.require("/fujp/lua_display.lua")
    equal(e.fujpDisplay.text("Oil"),"Oil","malformed labels fallback "..index)
    equal(e.fujpDisplay.beeSubtype("Honey"),"Honey","malformed bee fallback "..index)
    equal(e.fujpDisplay.text("Oil"),"Oil","failed dictionary remains safe "..index)
    equal(calls,1,"prepared malformed dictionary must not retry "..index)
    equal(warnings,1,"dictionary warning must be limited "..index)
  end
end)

case("fallback_species_and_monster_failures_are_cached_until_api_replaced",function()
  local e=environment(true)
  local warnings, speciesCalls, monsterCalls = {}, 0, 0
  e.sb.logWarn=function(message)warnings[message]=true end
  e.root.assetJson=function(path)
    if path=="/fujp/lua_display.config" then return clone(displayDictionaries) end
    if path=="/species/broken.species" then
      speciesCalls=speciesCalls+1
      error("broken species asset")
    end
    if path=="/species/malformed.species" then
      return {charCreationTooltip={title=42}}
    end
    error("unexpected asset "..path)
  end
  e.root.monsterParameters=function(id)
    monsterCalls=monsterCalls+1
    if id=="petcat" then error("broken monster asset") end
    if id=="malformedPet" then return {shortdescription={}} end
    error("unknown monster")
  end
  e.require("/fujp/lua_display.lua")
  equal(e.fujpDisplay.text("Oil"),"石油") -- load dictionaries before API failure fixtures
  for _=1,25 do
    equal(e.fujpDisplay.species("broken"),"broken")
    equal(e.fujpDisplay.monster("petcat"),"ネコ")
  end
  equal(speciesCalls,1,"same species ID must not retry a prepared failing API")
  equal(monsterCalls,1,"same monster ID must not retry a prepared failing API")
  equal(#(function()local out={} for _ in pairs(warnings)do out[#out+1]=true end return out end)(),2,
    "species and monster failures each warn once")

  -- A new API function is an explicit readiness boundary; cached fallbacks
  -- from the old function are discarded and the same IDs can recover.
  local previousAssetJson=e.root.assetJson
  e.root.assetJson=function(path)
    if path=="/fujp/lua_display.config" then return clone(displayDictionaries) end
    if path=="/species/broken.species" then return {charCreationTooltip={title="ヒューマン"}} end
    if path=="/species/malformed.species" then return {charCreationTooltip={title=42}} end
    return previousAssetJson(path)
  end
  equal(e.fujpDisplay.species("broken"),"ヒューマン")
  equal(e.fujpDisplay.species("malformed"),"malformed")
  local previousMonsterParameters=e.root.monsterParameters
  e.root.monsterParameters=function(id)
    if id=="petcat" then return {shortdescription="Cat"} end
    if id=="malformedPet" then return {shortdescription={}} end
    return previousMonsterParameters(id)
  end
  equal(e.fujpDisplay.monster("petcat"),"ネコ")
  equal(e.fujpDisplay.monster("malformedPet"),"malformedPet")
  equal(warnings["[FU_Japanese] species display asset lookup failed; using source IDs"],true)
  equal(warnings["[FU_Japanese] monster display metadata lookup failed; using source aliases"],true)
  equal(warnings["[FU_Japanese] species display metadata has an invalid title; using source IDs"],true)
  equal(warnings["[FU_Japanese] monster display metadata has an invalid shortdescription; using source aliases"],true)
end)

case("fallback_monster_partial_readiness_retries_dictionary_without_api_retry",function()
  local e=environment(true)
  local apiCalls=0
  e.root={monsterParameters=function(id)
    apiCalls=apiCalls+1
    return {shortdescription="後発caption"}
  end}
  e.require("/fujp/lua_display.lua")
  equal(e.fujpDisplay.monster("petdog"),"後発caption","pending dictionary uses raw caption temporarily")
  equal(apiCalls,1)

  e.root.assetJson=function(path)
    if path=="/fujp/lua_display.config" then
      local dictionary=clone(displayDictionaries)
      dictionary.labels["後発caption"]="JP-Dog"
      return dictionary
    end
    error("unexpected asset "..path)
  end
  equal(e.fujpDisplay.monster("petdog"),"JP-Dog","cached metadata is re-rendered after dictionary readiness")
  equal(apiCalls,1,"successful monster metadata is not fetched again")
end)

case("fallback_monster_pending_alias_failure_retranslates_without_retry",function()
  local e=environment(true)
  local apiCalls,warnings=0,0
  e.sb.logWarn=function()warnings=warnings+1 end
  e.root={monsterParameters=function()
    apiCalls=apiCalls+1
    error("confirmed API failure")
  end}
  e.require("/fujp/lua_display.lua")
  equal(e.fujpDisplay.monster("petdog"),"petdog","pending dictionary alias is raw temporarily")
  equal(e.fujpDisplay.monster("petdog"),"petdog")
  equal(apiCalls,1,"confirmed API error is suppressed for the same function")
  equal(warnings,1,"API warning is finite")

  e.root.assetJson=function(path)
    if path=="/fujp/lua_display.config" then
      local dictionary=clone(displayDictionaries)
      dictionary.labels.petdog="JP-Pet-Dog"
      return dictionary
    end
    error("unexpected asset "..path)
  end
  equal(e.fujpDisplay.monster("petdog"),"JP-Pet-Dog","cached failure alias is recomputed after dictionary readiness")
  equal(apiCalls,1,"dictionary recovery does not retry confirmed failing API")
  equal(warnings,1,"dictionary recovery does not repeat warning")
end)

case("fallback_monster_caption_pending_dictionary_retranslates_without_api_retry",function()
  local e=environment(true)
  local apiCalls=0
  e.root={monsterParameters=function()
    apiCalls=apiCalls+1
    return {shortdescription="後発caption"}
  end}
  e.require("/fujp/lua_display.lua")
  equal(e.fujpDisplay.monster("petdog"),"後発caption")
  e.root.assetJson=function(path)
    if path=="/fujp/lua_display.config" then
      local dictionary=clone(displayDictionaries)
      dictionary.labels["後発caption"]="犬"
      return dictionary
    end
    error("unexpected asset "..path)
  end
  equal(e.fujpDisplay.monster("petdog"),"犬","caption translation becomes visible after dictionary readiness")
  equal(apiCalls,1,"cached caption avoids a second metadata API call")
end)

case("fallback_non_string_ids_and_utf8_values_are_preserved",function()
  local e=environment(true)
  e.require("/fujp/lua_display.lua")
  equal(e.fujpDisplay.species(nil),nil)
  equal(e.fujpDisplay.species(12),12)
  equal(e.fujpDisplay.monster(false),false)
  equal(e.fujpDisplay.text("日本語の原文"),"日本語の原文")
  equal(utf8.len(e.fujpDisplay.text("Oil"))~=nil,true)
  equal(e.fujpDisplay.beeSubtype("futureBee"),"futureBee")
end)

case("fallback_does_not_suppress_original_builder_exceptions",function()
  local e=environment(true)
  local originalCalls=0
  e.root.generateName=function()
    originalCalls=originalCalls+1
    error("upstream builder failure")
  end
  e.setupAbility=function()end
  e.randomFromList=function(values)return values[1]end
  e.replacePatternInData=function()end
  loadScript("items/buildscripts/buildweapon.lua",true,e)
  local ok, err=pcall(e.build,"/items/",{builderConfig={{nameGenerator="/names.config"}}},{},1,1)
  equal(ok,false,"original builder exception must still propagate")
  check(tostring(err):find("upstream builder failure",1,true)~=nil,"original error changed")
  equal(originalCalls,1,"original builder API must be called once")
end)

case("display_lookup_preserves_unknown_values_and_types",function()
  local e = environment(true)
  e.require("/fujp/lua_display.lua")
  equal(e.fujpDisplay.text(nil),nil)
  equal(e.fujpDisplay.text(42),42)
  equal(e.fujpDisplay.text(false),false)
  equal(e.fujpDisplay.text("thirdPartyCallback"),"thirdPartyCallback")
  equal(e.fujpDisplay.text("日本語の名前"),"日本語の名前")
  equal(e.fujpDisplay.text("Oil"),"石油")
  equal(e.fujpDisplay.text("Mech fuel"),"メック燃料")
  deepEqual(e.storage,{})
end)

case("all_bee_subtype_aliases_and_ascii_case",function()
  local e = environment(true)
  e.require("/fujp/lua_display.lua")
  for name, expected in pairs(displayDictionaries.bee_subtypes) do
    equal(e.fujpDisplay.beeSubtype(name),expected)
    equal(e.fujpDisplay.beeSubtype(name:gsub("^%l",string.upper)),expected)
    check(utf8.len(expected) ~= nil,"invalid bee subtype UTF-8")
  end
  equal(e.fujpDisplay.beeSubtype("futureBee"),"futureBee")
end)

case("species_and_pet_metadata_fallback",function()
  local e = environment(true)
  local baseAsset=e.root.assetJson
  e.root.assetJson=function(path)
    if path == "/species/human.species" then return {charCreationTooltip={title="ヒューマン"}} end
    return baseAsset(path)
  end
  e.root.monsterParameters=function(id)
    if id == "petcat" then return {shortdescription="Cat"} end
    if id == "newPet" then return {shortdescription="新しいペット"} end
    error("not found")
  end
  e.require("/fujp/lua_display.lua")
  equal(e.fujpDisplay.species("human"),"ヒューマン")
  equal(e.fujpDisplay.species("thirdPartySpecies"),"thirdPartySpecies")
  equal(e.fujpDisplay.monster("petcat"),"ネコ")
  equal(e.fujpDisplay.monster("newPet"),"新しいペット")
  equal(e.fujpDisplay.monster("thirdPartyPet"),"thirdPartyPet")
end)

case("space_station_buttons_keep_command_ids",function()
  local results={}
  for _,localized in ipairs({false,true}) do
    local e=environment(localized)
    local out={texts={},data={},visible={},enabled={}}
    e.widget.setText=function(k,v)out.texts[k]=v end
    e.widget.setData=function(k,v)out.data[k]=v end
    e.widget.setVisible=function(k,v)out.visible[k]=v end
    e.widget.setButtonEnabled=function(k,v)out.enabled[k]=v end
    loadScript("interface/scripted/spaceStation/spaceStation.lua",localized,e)
    e.modifyButtons("Accept",{"独自の表示文","payload_command"},"Med Brochure",false,nil,"Back")
    results[#results+1]=out
  end
  deepEqual(results[1].data,results[2].data,"station command payloads")
  deepEqual(results[1].visible,results[2].visible,"station visibility")
  deepEqual(results[1].enabled,results[2].enabled,"station enabled state")
  equal(results[2].texts.button1,"引き受ける")
  equal(results[2].texts.button2,"独自の表示文")
  equal(results[2].texts.button3,"医療案内")
  equal(results[2].texts.button6,"戻る")
  equal(results[2].data.button1,"Accept")
  equal(results[2].data.button2,"payload_command")
  equal(results[2].data.button3,"Med Brochure")
  equal(results[2].texts.button5,nil)
end)

case("fuel_caption_keeps_fuel_type_id",function()
  local e=environment(true)
  local out={}
  e.widget.setText=function(k,v)out[k]=v end
  e.self.fuelTypes={Oil={textColor="yellow"},["Mech fuel"]={textColor="cyan"}}
  loadScript("interface/mechfuel/mechfuel.lua",true,e)
  e.setFuelTypeText("Oil")
  equal(out.lblFuelType,"現在の燃料：^yellow;石油")
  e.setFuelTypeText("Mech fuel")
  equal(out.lblFuelType,"現在の燃料：^cyan;メック燃料")
  e.setFuelTypeText(nil)
  equal(out.lblFuelType,"現在の燃料：^red;空^reset;")
  equal(e.self.fuelTypes.Oil.textColor,"yellow")
  equal(e.self.fuelTypes["Mech fuel"].textColor,"cyan")
  equal(e.self.fuelTypes["石油"],nil)
end)

case("sapling_names_leave_tree_asset_ids_unchanged",function()
  local e=environment(true)
  local baseAsset=e.root.assetJson
  e.root.assetJson=function(path)
    if path == "/items/buildscripts/buildsaplingfu.config" then
      return {stem={pineytree="松"},foliage={pinefoliage="針葉"}}
    end
    return baseAsset(path)
  end
  e.root.treeStemDirectory=function(id)equal(id,"pineytree");return "/trees/pine/" end
  e.root.treeFoliageDirectory=function(id)equal(id,"pinefoliage");return "/trees/leaves/" end
  loadScript("items/buildscripts/buildsapling.lua",true,e)
  local cfg,params=e.build("/items/",{}, {stemName="pineytree",foliageName="pinefoliage",stemHueShift=15,foliageHueShift=25},1,1)
  equal(params.stemName,"pineytree")
  equal(params.foliageName,"pinefoliage")
  equal(params.stemHueShift,15)
  equal(params.foliageHueShift,25)
  contains(params.shortdescription,"松")
  contains(params.shortdescription,"の苗木")
  contains(params.description,"針葉")
  contains(params.description,"松")
  check(not params.description:find("pineytree",1,true),"raw tree id leaked into sapling display")
  contains(cfg.inventoryIcon[1].image,"/trees/pine/saplingicon.png")
  contains(cfg.inventoryIcon[2].image,"/trees/leaves/saplingicon.png")
end)

local function beeFixture(localized,workTime,inspected)
  local e=environment(localized)
  local baseAsset=e.root.assetJson
  e.root.assetJson=function(path)
    if path == "/bees/beeData.config" then return {stats={honey={{name="honey"}}}} end
    return baseAsset(path)
  end
  e.root.itemHasTag=function()return false end
  e.genelib={returnFullGenomeStats=function()
    return {subtype=1,workTime=workTime,baseProduction=6,droneToughness=4,queenLifespan=8}
  end}
  loadScript("bees/beeBuilder.lua",localized,e)
  return e.build("/bees/",{itemName="bee_honey_drone",inventoryIcon="/bee.png"},
                 {genome="01234567",genomeInspected=inspected,wild=true},1,1)
end
for _,period in ipairs({"day","night","both"}) do
  case("bee_builder_"..period.."_keeps_genome_and_stats",function()
    local original,originalParams=beeFixture(false,period,true)
    local translated,translatedParams=beeFixture(true,period,true)
    deepEqual(originalParams,translatedParams,"bee parameters")
    equal(translated.tooltipFields.subTitle,"亜種：ミツバチ")
    equal(translated.tooltipFields.workTimeLabel,({day="昼",night="夜",both="昼夜"})[period])
    equal(original.tooltipFields.baseProductionLabel,translated.tooltipFields.baseProductionLabel)
    equal(original.tooltipFields.droneToughnessLabel,translated.tooltipFields.droneToughnessLabel)
    equal(original.tooltipFields.queenLifespanLabel,translated.tooltipFields.queenLifespanLabel)
    equal(translated.itemName,"bee_honey_drone")
    contains(translated.tooltipFields.genomeLabel,"ゲノム：")
    equal(translated.tooltipFields.objectImage,"/interface/tooltips/wildImage.png")
  end)
end

case("bee_builder_unidentified_state",function()
  local cfg,params=beeFixture(true,"day",false)
  equal(cfg.tooltipFields.subTitle,"不明な亜種")
  equal(cfg.tooltipFields.genomeLabel,"^gray;未鑑定のハチ")
  equal(cfg.tooltipFields.baseProductionLabel,"???")
  equal(params.genome,"01234567")
end)

case("bee_frame_description_retains_numeric_effects",function()
  local e=loadScript("items/buildscripts/buildbeeframe.lua",true)
  local cfg=e.build("/items/",{
    description="効果：<beeData>",baseProduction=4,droneToughness=-2,
    queenLifespan=20,mutationChance=15,radResistance=1,allowNight=true
  },{},1,1)
  contains(cfg.description,"基礎生産量: ^green;+4^reset;")
  contains(cfg.description,"雄バチの頑強さ: ^red;-2^reset;")
  contains(cfg.description,"突然変異の確率: ^green;+15^reset;^green;%^reset;")
  contains(cfg.description,"夜間に生産")
  contains(cfg.description,"放射線")
  equal(cfg.baseProduction,4)
  equal(cfg.droneToughness,-2)
  equal(cfg.mutationChance,15)
end)

case("armor_description_keeps_stats_and_class_tags",function()
  local results={}
  for _,localized in ipairs({false,true}) do
    local e=environment(localized)
    e.root.evalFunction=function()return 1 end
    loadScript("items/buildscripts/fubuildarmor.lua",localized,e)
    local cfg,params=e.build("/items/",{
      description="装甲",shortdescription="防具",inventoryIcon="/armor.png",rarity="rare",price=100,
      upgrades=1,itemTags={"defensive","ranged","explorer"},
      leveledStatusEffects={{stat="physicalResistance",amount=0.2,levelFunction="armor"},
                            {stat="fireResistance",amount=-0.1,levelFunction="armor"}}
    },{level=4},4,1)
    results[#results+1]={cfg,params}
  end
  deepEqual(results[1][2],results[2][2],"armor parameters")
  deepEqual(results[1][1].leveledStatusEffects,results[2][1].leveledStatusEffects,"armor effects")
  deepEqual(results[1][1].itemTags,results[2][1].itemTags,"armor class tags")
  equal(results[1][1].tooltipFields.physicalResLabel,results[2][1].tooltipFields.physicalResLabel)
  equal(results[1][1].tooltipFields.fireResLabel,results[2][1].tooltipFields.fireResLabel)
  equal(results[2][1].rarity,"rare")
  contains(results[2][1].description,"耐性：")
  contains(results[2][1].description,"防御型")
  contains(results[2][1].description,"遠距離")
  contains(results[2][1].description,"探索型")
end)

case("boomerang_display_alias_does_not_change_damage_or_asset_ids",function()
  local results={}
  for _,localized in ipairs({false,true}) do
    local e=environment(localized)
    e.setupAbility=function()end
    e.root.evalFunction=function()return 2 end
    e.replacePatternInData=function(cfg,unused,tag,value)
      for k,v in pairs(cfg) do if type(v)=="string" then cfg[k]=v:gsub(tag,function()return value end) end end
    end
    loadScript("items/buildscripts/buildboomerang.lua",localized,e)
    local cfg,params=e.build("/items/",{elementalType="fire",price=25,
      description="<elementalName> 属性",scriptTag="<elementalType>",projectileParameters={power=12,maxDistance=20}},
      {category="boomerang",level=3},3,1)
    results[#results+1]={cfg,params}
  end
  deepEqual(results[1][2],results[2][2],"weapon parameters")
  equal(results[2][1].elementalType,"fire")
  equal(results[2][1].scriptTag,"fire")
  equal(results[2][1].tooltipFields.damageKindImage,"/interface/elements/fire.png")
  equal(results[2][1].tooltipFields.subtitle,"ブーメラン")
  equal(results[2][1].tooltipFields.maxDamageLabel,24)
  equal(results[2][1].price,50)
  equal(results[2][1].description,"炎 属性")
  deepEqual(results[1][1].projectileParameters,results[2][1].projectileParameters)
end)

case("food_display_keeps_aging_and_food_values",function()
  local e=environment(true)
  e.root.assetJson=function(path)
    if path == "/items/rotting.config:baseTimeToRot" then return 300 end
    if path == "/items/rotting.config:rotTimeDescriptions" then return {{100,"傷みかけ"},{1000,"新鮮"}} end
    error(path)
  end
  loadScript("items/buildscripts/buildfood.lua",true,e)
  local cfg,params=e.build("/items/",{itemAgingScripts={},rottingMultiplier=2,foodValue=35},{},1,1)
  equal(params.timeToRot,600)
  equal(cfg.foodValue,35)
  equal(cfg.tooltipFields.foodValueLabel,"食料値：^green;35^reset;")
  equal(cfg.tooltipFields.rotTimeLabel,"新鮮")
end)

case("well_water_items_and_storage_unchanged",function()
  for _,amount in ipairs({0,30,150,250,350,450,550,650}) do
    local out={}
    for _,localized in ipairs({false,true}) do
      local e=environment(localized)
      local calls={}
      e.object.position=function()return {10,20} end
      e.object.say=function(text)calls.said=text end
      e.world.spawnItem=function(id,pos,count) calls.spawn={id,pos,count} end
      e.storage.waterCount=amount
      loadScript("objects/crafting/farmwell/farmwell.lua",localized,e)
      e.onInteraction({})
      calls.water=e.storage.waterCount
      out[#out+1]=calls
    end
    deepEqual(out[1].spawn,out[2].spawn,"well spawn")
    equal(out[1].water,out[2].water,"well stored water")
    if out[2].said then
      contains(out[2].said,"水量：")
      equal(out[1].said:match("%d+"),out[2].said:match("%d+"))
    end
  end
end)

case("gps_time_and_calendar_numbers_unchanged",function()
  for _,time in ipairs({0,0.1,0.3,0.5,0.9}) do
    local results={}
    for _,localized in ipairs({false,true}) do
      local e=environment(localized)
      e.world.timeOfDay=function()return time end
      loadScript("interface/kukagps/kukagps.lua",localized,e)
      results[#results+1]={e.timeConversion(),e.getDate(400)}
    end
    equal(results[1][1]:match("%d+:%d+"),results[2][1]:match("%d+:%d+"))
    check(results[2][1]:find("午前",1,true) or results[2][1]:find("午後",1,true),"AM/PM still English")
    local a,b={},{}
    for n in results[1][2]:gmatch("%d+")do a[#a+1]=n end
    for n in results[2][2]:gmatch("%d+")do b[#b+1]=n end
    deepEqual(a,b,"calendar numbers")
  end
end)

case("ship_pet_list_keeps_selection_and_portrait_ids",function()
  local e=environment(true)
  local values={text={},data={},images={}}
  local i=0
  e.petList={petcat="catSpawner",petdog="dogSpawner"}
  e.containerId=5
  e.petParams={}
  e.root.itemConfig=function()return {config={}} end
  e.root.monsterParameters=function()return {} end
  e.root.monsterPortrait=function(id) return {{image="/portraits/"..id..".png"}} end
  e.world.getObjectParameter=function()return "petcat" end
  e.widget.clearListItems=function()end
  e.widget.addListItem=function()i=i+1;return tostring(i)end
  e.widget.setText=function(k,v)values.text[k]=v end
  e.widget.setData=function(k,v)values.data[k]=v end
  e.widget.setImage=function(k,v)values.images[k]=v end
  e.widget.setListSelected=function(k,v)values.selected={k,v} end
  loadScript("interface/objectcrafting/fu_pethouse/fu_pethouse.lua",true,e)
  e.populateList()
  equal(values.text["petList.petList.1.name"],"ネコ")
  equal(values.text["petList.petList.2.name"],"イヌ")
  equal(values.data["petList.petList.1"].pet,"petcat")
  equal(values.data["petList.petList.2"].pet,"petdog")
  equal(values.images["petList.petList.1.icon"],"/portraits/petcat.png")
  equal(values.images["petList.petList.2.icon"],"/portraits/petdog.png")
  equal(values.selected[2],"1")
end)

case("atmosphere_condenser_keeps_weight_keys",function()
  local e=environment(true)
  local outputs={default={{weight="common",items={"water"}},
                         {weight="uncommon",items={"oil"}},
                         {weight="rare",items={"helium"}}}}
  e.self={rarityInfoLevel=3,overrideScanTooltip=true}
  e.wellRange=30
  e.wellsDrawing=2
  e.world.type=function()return "default"end
  e.config.getParameter=function(k)if k=="outputs"then return outputs end end
  e.root.itemConfig=function(id)return {config={shortdescription=({water="水",oil="石油",helium="ヘリウム"})[id]}}end
  e.object.setConfigParameter=function(k,v)e.display=v end
  loadScript("objects/power/isn_atmoscondenser/isn_resource_generator.lua",true,e)
  e.setDesc()
  contains(e.display,"一般")
  contains(e.display,"やや希少")
  contains(e.display,"希少")
  contains(e.display,"水")
  contains(e.display,"石油")
  contains(e.display,"ヘリウム")
  equal(outputs.default[1].weight,"common")
  equal(outputs.default[2].weight,"uncommon")
  equal(outputs.default[3].weight,"rare")
end)

case("quest_bitmap_title_overlays_preserve_quest_ids_and_navigation",function()
  local original,localized
  for _,translated in ipairs({false,true})do
    local e=environment(translated)
    local out={texts={},data={},images={},visible={},enabled={},saved={},nextItem=0}
    e.widget.setText=function(k,v)out.texts[k]=v end
    e.widget.setData=function(k,v)out.data[k]=v end
    e.widget.getData=function(k)return out.data[k]end
    e.widget.setImage=function(k,v)out.images[k]=v end
    e.widget.setVisible=function(k,v)out.visible[k]=v end
    e.widget.setButtonEnabled=function(k,v)out.enabled[k]=v end
    e.widget.addListItem=function()out.nextItem=out.nextItem+1;return tostring(out.nextItem)end
    e.widget.clearListItems=function()end
    e.widget.getListSelected=function()return "1"end
    e.widget.active=function(k)return k=="questlineList"end
    e.status={statusProperty=function()return "alpha;"end,
              setStatusProperty=function(k,v)out.saved[k]=v end}
    e.player={hasCompletedQuest=function()return false end}
    loadScript("zb/questList/questList.lua",translated,e)
    e.GD={unavailableQuestlineString="unavailable"}
    e.QD={current={},lines={{id="alpha",sublines={}},{id="beta",requirements={"unlock"}},
                           {id="secret",secret=true,requirements={"unlock"}}},
          strings={questlines={alpha={title="採掘の基礎"},beta={title="研究の入門"}}}}
    e.populateQueslineList()
    equal(out.nextItem,2,"unavailable and secret questline handling")
    e.populateQuestList=function()out.populated=true end
    e.questButton()
    equal(e.QD.current.line,"alpha")
    equal(out.populated,true)
    if translated then
      equal(out.texts["questlineList.list.1.fuJapaneseBannerTitle"],"採掘の基礎")
      equal(out.texts["questlineList.list.2.fuJapaneseBannerTitle"],"^gray;研究の入門^reset;")
      equal(out.texts.fuJapaneseQuestlineTitle,"採掘の基礎")
      equal(out.visible.fuJapaneseQuestlineTitle,true)
      equal(out.visible.fuJapaneseQuestlineCover,true)
    end
    e.questlineButton()
    if translated then
      equal(out.texts.fuJapaneseQuestlineTitle,"")
      equal(out.visible.fuJapaneseQuestlineTitle,false)
      equal(out.visible.fuJapaneseQuestlineCover,false)
      localized=out
    else original=out end
  end
  deepEqual(original.data,localized.data,"questline selection IDs")
  deepEqual(original.images,localized.images,"questline banner image IDs")
  deepEqual(original.saved,localized.saved,"quest completion status")
  deepEqual(original.enabled,localized.enabled,"quest navigation controls")
  equal(localized.data["questlineList.list.1.banner"],"alpha")
  equal(localized.data["questlineList.list.2.banner"],"unavailable_beta")
end)

case("format_strings_accept_original_argument_types",function()
  for _,fixture in ipairs(formatFixtures) do
    local ok, original=pcall(string.format,fixture.source,table.unpack(fixture.args))
    check(ok,"invalid upstream format fixture")
    local ok2, translated=pcall(string.format,fixture.target,table.unpack(fixture.args))
    check(ok2,"translated format does not accept original argument types")
    check(utf8.len(translated) ~= nil,"format output invalid UTF-8")
    local a,b={},{}
    for n in original:gmatch("%d+%.?%d*")do a[#a+1]=n end
    for n in translated:gmatch("%d+%.?%d*")do b[#b+1]=n end
    deepEqual(a,b,"formatted numerical values")
  end
end)

local encodedNames={}
for index, name in ipairs(names) do encodedNames[index]='"'..name..'"' end
luaLocalizationReport = '{"cases":'..cases..',"assertions":'..assertions..',"case_names":['..
  table.concat(encodedNames,",")..'],"runtime":"'.._VERSION..'","status":"passed"}'
