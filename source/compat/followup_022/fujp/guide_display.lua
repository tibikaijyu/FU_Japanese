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

local function normalize(value)
  -- Normalize formatting only. Do not alter letters, numbers, punctuation or tags.
  return (value:gsub("[ \t\r\n\v\f]+", " "):gsub("^ +", ""):gsub(" +$", ""))
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

local function validateDictionary(value)
  if not isObject(value) then return nil, "root is not an object" end
  local guides = rawget(value, "guides")
  if rawget(value, "version") ~= 1 or not isObject(guides) then
    return nil, "version/guides shape is invalid"
  end
  for guideId, entries in next, guides do
    if type(guideId) ~= "string" or guideId == "" then return nil, "guide id is invalid" end
    local function validEntry(entry)
      if not isObject(entry) then return false end
      local field, source = rawget(entry, "field"), rawget(entry, "source")
      local normalizedSource, translation = rawget(entry, "normalizedSource"), rawget(entry, "translation")
      if type(field) ~= "string"
        or type(source) ~= "string" or type(normalizedSource) ~= "string"
        or type(translation) ~= "string" then
        return false
      end
      if normalize(source) ~= normalizedSource then return false end
      if field == "title" or field == "description" then
        return rawget(entry, "index") == nil
      end
      if field == "contentPages" or field == "longContentPages" then
        local index = rawget(entry, "index")
        return type(index) == "number" and index >= 1 and index % 1 == 0
      end
      return false
    end
    if not validArray(entries, validEntry) then return nil, "guide entries have an invalid shape" end
  end
  return guides
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

local function configuration()
  local assetJson = currentAssetJson()
  -- Keep loading pending until the engine API exists. Cache both success and
  -- failure only for the current assetJson function, so a replacement retries.
  if not assetJson then return nil end
  if cacheReady and cachedApi == assetJson then return cachedGuides end

  cachedApi = assetJson
  cacheReady = true
  cachedGuides = nil
  local loaded, value = pcall(assetJson, "/fujp/guide_display.config")
  if not loaded then
    warnOnce("dictionary", "[FU Japanese] /fujp/guide_display.config load failed (" .. safeCause(value) .. "); codex preserved")
  else
    local checked, validated, reason = pcall(validateDictionary, value)
    if checked and validated then cachedGuides = validated
    else
      if not checked then reason = safeCause(validated) end
      warnOnce("dictionary", "[FU Japanese] /fujp/guide_display.config invalid (" .. (reason or "invalid shape") .. "); codex preserved")
    end
  end
  return cachedGuides
end

local function shallowCopy(value)
  local copy = {}
  for key, child in next, value do rawset(copy, key, child) end
  local mt = getmetatable(value)
  if mt ~= nil then setmetatable(copy, mt) end
  return copy
end

local function localizeCodex(codex)
  if not isObject(codex, true) then return codex end
  local codexId = rawget(codex, "id")
  if type(codexId) ~= "string" then return codex end
  local guides = configuration()
  local entries = guides and rawget(guides, codexId)
  if not entries then return codex end

  local edits = {}
  local entryIndex = 1
  while true do
    local entry = rawget(entries, entryIndex)
    if entry == nil then break end
    local container = codex
    local field, index = rawget(entry, "field"), rawget(entry, "index")
    if index ~= nil then
      container = rawget(codex, field)
      -- A proxy array can have observable or throwing setters. Preserve the
      -- entire original codex instead of copying or changing it.
      if type(container) == "table" and not isArray(container, true) then return codex end
    end
    local current = type(container) == "table" and rawget(container, index or field) or nil
    if type(current) == "string" and normalize(current) == rawget(entry, "normalizedSource") then
      edits[#edits + 1] = {
        field = field,
        index = index,
        translation = rawget(entry, "translation"),
      }
    end
    entryIndex = entryIndex + 1
  end
  if #edits == 0 then return codex end

  -- Build the complete result only after all comparisons and normalizations
  -- succeeded; a later failure cannot leak earlier translated fields.
  local result = shallowCopy(codex)
  local copiedPages = {}
  for editIndex = 1, #edits do
    local edit = rawget(edits, editIndex)
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
