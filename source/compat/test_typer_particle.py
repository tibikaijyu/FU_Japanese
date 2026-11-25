"""Exercise the real particle writer on Lua 5.3/5.4, without starting Starbound.

Optional --upstream and --corpus paths bind the regression to installed assets.
The corpus is a JSON array of {asset, config} records after translation patches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
from run_limited_helper_tests import create_runtime
from test_extra_display_fallback import lua_literal

HARNESS = r'''
local function copy(value)
  if type(value) ~= "table" then return value end
  local result = {}
  for k, v in pairs(value) do result[k] = copy(v) end
  return result
end

local function equal(a, b)
  if type(a) ~= type(b) then return false end
  if type(a) ~= "table" then return a == b end
  for k, v in pairs(a) do if not equal(v, b[k]) then return false end end
  for k in pairs(b) do if a[k] == nil then return false end end
  return true
end

local function writer(source, cfg, kind)
  local emitted = {}
  local env = setmetatable({
    init = function() initCalls = (initCalls or 0) + 1 end,
    update = function() updateCalls = (updateCalls or 0) + 1 end,
    config = {getParameter = function() return copy(cfg) end},
    entity = {id = function() return 42 end, position = function() return {10, 20} end},
    world = {
      entityType = function(id) assert(id == 42); return kind or "player" end,
      sendEntityMessage = function(id, name, particle)
        assert(id == 42 and name == "fu_specialAnimator.spawnParticle")
        emitted[#emitted + 1] = copy(particle)
      end
    }
  }, {__index = _G})
  assert(load(source, "typer_particle.lua", "t", env))()
  env.init()
  return env, emitted
end

local function render(source, text, cfg)
  local env, emitted = writer(source, cfg)
  env.typerParticle.spawnCooldown = 1e9
  env.typerParticle.instances = {{text = text, index = 1, lastTime = 0,
    origin = {10, 20}, position = {10, 20}}}
  local frames = 0
  repeat
    env.update(cfg.writeInterval + 0.001)
    frames = frames + 1
    assert(frames <= #text + 2, "writer did not finish")
  until #env.typerParticle.instances == 0
  return emitted
end

local minimal = {particle = {color = {0, 0, 0, 205}, size = 1},
  writeInterval = 0.1, spawnInterval = 0.5, spacing = {1, 1.5},
  printTextInOrder = false, texts = {"ASCII"}, controllers = {}}
local fixtureTexts = {"ASCII words!", "A\nB", "A\n", "日本語", "Aé日😀Z", "日\n本語"}
local count, particles, baselineFailures = 0, 0, 0

local function verify(text, cfg)
  local emitted = render(candidate, text, cfg)
  local joined = {}
  for _, particle in ipairs(emitted) do
    assert(utf8.len(particle.text) == 1, "invalid or split UTF-8 particle")
    assert(particle.type == "text" and particle.layer == "front")
    joined[#joined + 1] = particle.text
  end
  assert(table.concat(joined) == text:gsub("\n", ""), "lost or duplicated text")
  count, particles = count + 1, particles + #emitted
  if baseline then
    local old = render(baseline, text, cfg)
    local invalid = false
    for _, particle in ipairs(old) do
      if utf8.len(particle.text) == nil then invalid = true end
    end
    if invalid then baselineFailures = baselineFailures + 1 end
    if not text:find("[\128-\255]") then
      assert(equal(old, emitted), "ASCII particle properties or placement changed")
    end
  end
end

for _, text in ipairs(fixtureTexts) do verify(text, minimal) end
for _, row in ipairs(corpus) do
  for _, text in ipairs(row.config.texts) do verify(text, row.config) end
end

local positioned = render(candidate, "日\n本語", minimal)
assert(equal(positioned[1].position, {10,20}))
assert(equal(positioned[2].position, {10,21.5}))
assert(equal(positioned[3].position, {11,21.5}))

-- Exercise actual instance creation and the original init/update chain.
local ordered = copy(minimal)
ordered.printTextInOrder, ordered.loopOrderedText = true, true
ordered.texts = {"日", "本"}
local beforeInit, beforeUpdate = initCalls or 0, updateCalls or 0
local env, emitted = writer(candidate, ordered)
env.update(0.11) -- creates the first instance
env.update(0.11) -- emits its complete character
assert(emitted[1].text == "日")
assert((initCalls or 0) == beforeInit + 1 and (updateCalls or 0) == beforeUpdate + 2)
assert(env.typerParticle.SelectText() == "本")
local npc, npcParticles = writer(candidate, minimal, "npc")
npc.update(1)
assert(#npcParticles == 0 and npc.typerParticle.isActive == false)
checkedTexts, checkedParticles, invalidBaselineTexts = count, particles, baselineFailures
'''


def verify(candidate: Path, upstream: Path | None = None, corpus: Path | None = None):
    candidate = candidate.resolve(strict=True)
    rows = json.loads(corpus.read_text(encoding='utf-8')) if corpus else []
    for row in rows:
        if 'patch_sha256' in row:
            patch = HERE.parents[1] / 'mods/FU_Japanese' / (row['asset'] + '.patch')
            if hashlib.sha256(patch.read_bytes()).hexdigest() != row['patch_sha256']:
                raise ValueError('Particle corpus translation patch changed: ' + row['asset'])
    source = ('candidate = ' + lua_literal(candidate.read_text(encoding='utf-8')) + '\n'
              + 'baseline = ' + lua_literal(upstream.read_text(encoding='utf-8') if upstream else None) + '\n'
              + 'corpus = ' + lua_literal(rows) + '\n' + HARNESS)
    reports = []
    for version in ('5.3', '5.4'):
        runtime = create_runtime(version, 'auto')
        try:
            runtime.execute(source, 'particle UTF-8 regression')
            reports.append({
                'lua_version': version, 'runtime': runtime.artifact(),
                'checked_texts': runtime.integer_global('checkedTexts'),
                'checked_particles': runtime.integer_global('checkedParticles'),
                'invalid_baseline_texts': runtime.integer_global('invalidBaselineTexts'),
                'passed': True,
            })
        finally:
            runtime.close()
    return {'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'upstream_sha256': hashlib.sha256(upstream.read_bytes()).hexdigest() if upstream else None,
            'corpus_sha256': hashlib.sha256(corpus.read_bytes()).hexdigest() if corpus else None,
            'effect_count': len(rows), 'runs': reports, 'game_launched': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, default=HERE / 'stats/typer_particle.lua')
    parser.add_argument('--upstream', type=Path)
    parser.add_argument('--corpus', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = verify(args.candidate, args.upstream, args.corpus)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding='utf-8')
    print(serialized)
