-- FU Japanese: translate values only at a display boundary.
-- Gameplay IDs, lookup keys, saved data, and unknown third-party values remain
-- unchanged. This module never wraps a game API or mutates its input values.
fujpDisplay = fujpDisplay or {}
local labelCache
local beeCache
local speciesCache = {}
local monsterCache = {}

local function dictionaries()
  if not labelCache then
    labelCache, beeCache = {}, {}
    local ok, data = pcall(root.assetJson, "/fujp/lua_display.config")
    if ok and type(data) == "table" then
      for key, value in pairs(data.labels or {}) do
        labelCache[key] = value
        labelCache[string.lower(key)] = value
      end
      for key, value in pairs(data.bee_subtypes or {}) do
        beeCache[key] = value
        beeCache[string.lower(key)] = value
      end
    end
  end
end

function fujpDisplay.text(value)
  if type(value) ~= "string" then return value end
  dictionaries()
  return labelCache[value] or labelCache[string.lower(value)] or value
end

function fujpDisplay.beeSubtype(value)
  if type(value) ~= "string" then return value end
  dictionaries()
  return beeCache[value] or beeCache[string.lower(value)] or value
end

function fujpDisplay.species(id)
  if type(id) ~= "string" then return id end
  if speciesCache[id] then return speciesCache[id] end
  local ok, data = pcall(root.assetJson, "/species/" .. id .. ".species")
  local caption = ok and type(data) == "table" and data.charCreationTooltip
  caption = type(caption) == "table" and caption.title
  speciesCache[id] = type(caption) == "string" and caption or id
  return speciesCache[id]
end

function fujpDisplay.monster(id)
  if type(id) ~= "string" then return id end
  if monsterCache[id] then return monsterCache[id] end
  local ok, data = pcall(root.monsterParameters, id)
  local caption = ok and type(data) == "table" and data.shortdescription
  -- Prefer translated asset metadata. Vanilla pets without a translated name
  -- use an explicit display alias; the original monster ID is never replaced.
  local alias = fujpDisplay.text(id)
  if type(caption) == "string" and (caption:find("[\128-\255]") or alias == id) then
    monsterCache[id] = fujpDisplay.text(caption)
  else
    monsterCache[id] = alias
  end
  return monsterCache[id]
end
