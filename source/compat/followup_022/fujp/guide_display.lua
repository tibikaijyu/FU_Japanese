-- FU Japanese: localize known guide display fields at the codex viewer boundary.
-- No IDs, save properties, numeric values or unrecognized passages are changed.
-- Source/provenance and CC BY 4.0 attribution are included with the translation.
-- Starbound's require executes scripts but does not return Lua module values.
local M = {}
fuJapaneseGuideDisplay = M

local warned = {}
local cachedApi
local cacheReady = false
local cachedGuides

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

safeLog("logInfo", "[FU Japanese 0.2.2] Guide display helper active")

local function isPlainTable(value)
  return type(value) == "table" and getmetatable(value) == nil
end

local function normalize(value)
  -- Normalize formatting only. Do not alter letters, numbers, punctuation or tags.
  return (value:gsub("[ \t\r\n\v\f]+", " "):gsub("^ +", ""):gsub(" +$", ""))
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

local function validateDictionary(value)
  if not isPlainTable(value) or value.version ~= 1 or not isPlainTable(value.guides) then
    return nil
  end
  for guideId, entries in pairs(value.guides) do
    if type(guideId) ~= "string" or guideId == "" then return nil end
    local function validEntry(entry)
      if not isPlainTable(entry) or type(entry.field) ~= "string"
        or type(entry.source) ~= "string" or type(entry.normalizedSource) ~= "string"
        or type(entry.translation) ~= "string" then
        return false
      end
      if normalize(entry.source) ~= entry.normalizedSource then return false end
      if entry.field == "title" or entry.field == "description" then
        return entry.index == nil
      end
      if entry.field == "contentPages" or entry.field == "longContentPages" then
        return type(entry.index) == "number" and entry.index >= 1 and entry.index % 1 == 0
      end
      return false
    end
    if not validArray(entries, validEntry) then return nil end
  end
  return value.guides
end

local function currentAssetJson()
  if type(root) ~= "table" then return nil end
  local assetJson = root.assetJson
  if type(assetJson) ~= "function" then return nil end
  return assetJson
end

local function configuration()
  local assetJson = currentAssetJson()
  -- Keep loading pending until the engine API exists. Cache both success and
  -- failure only for the current assetJson function, so a replacement retries.
  if not assetJson then return nil end
  if cacheReady and cachedApi == assetJson then return cachedGuides end

  cachedApi = assetJson
  cacheReady = true
  cachedGuides = nil
  local ok, result = pcall(function()
    local value = assetJson("/fujp/guide_display.config")
    local validated = validateDictionary(value)
    if not validated then error("invalid guide display dictionary") end
    return validated
  end)
  if ok then
    cachedGuides = result
  else
    warnOnce("dictionary", "[FU Japanese] guide display dictionary unavailable or invalid; codex preserved")
  end
  return cachedGuides
end

local function shallowCopy(value)
  local copy = {}
  for key, child in next, value do rawset(copy, key, child) end
  return copy
end

local function localizeCodex(codex)
  if not isPlainTable(codex) then return codex end
  local codexId = rawget(codex, "id")
  if type(codexId) ~= "string" then return codex end
  local guides = configuration()
  local entries = guides and guides[codexId]
  if not entries then return codex end

  local edits = {}
  for _, entry in ipairs(entries) do
    local container = codex
    if entry.index ~= nil then
      container = rawget(codex, entry.field)
      -- A proxy array can have observable or throwing setters. Preserve the
      -- entire original codex instead of copying or changing it.
      if type(container) == "table" and not isPlainTable(container) then return codex end
    end
    local current = type(container) == "table" and rawget(container, entry.index or entry.field) or nil
    if type(current) == "string" and normalize(current) == entry.normalizedSource then
      edits[#edits + 1] = {
        field = entry.field,
        index = entry.index,
        translation = entry.translation,
      }
    end
  end
  if #edits == 0 then return codex end

  -- Build the complete result only after all comparisons and normalizations
  -- succeeded; a later failure cannot leak earlier translated fields.
  local result = shallowCopy(codex)
  local copiedPages = {}
  for _, edit in ipairs(edits) do
    if edit.index ~= nil then
      if not copiedPages[edit.field] then
        copiedPages[edit.field] = shallowCopy(rawget(codex, edit.field))
        rawset(result, edit.field, copiedPages[edit.field])
      end
      rawset(copiedPages[edit.field], edit.index, edit.translation)
    else
      rawset(result, edit.field, edit.translation)
    end
  end
  return result
end

function M.localize(codex)
  local ok, result = pcall(localizeCodex, codex)
  if ok then return result end
  warnOnce("conversion", "[FU Japanese] guide display conversion failed; original codex preserved")
  return codex
end

return M
