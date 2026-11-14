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

local function tableKind(value)
  if type(value) ~= "table" then return nil end
  local mt = getmetatable(value)
  if mt == nil then return "plain" end
  if type(mt) ~= "table" then return nil end
  local count = 0
  for key in next, mt do
    if key ~= "__typehint" and key ~= "__nils" and key ~= "__newindex" then return nil end
    count = count + 1
  end
  if count ~= 3 then return nil end
  local hint, nils, newindex = rawget(mt, "__typehint"), rawget(mt, "__nils"), rawget(mt, "__newindex")
  if (hint ~= 1 and hint ~= 2) or type(nils) ~= "table" or getmetatable(nils) ~= nil
    or type(newindex) ~= "function" then return nil end
  return hint == 1 and "array" or "object", nils
end

local function isObject(value, allowNulls)
  local kind, nils = tableKind(value)
  return kind == "plain" or (kind == "object" and (allowNulls or next(nils) == nil))
end

local function isArray(value, allowNulls)
  local kind, nils = tableKind(value)
  return kind == "plain" or (kind == "array" and (allowNulls or next(nils) == nil))
end

local function validArray(value, validateEntry)
  if not isArray(value) then return false end
  local count, largest = 0, 0
  for key, entry in next, value do
    if type(key) ~= "number" or key < 1 or key % 1 ~= 0 then return false end
    count = count + 1
    if key > largest then largest = key end
    if not validateEntry(entry) then return false end
  end
  return count == largest
end

local function validateDictionary(data)
  if not isObject(data) then return nil, "root is not an object" end
  local species = rawget(data, "species")
  if rawget(data, "schemaVersion") ~= 1 or not isObject(species) then
    return nil, "schemaVersion/species shape is invalid"
  end
  for race, entry in next, species do
    if type(race) ~= "string" or race == "" or not isObject(entry) then return nil, "species entry is invalid" end
    local function validCandidate(candidate)
      return isObject(candidate) and type(rawget(candidate, "source")) == "string"
        and type(rawget(candidate, "translation")) == "string"
    end
    if not validArray(rawget(entry, "descriptions"), validCandidate)
      or not validArray(rawget(entry, "names"), validCandidate) then
      return nil, "species candidates have an invalid shape"
    end
  end
  return species
end

local function safeCause(value)
  if type(value) ~= "string" then return "non-string error" end
  local ok, result = pcall(function()
    local cleaned, parts, bytes = value:gsub("[%c]", " "), {}, 0
    for _, codepoint in utf8.codes(cleaned) do
      local character = utf8.char(codepoint)
      if bytes + #character > 160 then break end
      parts[#parts + 1] = character
      bytes = bytes + #character
    end
    return table.concat(parts)
  end)
  return ok and result or "unreadable error"
end

local function currentAssetJson()
  if type(root) ~= "table" then return nil end
  local assetJson = rawget(root, "assetJson")
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
  local loaded, value = pcall(assetJson, "/fujp/species_display.config")
  if not loaded then
    warnOnce("dictionary", "[FU Japanese] /fujp/species_display.config load failed (" .. safeCause(value) .. "); source text preserved")
  else
    local checked, validated, reason = pcall(validateDictionary, value)
    if checked and validated then speciesData = validated
    else
      if not checked then reason = safeCause(validated) end
      warnOnce("dictionary", "[FU Japanese] /fujp/species_display.config invalid (" .. (reason or "invalid shape") .. "); source text preserved")
    end
  end
  return speciesData
end

local function normalizeWhitespace(text)
  return (text:gsub("[ \t\r\n\f\v]+", " "):gsub("^ ", ""):gsub(" $", ""))
end

local function displayText(race, text, field)
  if type(race) ~= "string" or type(text) ~= "string" then return text end
  local data = getData()
  local entry = data and rawget(data, race)
  local candidates = type(entry) == "table" and rawget(entry, field)
  if not isArray(candidates) then return text end
  local normalized = normalizeWhitespace(text)
  local whitespaceMatch
  local index = 1
  while true do
    local candidate = rawget(candidates, index)
    if candidate == nil then break end
    local source, translation = rawget(candidate, "source"), rawget(candidate, "translation")
    if text == source then return translation end
    if not whitespaceMatch and normalized == normalizeWhitespace(source) then
      whitespaceMatch = translation
    end
    index = index + 1
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
