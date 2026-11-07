#!/usr/bin/env python3
"""Reproduce the minimal UTF-8 / Japanese menu override for FU's SBVN reader."""
import argparse
import hashlib
import json
from pathlib import Path


HELPERS = '''-- FU Japanese: count complete UTF-8 characters, never bytes, while revealing.
-- Markup tokens have zero width and must not be split by an inserted color tag.
local function fuJpTextBoundaries(text)
  local positions = {}
  local i = 1
  while i <= #text do
    local tagEnd = text:sub(i, i) == "^" and text:find(";", i, true)
    if tagEnd and not text:sub(i, tagEnd):find("\\n", 1, true) then
      i = tagEnd + 1
    else
      local byte = text:byte(i)
      local width = 1
      if byte >= 0xF0 and byte <= 0xF4 then
        width = 4
      elseif byte >= 0xE0 and byte <= 0xEF then
        width = 3
      elseif byte >= 0xC2 and byte <= 0xDF then
        width = 2
      end
      i = math.min(#text + 1, i + width)
      positions[#positions + 1] = i - 1
    end
  end
  if #positions > 0 then positions[#positions] = #text end
  return positions
end

local function fuJpConcealText(text)
  -- A color tag in the hidden suffix must not override the clear color.
  return "^clear;" .. text:gsub("(%^[^;\\n]*;)", "%1^clear;")
end

'''


DISPLAY_HELPERS = '''-- The original end card is black with an English bitmap caption.
-- Reuse the existing black background and draw the Japanese caption as text.
-- An exact asset-path check leaves every other story/background unchanged.
local function fuJpDrawBackground(canvas, path, position, scale, color)
  local isEndCard = path == "/interface/scripted/sbvn/games/cthululove/bg_end.png"
  local drawPath = isEndCard and "/interface/scripted/sbvn/games/cthululove/bg_black.png" or path
  if scale == nil then
    canvas:drawImage(drawPath, position)
  else
    canvas:drawImage(drawPath, position, scale, color)
  end
  if isEndCard then
    canvas:drawText("おわり", {
      position = {position[1] + 20, position[2] + 60},
      horizontalAnchor = "left", verticalAnchor = "bottom"
    }, 10, {235, 229, 182, color and color[4] or 255})
  end
end

'''


def prepare(upstream, compat):
    upstream, compat = Path(upstream), Path(compat)
    rel = 'interface/scripted/sbvn/pandorasboxsbvngui.lua'
    source = (upstream / rel).read_text(encoding='utf-8')
    result = source
    changes = [
        ('require "/scripts/util.lua"\n', 'require "/scripts/util.lua"\n\n' + HELPERS + DISPLAY_HELPERS),
        ('{"New Game", "NEW"}', '{"はじめから", "NEW"}'),
        ('{"Continue", "LOAD", savedState}', '{"つづきから", "LOAD", savedState}'),
        ('    widget.setText("lblText", "^clear;" .. scene.text)',
         '    local textBoundaries = fuJpTextBoundaries(scene.text)\n'
         '    local textLength = #textBoundaries\n'
         '    widget.setText("lblText", fuJpConcealText(scene.text))'),
        ('        local rate = dt / (scene.text:len() / self.textRate)',
         '        local rate = textLength > 0 and dt / (textLength / self.textRate) or 1'),
        ('          local i = math.ceil(ratio * scene.text:len())',
         '          local i = textBoundaries[math.ceil(ratio * textLength)] or #scene.text'),
        ('            local outStr = scene.text:sub(1, i) .. "^clear;" .. scene.text:sub(i + 1, scene.text:len())',
         '            local outStr = scene.text:sub(1, i) .. fuJpConcealText(scene.text:sub(i + 1))'),
        ('self.bgCanvas:drawImage(oldBg, {0, 0})',
         'fuJpDrawBackground(self.bgCanvas, oldBg, {0, 0})'),
        ('self.bgCanvas:drawImage(newBg, {0, 0}, 1.0, {255, 255, 255, alpha})',
         'fuJpDrawBackground(self.bgCanvas, newBg, {0, 0}, 1.0, {255, 255, 255, alpha})'),
        ('self.bgCanvas:drawImage(newBg, {0, 0})',
         'fuJpDrawBackground(self.bgCanvas, newBg, {0, 0})'),
        ('self.bgCanvas:drawImage(imagePath(scene.background), {0, 0})',
         'fuJpDrawBackground(self.bgCanvas, imagePath(scene.background), {0, 0})'),
    ]
    for original, replacement in changes:
        if result.count(original) != 1:
            raise ValueError(f'Upstream SBVN source changed: expected unique {original!r}')
        result = result.replace(original, replacement, 1)
    target = compat / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result, encoding='utf-8')
    report = {'asset': rel, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'target_sha256': hashlib.sha256(result.encode()).hexdigest(),
              'guarded_source_edits': len(changes),
              'changes': ['UTF-8 character-safe progressive text reveal',
                          'Atomic zero-width color tags and hidden suffix colors',
                          'Japanese New Game / Continue captions; NEW / LOAD IDs unchanged',
                          'Japanese native text for the exact Cthulhu story end card; fade alpha retained; no bitmap edits']}
    (compat / 'sbvn_source_changes.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('upstream')
    parser.add_argument('compat')
    args = parser.parse_args()
    print(json.dumps(prepare(args.upstream, args.compat), ensure_ascii=False, indent=2))
