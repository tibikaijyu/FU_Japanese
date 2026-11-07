local assertions = 0
local tests = 0
local function check(ok, message)
  assertions = assertions + 1
  if not ok then error(message or "check failed", 2) end
end

local function clone(v)
  if type(v) ~= "table" then return v end
  local result = {}
  for k, x in pairs(v) do result[k] = clone(x) end
  return result
end

local function environment(path, rate, step)
  local e = setmetatable({}, {__index = _G})
  e.require = function() end
  e.copy = clone
  e.dt = step or (1 / 60)
  e.util = {filter = function(array, fn)
    local out = {}
    for _, value in ipairs(array) do if fn(value) then table.insert(out, value) end end
    return out
  end}
  e.draws = {}
  local canvas = {
    clear = function() end,
    drawImage = function(_, path, position, scale, color)
      table.insert(e.draws, {kind="image", path=path, position=clone(position), scale=scale, color=clone(color)})
    end,
    drawText = function(_, text, options, fontSize, color)
      table.insert(e.draws, {kind="text", text=text, options=clone(options), fontSize=fontSize, color=clone(color)})
    end
  }
  e.self = {
    transitions = {}, scene = {}, bgCanvas = canvas, fgCanvas = canvas,
    gamePath = "test/", screenSize = {300, 200}, textRate = rate or 30,
    bgFadeTime = 0.5,
    selected = 1, selFormat = "^green;[%s]", unselFormat = "^gray; %s ",
    gameScenes = {}, gameConfig = {titleScene = {text = "title"}, entryScene = "intro"}
  }
  e.history = {}
  e.visible = {}
  e.widget = {
    setText = function(id, value)
      if id == "lblText" then table.insert(e.history, value) end
      e.visible[id] = value
    end,
    setVisible = function(id, value) e.visible[id .. ".visible"] = value end
  }
  e.world = {sendEntityMessage = function() end}
  e.pane = {sourceEntity = function() return 1 end}
  e.sb = {logError = function() end}
  local chunk = assert(loadfile(path, "t", e))
  chunk()
  return e
end

local function run(path, source, rate, step)
  local e = environment(path, rate, step)
  e.setScene({text = source, options = {{"次へ", "next"}}}, true)
  local iterations = 0
  for _, task in ipairs(e.self.transitions) do
    while coroutine.status(task) ~= "dead" do
      local ok, errorMessage = coroutine.resume(task)
      check(ok, errorMessage)
      iterations = iterations + 1
      check(iterations < 20000, "text transition did not finish")
    end
  end
  check(e.visible["lblOptions.visible"] == true, "options stay hidden after reveal")
  check(e.visible.lblText == source, "final text differs from source")
  return e.history, e
end

local function plain(text)
  return (text:gsub("%^[^;\n]*;", ""))
end

local function visibleText(text)
  local visible, hidden, i = {}, false, 1
  while i <= #text do
    local start, finish, color = text:find("%^([^;\n]*);", i)
    if start == i then
      hidden = color == "clear"
      i = finish + 1
    else
      local finishText = start and start - 1 or #text
      if not hidden then table.insert(visible, text:sub(i, finishText)) end
      i = finishText + 1
    end
  end
  return table.concat(visible)
end

