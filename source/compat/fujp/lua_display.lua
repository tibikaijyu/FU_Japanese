-- FU Japanese: translate values only at a display boundary.
-- Gameplay IDs, lookup keys, saved data, and unknown third-party values remain
-- unchanged. This module never wraps a game API or mutates its input values.
fujpDisplay = fujpDisplay or {}

local dictionaryState = "pending"
local dictionaryRevision = 0
local labelCache
local beeCache
local speciesCache = {}
local monsterCache = {}
local speciesFallbacks = {}
local monsterFallbacks = {}
local warned = {}

local function warnOnce(category, message)
  if warned[category] then return end
  warned[category] = true
  local logger = type(sb) == "table" and sb.logWarn
  if type(logger) == "function" then
    pcall(logger, "[FU_Japanese] " .. message)
  end
end

local function rootFunction(name)
  local apiRoot = root
  if type(apiRoot) ~= "table" then return nil end
  local fn = apiRoot[name]
  if type(fn) ~= "function" then return nil end
  return fn
end

local function normalizedSection(section)
  if type(section) ~= "table" then return nil end
  local normalized = {}
  for key, value in pairs(section) do
    if type(key) ~= "string" or type(value) ~= "string" then return nil end
    normalized[key] = value
    normalized[string.lower(key)] = value
  end
  return normalized
end

local function dictionaries()
  if dictionaryState == "ready" then return true end
  if dictionaryState == "failed" then return false end

  -- A missing root/API means this Lua environment may not be ready yet. Keep
  -- the pending state so a later display call can make the first load attempt.
  local assetJson = rootFunction("assetJson")
  if not assetJson then return false end

  local ok, labels, bees = pcall(function()
    local data = assetJson("/fujp/lua_display.config")
    if type(data) ~= "table" then return nil, nil end
    return normalizedSection(data.labels), normalizedSection(data.bee_subtypes)
  end)
  if not ok or type(labels) ~= "table" or type(bees) ~= "table" then
    dictionaryState = "failed"
    warnOnce("dictionary", "display dictionary could not be loaded or validated; using source text")
    return false
  end

  labelCache = labels
  beeCache = bees
  dictionaryState = "ready"
  dictionaryRevision = dictionaryRevision + 1
  return true
end

local function cachedOrRetry(cache, fallbacks, id, api)
  local value = cache[id]
  if value ~= nil then return true, value end

  local fallback = fallbacks[id]
  if fallback ~= nil then
    -- A missing API is still unavailable, not a reason to freeze the fallback.
    -- A replacement function is a new readiness boundary and may be retried.
    if api == nil or api == fallback.api then return true, fallback.value end
    fallbacks[id] = nil
  end
  return false, nil
end

local function cacheFallback(fallbacks, id, api, value)
  fallbacks[id] = {api = api, value = value}
end

function fujpDisplay.text(value)
  if type(value) ~= "string" then return value end
  if not dictionaries() then return value end
  return labelCache[value] or labelCache[string.lower(value)] or value
end

function fujpDisplay.beeSubtype(value)
  if type(value) ~= "string" then return value end
  if not dictionaries() then return value end
  return beeCache[value] or beeCache[string.lower(value)] or value
end

function fujpDisplay.species(id)
  if type(id) ~= "string" then return id end
  dictionaries()
  local assetJson = rootFunction("assetJson")
  local cached = speciesCache[id]
  if cached ~= nil then
    if cached.api ~= assetJson then
      speciesCache[id] = nil
    elseif cached.revision ~= dictionaryRevision then
      cached.value = fujpDisplay.text(cached.caption)
      cached.revision = dictionaryRevision
      return cached.value
    else
      return cached.value
    end
  end
  local found, value = cachedOrRetry({}, speciesFallbacks, id, assetJson)
  if found then return value end
  if not assetJson then return id end

  local ok, data = pcall(assetJson, "/species/" .. id .. ".species")
  if not ok then
    cacheFallback(speciesFallbacks, id, assetJson, id)
    warnOnce("species_api", "species display asset lookup failed; using source IDs")
    return id
  end

  local caption
  if type(data) == "table" then
    local tooltip = data.charCreationTooltip
    if type(tooltip) == "table" then
      caption = tooltip.title
      if caption ~= nil and type(caption) ~= "string" then
        warnOnce("species_data", "species display metadata has an invalid title; using source IDs")
      end
    elseif tooltip ~= nil then
      warnOnce("species_data", "species display metadata has an invalid tooltip; using source IDs")
    end
  elseif data ~= nil then
    warnOnce("species_data", "species display metadata has an invalid shape; using source IDs")
  end

  if type(caption) == "string" then
    local translated = fujpDisplay.text(caption)
    speciesCache[id] = {api=assetJson, caption=caption, value=translated,
                        revision=dictionaryRevision}
    return translated
  end

  -- A callable API has now returned a definitive result for this ID. Hold its
  -- raw fallback for this API function to avoid repeating a failing lookup on
  -- every display refresh. A missing API was never cached above.
  cacheFallback(speciesFallbacks, id, assetJson, id)
  return id
end

function fujpDisplay.monster(id)
  if type(id) ~= "string" then return id end
  dictionaries()
  local monsterParameters = rootFunction("monsterParameters")
  local alias = fujpDisplay.text(id)
  local cached = monsterCache[id]
  if cached ~= nil then
    if cached.api ~= monsterParameters then
      monsterCache[id] = nil
    elseif cached.revision ~= dictionaryRevision then
      cached.value = cached.caption and
        ((cached.caption:find("[\128-\255]") or alias == id) and
          fujpDisplay.text(cached.caption) or alias) or alias
      cached.revision = dictionaryRevision
      return cached.value
    else
      return cached.value
    end
  end
  local fallback = monsterFallbacks[id]
  if fallback ~= nil then
    if monsterParameters == nil or monsterParameters == fallback.api then return alias end
    monsterFallbacks[id] = nil
  end
  if not monsterParameters then return alias end

  local ok, data = pcall(monsterParameters, id)
  if not ok then
    cacheFallback(monsterFallbacks, id, monsterParameters, true)
    warnOnce("monster_api", "monster display metadata lookup failed; using source aliases")
    return alias
  end

  local caption
  if type(data) == "table" then
    caption = data.shortdescription
    if caption ~= nil and type(caption) ~= "string" then
      warnOnce("monster_data", "monster display metadata has an invalid shortdescription; using source aliases")
    end
  elseif data ~= nil then
    warnOnce("monster_data", "monster display metadata has an invalid shape; using source aliases")
  end

  -- Prefer translated asset metadata. Vanilla pets without a translated name
  -- use an explicit display alias; the original monster ID is never replaced.
  if type(caption) == "string" and (caption:find("[\128-\255]") or alias == id) then
    value = fujpDisplay.text(caption)
  else
    value = alias
  end
  if type(caption) == "string" then
    monsterCache[id] = {api=monsterParameters, caption=caption, value=value,
                        revision=dictionaryRevision}
  else
    cacheFallback(monsterFallbacks, id, monsterParameters, true)
  end
  return value
end
