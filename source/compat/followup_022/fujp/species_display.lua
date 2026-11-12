-- FU Japanese 0.2.2: display-only fallback for reviewed species information.
-- Keys remain internal species IDs. Unknown descriptions and Japanese text pass
-- through unchanged. Whitespace normalization never authorizes a partial match.
-- Starbound's require executes a script for side effects and returns nil.
fuJapaneseSpeciesDisplay = {}

local warned = {}
local cachedApi
local cacheReady = false
local speciesData

local function safeLog(method, message)
  pcall(function()
    if type(sb) == "table" and type(sb[method]) == "function" then
      sb[method](message)
    end
  end)
end

local function warnOnce(kind, message)
  if warned[kind] then return end
  warned[kind] = true
  safeLog("logWarn", message)
end

safeLog("logInfo", "[FU Japanese 0.2.2] Species display helper active")

local function isPlainTable(value)
  return type(value) == "table" and getmetatable(value) == nil
end

local function validArray(value, validateEntry)
  if not isPlainTable(value) then return false end
  local count, largest = 0, 0
  for key, entry in pairs(value) do
    if type(key) ~= "number" or key < 1 or key % 1 ~= 0 then return false end
    count = count + 1
    if key > largest then largest = key end
    if not validateEntry(entry) then return false end
  end
  return count == largest
end

local function validateDictionary(data)
  if not isPlainTable(data) or data.schemaVersion ~= 1 or not isPlainTable(data.species) then
    return nil
  end
  for race, entry in pairs(data.species) do
    if type(race) ~= "string" or race == "" or not isPlainTable(entry) then return nil end
    local function validCandidate(candidate)
      return isPlainTable(candidate) and type(candidate.source) == "string"
        and type(candidate.translation) == "string"
    end
    if not validArray(entry.descriptions, validCandidate)
      or not validArray(entry.names, validCandidate) then
      return nil
    end
  end
  return data.species
end

local function currentAssetJson()
  if type(root) ~= "table" then return nil end
  local assetJson = root.assetJson
  if type(assetJson) ~= "function" then return nil end
  return assetJson
end

local function getData()
  local assetJson = currentAssetJson()
  -- A missing root/API is a pending state, not a failed load. Do not poison the
  -- cache so a later FU initialization in this Lua state can load the config.
  if not assetJson then return nil end
  if cacheReady and cachedApi == assetJson then return speciesData end

  cachedApi = assetJson
  cacheReady = true
  speciesData = nil
  local ok, result = pcall(function()
    local value = assetJson("/fujp/species_display.config")
    local validated = validateDictionary(value)
    if not validated then error("invalid species display dictionary") end
    return validated
  end)
  if ok then
    speciesData = result
  else
    warnOnce("dictionary", "[FU Japanese] species display dictionary unavailable or invalid; source text preserved")
  end
  return speciesData
end

local function normalizeWhitespace(text)
  return (text:gsub("[ \t\r\n\f\v]+", " "):gsub("^ ", ""):gsub(" $", ""))
end

local function displayText(race, text, field)
  if type(race) ~= "string" or type(text) ~= "string" then return text end
  local data = getData()
  local entry = data and data[race]
  local candidates = type(entry) == "table" and entry[field]
  if type(candidates) ~= "table" then return text end
  local normalized = normalizeWhitespace(text)
  local whitespaceMatch
  for _, candidate in ipairs(candidates) do
    if text == candidate.source then return candidate.translation end
    if not whitespaceMatch and normalized == normalizeWhitespace(candidate.source) then
      whitespaceMatch = candidate.translation
    end
  end
  return whitespaceMatch or text
end

local function safelyDisplay(race, text, field)
  local ok, result = pcall(displayText, race, text, field)
  if ok then return result end
  warnOnce("conversion", "[FU Japanese] species display conversion failed; source text preserved")
  return text
end

function fuJapaneseSpeciesDisplay.description(race, text)
  return safelyDisplay(race, text, "descriptions")
end

function fuJapaneseSpeciesDisplay.name(race, text)
  return safelyDisplay(race, text, "names")
end