-- ASCII scene output and reveal timing remain byte-for-byte compatible.
for _, source in ipairs({"A", "A short scene.", "Line one.\nLine two.", "1234567890"}) do
  tests = tests + 1
  local before = run(original_path, source, 17, 1 / 60)
  local after = run(patched_path, source, 17, 1 / 60)
  check(#before == #after, "ASCII transition frame count changed")
  for i, value in ipairs(before) do check(value == after[i], "ASCII frame changed at " .. i) end
end

-- Every intermediate UTF-8 string must decode; visible characters form a prefix.
for _, source in ipairs({
  "日本語の本文です。", "A日本語B", "日本語\n次の行", "二字😊éЖ",
  "^red;赤色の文字^reset;通常の文字", "先頭^green;途中^yellow;末尾^reset;",
  "", "^red;^reset;"
}) do
  tests = tests + 1
  local history = run(patched_path, source, 9, 1 / 60)
  local expected = plain(source)
  local lastVisible = ""
  for _, frame in ipairs(history) do
    check(utf8.len(frame) ~= nil, "invalid intermediate UTF-8")
    check(plain(frame) == expected, "intermediate frame changed text or split markup")
    check(not plain(frame):find("^", 1, true), "color token split across frames")
    local shown = visibleText(frame)
    check(utf8.len(shown) ~= nil, "visible prefix ends inside a character")
    check(expected:sub(1, #shown) == shown, "hidden suffix color leaked future text")
    check(#shown >= #lastVisible, "visible prefix decreased")
    lastVisible = shown
  end
  check(lastVisible == expected, "full scene was not eventually visible")
end

-- Japanese characters reveal at the same character rate as an ASCII scene.
tests = tests + 1
local japanese = run(patched_path, "日本語表示", 8, 1 / 60)
local ascii = run(original_path, "ABCDE", 8, 1 / 60)
check(#japanese == #ascii, "Japanese rate still counts UTF-8 bytes")

-- Skipping a transition reveals the full scene and preserves choices.
tests = tests + 1
local skipped = environment(patched_path, 8, 1 / 60)
local skipScene = {text = "日本語をまとめて表示する。", options = {{"選択肢", "destination"}}}
skipped.setScene(skipScene, true)
skipped.advance()
check(skipped.visible.lblText == skipScene.text, "skip lost Japanese text")
check(#skipped.self.transitions == 0, "skip did not clear transitions")
check(skipped.self.options[1][2] == "destination", "choice target changed")

-- Menu caption changes must not modify NEW/LOAD control IDs or saved state.
tests = tests + 1
local menu = environment(patched_path)
local saved = {scene = "intro", flags = {seen = 3}}
menu.setTitleScene(saved)
check(menu.self.options[1][1] == "はじめから", "New Game menu is not Japanese")
check(menu.self.options[1][2] == "NEW", "NEW control ID changed")
check(menu.self.options[2][1] == "つづきから", "Continue menu is not Japanese")
check(menu.self.options[2][2] == "LOAD", "LOAD control ID changed")
check(menu.self.options[2][3] == saved, "saved state was replaced")
menu.self.gameScenes.intro = {text = "読み込んだ本文。"}
menu.processOption(menu.self.options[2])
check(menu.visible.lblText == "読み込んだ本文。", "load behavior changed")
check(menu.self.gameState.flags.seen == 3, "save flags changed")

-- Only the exact story end-card image receives the native Japanese caption.
tests = tests + 1
local ending = environment(patched_path)
ending.self.gamePath = "/interface/scripted/sbvn/games/cthululove/"
local endScene = {background="bg_end", text=" "}
ending.setScene(endScene, false)
check(ending.draws[1].path == ending.self.gamePath .. "bg_black.png", "English end card was not replaced")
check(ending.draws[2].text == "おわり", "Japanese end-card text missing")
check(ending.draws[2].fontSize == 10, "end-card text is too small")
check(ending.draws[2].color[4] == 255, "end-card caption alpha incorrect")
check(endScene.background == "bg_end", "scene state/asset ID was mutated")

tests = tests + 1
local foreign = environment(patched_path)
foreign.self.gamePath = "/another/story/"
foreign.setScene({background="bg_end", text=" "}, false)
check(#foreign.draws == 1, "an unrelated story received the Cthulhu end caption")
check(foreign.draws[1].path == "/another/story/bg_end.png", "unrelated story image changed")

-- A fade transition must apply exactly the background alpha to its caption.
tests = tests + 1
local fade = environment(patched_path)
fade.self.gamePath = "/interface/scripted/sbvn/games/cthululove/"
fade.self.scene = {background="bg_school"}
fade.setScene({background="bg_end", text=" "}, true)
for _, task in ipairs(fade.self.transitions) do
  while coroutine.status(task) ~= "dead" do
    local ok, message = coroutine.resume(task)
    check(ok, message)
  end
end
local captions = 0
for index, call in ipairs(fade.draws) do
  if call.kind == "text" then
    captions = captions + 1
    local background = fade.draws[index - 1]
    check(background.path == fade.self.gamePath .. "bg_black.png", "end text not paired with black background")
    check(call.color[4] == (background.color and background.color[4] or 255), "fade alpha changed for caption")
  elseif call.path == fade.self.gamePath .. "bg_end.png" then
    check(false, "English end-card bitmap drawn during fade")
  end
end
check(captions > 2, "end-card fade was not exercised")

sbvnReportJson = string.format('{"passed":true,"tests":%d,"assertions":%d,"ascii_regression_scenes":4,"unicode_and_markup_scenes":8,"end_card_rendering_cases":3}', tests, assertions)
