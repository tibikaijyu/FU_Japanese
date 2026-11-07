-- FU Japanese: localize known guide display fields at the codex viewer boundary.
-- No IDs, save properties, numeric values or unrecognized passages are changed.
-- Source/provenance and CC BY 4.0 attribution are included with the translation.
local M = {}
local cachedConfig
local didLoad = false

if sb and sb.logInfo then
  sb.logInfo("[FU Japanese 0.2.2] Guide display helper active")
end

local function normalize(value)
  -- Normalize formatting only. Do not alter letters, numbers, punctuation or tags.
  return (value:gsub("[ \t\r\n\v\f]+", " "):gsub("^ +", ""):gsub(" +$", ""))
end

local function configuration()
  if not didLoad then
    didLoad = true
    local ok, value = pcall(function()
      return root.assetJson("/fujp/guide_display.config")
    end)
    if ok and type(value) == "table" and type(value.guides) == "table" then
      cachedConfig = value.guides
    end
  end
  return cachedConfig
end

local function shallowCopy(value)
  local copy = {}
  for key, child in pairs(value) do copy[key] = child end
  return copy
end

function M.localize(codex)
  if type(codex) ~= "table" or type(codex.id) ~= "string" then return codex end
  local guides = configuration()
  local entries = guides and guides[codex.id]
  if type(entries) ~= "table" then return codex end
  local result = codex
  local copiedArrays = {}
  for _, entry in ipairs(entries) do
    local field = entry.field
    -- The dictionary cannot authorize arbitrary data changes.
    local validRoot = (field == "title" or field == "description") and entry.index == nil
    local validPage = (field == "contentPages" or field == "longContentPages")
        and type(entry.index) == "number" and entry.index >= 1 and entry.index % 1 == 0
    if (validRoot or validPage) and type(entry.source) == "string"
        and type(entry.translation) == "string" then
      local container = entry.index and codex[field] or codex
      local key = entry.index or field
      local current = type(container) == "table" and container[key] or nil
      if type(current) == "string" and current ~= entry.translation
          and normalize(current) == entry.normalizedSource then
        if result == codex then result = shallowCopy(codex) end
        if entry.index then
          if not copiedArrays[field] then
            result[field] = shallowCopy(codex[field])
            copiedArrays[field] = true
          end
          result[field][key] = entry.translation
        else
          result[field] = entry.translation
        end
      end
    end
  end
  return result
end

-- Starbound's require executes scripts but does not return Lua module values.
-- Export a distinct global for callers, while retaining a return for test tools.
fuJapaneseGuideDisplay = M
return M
