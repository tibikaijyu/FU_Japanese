-- FU Japanese 0.2.2: display-only fallback for reviewed species information.
-- Keys remain internal species IDs. Unknown descriptions and Japanese text pass
-- through unchanged. Whitespace normalization never authorizes a partial match.
-- Starbound's require executes a script for side effects and returns nil.
-- Export the uniquely named namespace globally, like FU's other Lua modules.
fuJapaneseSpeciesDisplay = {}
local displayData

if sb and type(sb.logInfo) == "function" then
  sb.logInfo("[FU Japanese 0.2.2] Species display helper active")
end

local function normalizeWhitespace(text)
  return (text:gsub("[ \t\r\n\f\v]+", " "):gsub("^ ", ""):gsub(" $", ""))
end

local function getData()
  if displayData == nil then
    local ok, data = pcall(root.assetJson, "/fujp/species_display.config")
    displayData = (ok and type(data) == "table" and type(data.species) == "table" and data.species) or {}
  end
  return displayData
end

local function displayText(race, text, field)
  if type(race) ~= "string" or type(text) ~= "string" then return text end
  local entry = getData()[race]
  if type(entry) ~= "table" or type(entry[field]) ~= "table" then return text end
  local normalized = normalizeWhitespace(text)
  local whitespaceMatch
  for _, candidate in ipairs(entry[field]) do
    if type(candidate) == "table" and type(candidate.source) == "string" and type(candidate.translation) == "string" then
      if text == candidate.source then return candidate.translation end
      if not whitespaceMatch and normalized == normalizeWhitespace(candidate.source) then
        whitespaceMatch = candidate.translation
      end
    end
  end
  return whitespaceMatch or text
end

function fuJapaneseSpeciesDisplay.description(race, text)
  return displayText(race, text, "descriptions")
end

function fuJapaneseSpeciesDisplay.name(race, text)
  return displayText(race, text, "names")
end

