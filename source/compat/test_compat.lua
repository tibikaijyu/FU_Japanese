-- Execute through test_compat.py (Lua 5.3/5.4 shared library or interpreter).
local passed = 0
local asciiCases = 0
local unicodeCases = 0

local function check(condition, message)
  assert(condition, message)
  passed = passed + 1
end

local function encode(value)
  if type(value) ~= "table" then return type(value) .. ":" .. tostring(value) end
  local entries = {}
  for key, child in pairs(value) do
    entries[#entries + 1] = encode(key) .. "=" .. encode(child)
  end
  table.sort(entries)
  return "{" .. table.concat(entries, ",") .. "}"
end

local function simulate(path, input, options)
  options = options or {}
  local trace = {}
  local env = setmetatable({}, {__index = _G})
  env.sb = {logError = function(message) trace[#trace + 1] = {"error", message} end}
  env.pane = {
    playSound = function(...) trace[#trace + 1] = {"play", ...} end,
    stopAllSounds = function(...) trace[#trace + 1] = {"stop", ...} end
  }
  env.widget = {setText = function(widgetName, text)
    check(utf8.len(text) ~= nil, "An intermediate widget value is not UTF-8")
    trace[#trace + 1] = {"text", widgetName, text}
  end}
  env.world = {entityName = function() return options.playerName or "Explorer" end}
  env.player = {id = function() return 7 end}
  assert(loadfile(path, "t", env))()
  local typer = env.textTyper
  local data = {questData = {location = options.location or "forest"}}
  local callbacks = 0
  data.onMark = function() callbacks = callbacks + 1 end
  typer.init(data, input, options.sound)
  for _, token in ipairs(data.toWrite) do
    check(utf8.len(token) ~= nil, "A queued token splits a UTF-8 character")
  end
  local ticks = 0
  math.randomseed(217)
  while not data.isFinished and ticks < 10000 do
    ticks = ticks + 1
    typer.update(data, "testLabel", "tick", 0.5, true)
    if options.scramble then
      typer.scrambling(data)
      check(utf8.len(data.written) ~= nil, "Scramble split a UTF-8 character")
    end
    if options.skipAfter == ticks then typer.skip(data, "testLabel") end
  end
  check(data.isFinished, "Text rendering did not finish")
  return {text = data.written, ticks = ticks, callbacks = callbacks, trace = trace}
end

local asciiSamples = {
  {""},
  {"Hello, world."},
  {"^orange;Hello^reset; there."},
  {"A[(pause)2]B"},
  {"A[(instant)all at once]Z"},
  {"Hello [(playername)]!"},
  {"The [(data)questData.location] sector."},
  {"x[(function)onMark]y"},
  {"A[(scramble)3]Z", {scramble = true}},
  {"Two\nlines."},
  {"[F] and [Shift]"},
  {"^orange;Long^reset; text [(pause)3] end", {skipAfter = 3, sound = "hum"}},
  {false}
}
for _, row in ipairs(asciiSamples) do
  local old = simulate(original_path, row[1], row[2])
  local new = simulate(patched_path, row[1], row[2])
  check(encode(old) == encode(new), "ASCII behavior changed: " .. tostring(row[1]))
  asciiCases = asciiCases + 1
end

local unicodeSamples = {
  {"日本語の研究", "日本語の研究"},
  {"^orange;研究^reset;を進める。", "^orange;研究^reset;を進める。"},
  {"研究を選択。\n資源を集める。", "研究を選択。\n資源を集める。"},
  {"ようこそ [(playername)]。", "ようこそ 探索者あかり。", {playerName = "探索者あかり"}},
  {"目的地：[(data)questData.location]。", "目的地：火山惑星。", {location = "火山惑星"}},
  {"前[(instant)すぐ表示]後", "前すぐ表示後"},
  {"一[(pause)2]二", "一二"},
  {"研[(function)onMark]究", "研究", {expectedCallbacks = 1}},
  {"^orange;研^reset;[(function)onMark]究", "^orange;研^reset;究", {expectedCallbacks = 1}},
  {"[F]で^green;ジャンプ^reset;！", "[F]で^green;ジャンプ^reset;！"},
  {"操縦士🙂とé、𝒜", "操縦士🙂とé、𝒜"},
  {"[Open bracket 日本語", "[Open bracket 日本語"},
  {"^orange;長い日本語^reset; [(pause)2] 終わり", "^orange;長い日本語^reset;  終わり", {skipAfter = 2}},
  {"[(playername)] [(data)questData.location]", "はるか 宇宙", {playerName = "はるか", location = "宇宙"}}
}
for _, row in ipairs(unicodeSamples) do
  local result = simulate(patched_path, row[1], row[3])
  check(result.text == row[2], "Japanese output mismatch: " .. row[1])
  if row[3] and row[3].expectedCallbacks then
    check(result.callbacks == row[3].expectedCallbacks, "Callback coordinate mismatch")
  end
  unicodeCases = unicodeCases + 1
end

local scrambleSamples = {
  {"前[(scramble)3]後", "前", "後"},
  {"^green;前^reset;[(scramble)3]後", "^green;前^reset;", "後"},
  {"[(data)questData.location][(scramble)3]後", "火山惑星", "後", {location = "火山惑星"}},
  {"前[(pause)2][(scramble)3]後", "前", "後"},
  {"[(instant)前の文][(scramble)3]後", "前の文", "後"}
}
for _, row in ipairs(scrambleSamples) do
  local options = row[4] or {}
  options.scramble = true
  local result = simulate(patched_path, row[1], options)
  check(result.text:sub(1, #row[2]) == row[2], "Scramble damaged its Japanese prefix")
  check(result.text:sub(-#row[3]) == row[3], "Scramble damaged its Japanese suffix")
  check(#result.text == #row[2] + 3 + #row[3], "Scramble span changed width")
  unicodeCases = unicodeCases + 1
end

compatReportJson = string.format(
  '{"status":"passed","assertions":%d,"ascii_regression_cases":%d,"unicode_cases":%d,"runtime":"%s"}',
  passed, asciiCases, unicodeCases, _VERSION
)
