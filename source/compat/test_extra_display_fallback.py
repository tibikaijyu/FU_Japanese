#!/usr/bin/env python3
"""Run isolated display-helper regression cases against the bundled Lua DLLs."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FU_ROOT = ROOT / "FU_Japanese"
COMPAT = FU_ROOT / "source" / "compat"
FUJP = COMPAT / "followup_022" / "fujp"
SPECIES_SOURCE = FUJP / "species_display.lua"
GUIDE_SOURCE = FUJP / "guide_display.lua"
SPECIES_CONFIG = FUJP / "species_display.config"
GUIDE_CONFIG = FUJP / "guide_display.config"
DLLS = {
    "5.3": ROOT / "RPGGrowthJP" / "source" / "build" / "tools" / "lua53" / "lua53.dll",
    "5.4": ROOT / "RPGGrowthJP" / "source" / "build" / "tools" / "lua54" / "lua54.dll",
}
REPORT = ROOT / ".local" / "stability-2026-11-12" / "fu-extra" / "fallback-report.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lua_literal(value: Any) -> str:
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "{" + ",".join(f"[{i}]={lua_literal(v)}" for i, v in enumerate(value, 1)) + "}"
    if isinstance(value, dict):
        return "{" + ",".join(f"[{lua_literal(k)}]={lua_literal(v)}" for k, v in value.items()) + "}"
    raise TypeError(f"unsupported Lua literal type: {type(value).__name__}")


class Lua:
    def __init__(self, dll_path: Path, version: str):
        self.path = dll_path
        self.version = version
        self.lib = ctypes.CDLL(str(dll_path))
        self.lib.luaL_newstate.restype = ctypes.c_void_p
        self.lib.luaL_newstate.argtypes = []
        self.lib.luaL_openlibs.restype = None
        self.lib.luaL_openlibs.argtypes = [ctypes.c_void_p]
        self.lib.luaL_loadbufferx.restype = ctypes.c_int
        self.lib.luaL_loadbufferx.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]
        self.lib.lua_pcallk.restype = ctypes.c_int
        self.lib.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_void_p]
        self.lib.lua_tolstring.restype = ctypes.c_void_p
        self.lib.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
        self.lib.lua_settop.restype = None
        self.lib.lua_settop.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.lib.lua_getglobal.restype = ctypes.c_int
        self.lib.lua_getglobal.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.lib.lua_tointegerx.restype = ctypes.c_longlong
        self.lib.lua_tointegerx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.state = self.lib.luaL_newstate()
        if not self.state:
            raise RuntimeError(f"lua {version}: luaL_newstate failed")
        self.lib.luaL_openlibs(self.state)

    def run(self, source: str | bytes, label: str) -> None:
        data = source.encode("utf-8") if isinstance(source, str) else source
        status = self.lib.luaL_loadbufferx(self.state, data, len(data), label.encode("utf-8"), None)
        if status == 0:
            status = self.lib.lua_pcallk(self.state, 0, 0, 0, 0, None)
        if status != 0:
            size = ctypes.c_size_t()
            ptr = self.lib.lua_tolstring(self.state, -1, ctypes.byref(size))
            error = ctypes.string_at(ptr, size.value).decode("utf-8", "replace") if ptr else f"Lua status {status}"
            self.lib.lua_settop(self.state, 0)
            raise AssertionError(f"Lua {self.version} {label}: {error}")

    def close(self) -> None:
        close = getattr(self.lib, "lua_close")
        close.argtypes = [ctypes.c_void_p]
        close.restype = None
        close(self.state)

    def integer_global(self, name: str) -> int:
        self.lib.lua_getglobal(self.state, name.encode("ascii"))
        is_number = ctypes.c_int()
        value = self.lib.lua_tointegerx(self.state, -1, ctypes.byref(is_number))
        self.lib.lua_settop(self.state, -2)
        if not is_number.value:
            raise RuntimeError(f"Lua {self.version}: global {name} is not an integer")
        return int(value)


def source_meta(path: Path) -> dict[str, str]:
    return {"path": str(path.resolve()), "sha256": sha256(path)}


def build_suite(species: dict[str, Any], guides: dict[str, Any]) -> tuple[str, str, list[str]]:
    case_names: list[str] = []
    chunks = [
        "__assertions=0; __cases=0; __warnings=0; __assetCalls={};",
        "sb={logInfo=function() error('logger info failure') end,logWarn=function() __warnings=__warnings+1; error('logger warning failure') end};",
        "root=nil; __speciesCurrent=nil; __guideCurrent=nil;",
        "function __setAssets() root={assetJson=function(path) __assetCalls[path]=(__assetCalls[path] or 0)+1; if path=='/fujp/species_display.config' then return __speciesCurrent elseif path=='/fujp/guide_display.config' then return __guideCurrent end; error('unexpected asset '..tostring(path)) end} end;",
    ]
    setup = "\n".join(chunks)
    chunks = [
        "function check(ok,msg) __assertions=__assertions+1; if not ok then error('assertion failed: '..msg,2) end end; "
        "function case(name) __cases=__cases+1 end;"
    ]
    case_names.append("source modules load with logger errors; root readiness recovers later")
    chunks.append(
        "case('load and late root readiness'); "
        "local untouched='untranslated'; check(fuJapaneseSpeciesDisplay.description('aegi',untouched)==untouched,'species root nil fallback'); "
        "local codex={id='ffguide',title='How to Play'}; check(fuJapaneseGuideDisplay.localize(codex)==codex,'guide root nil identity'); "
        "root={}; check(fuJapaneseSpeciesDisplay.name('aegi','Aegi')=='Aegi','species empty root pending'); "
        "check(fuJapaneseGuideDisplay.localize(codex)==codex,'guide empty root pending'); "
        "__speciesCurrent=" + lua_literal(species) + "; __guideCurrent=" + lua_literal(guides) + "; __setAssets(); "
    )

    # Every species entry is checked against its exact configured source, plus unknown and near-match guards.
    species_total = 0
    for race, entry in species["species"].items():
        for field, method in (("descriptions", "description"), ("names", "name")):
            for candidate in entry[field]:
                species_total += 1
                case_names.append(f"species {race}/{field} exact translation {species_total}")
                chunks.append(
                    "case('species configured exact translation'); do local source=" + lua_literal(candidate["source"])
                    + "; local translated=fuJapaneseSpeciesDisplay." + method + "(" + lua_literal(race) + ",source); "
                    + "check(translated==" + lua_literal(candidate["translation"]) + ",'species exact configured translation'); "
                    + "check(utf8.len(translated)~=nil,'species translated UTF-8'); end;"
                )
    chunks.append(
        "case('species exact source guard'); local unknown='unknown species text'; "
        "check(fuJapaneseSpeciesDisplay.description('aegi',unknown)==unknown,'unknown description preserved'); "
        "local near='The descendants of Humans who fled Earth in the face of a natural disaster. changed'; "
        "check(fuJapaneseSpeciesDisplay.description('aegi',near)==near,'near-match preserved');"
    )
    case_names.append("species exact source guard")

    guide_total = 0
    for guide_id, entries in guides["guides"].items():
        for entry in entries:
            guide_total += 1
            case_names.append(f"guide {guide_id}/{entry['field']} exact translation {guide_total}")
            if "index" in entry:
                obj = {"id": guide_id, entry["field"]: {entry["index"]: entry["source"]}}
                access = f"result[{lua_literal(entry['field'])}][{entry['index']}]"
            else:
                obj = {"id": guide_id, entry["field"]: entry["source"]}
                access = f"result[{lua_literal(entry['field'])}]"
            chunks.append(
                "case('guide configured exact translation'); do local original=" + lua_literal(obj)
                + "; local result=fuJapaneseGuideDisplay.localize(original); "
                + "check(result~=original,'guide returns isolated changed copy'); check(" + access + "==" + lua_literal(entry["translation"])
                + ",'guide configured exact translation'); check(utf8.len(" + access + ")~=nil,'guide translated UTF-8'); "
                + "check(original[" + lua_literal(entry["field"]) + "]~=result[" + lua_literal(entry["field"]) + "],'guide original untouched'); end;"
            )
    chunks.append(
        "case('guide unknown and whitespace normalization'); do local original={id='ffguide',title='unknown title'}; "
        "check(fuJapaneseGuideDisplay.localize(original)==original,'guide unknown preserves identity'); end; "
        "do local original={id='ffguide',description='How   to Play'}; local result=fuJapaneseGuideDisplay.localize(original); "
        "check(result~=original and result.description==" + lua_literal(guides["guides"]["ffguide"][1]["translation"] if guides["guides"]["ffguide"][0]["field"] == "description" else next(e["translation"] for e in guides["guides"]["ffguide"] if e["field"] == "description"))
        + ",'guide whitespace normalization'); check(original.description=='How   to Play','guide source untouched'); end;"
    )
    case_names.append("guide unknown source preserved; whitespace normalization retains original")

    # Invalid dictionaries are rejected atomically and cached for their asset API identity.
    malformed_species = [
        '"not a dictionary"',
        "{schemaVersion=1,species=false}",
        "{schemaVersion=1,species={aegi='bad'}}",
        "{schemaVersion=1,species={aegi={descriptions=false,names={}}}}",
        "{schemaVersion=1,species={aegi={descriptions={{source=4,translation='x'}},names={}}}}",
        "{schemaVersion=1,species={aegi={descriptions={{source='x',translation=false}},names={}}}}",
    ]
    for i, bad in enumerate(malformed_species, 1):
        case_names.append(f"malformed species dictionary {i}")
        chunks.append(
            f"case('malformed species dictionary {i}'); __speciesCurrent={bad}; __setAssets(); local source='original species text'; "
            "check(fuJapaneseSpeciesDisplay.description('aegi',source)==source,'malformed species fallback'); "
            "local before=__assetCalls['/fujp/species_display.config']; fuJapaneseSpeciesDisplay.description('aegi',source); "
            "check(__assetCalls['/fujp/species_display.config']==before,'malformed species cached once');"
        )
    malformed_guides = [
        '"not a dictionary"',
        "{version=1,guides=false}",
        "{version=1,guides={ffguide='bad'}}",
        "{version=1,guides={ffguide={{field=4,source='x',normalizedSource='x',translation='y'}}}}",
        "{version=1,guides={ffguide={{field='title',source=4,normalizedSource='x',translation='y'}}}}",
        "{version=1,guides={ffguide={{field='title',source='x',normalizedSource='bad',translation='y'}}}}",
        "{version=1,guides={ffguide={{field='title',source='x',normalizedSource='x',translation=false}}}}",
        "{version=1,guides={ffguide={{field='contentPages',source='x',normalizedSource='x',translation='y',index=0}}}}",
    ]
    for i, bad in enumerate(malformed_guides, 1):
        case_names.append(f"malformed guide dictionary {i}")
        chunks.append(
            f"case('malformed guide dictionary {i}'); __guideCurrent={bad}; __setAssets(); local original={{id='ffguide',title='How to Play'}}; "
            "check(fuJapaneseGuideDisplay.localize(original)==original,'malformed guide same identity'); "
            "check(original.title=='How to Play','malformed guide no mutation'); "
            "local before=__assetCalls['/fujp/guide_display.config']; fuJapaneseGuideDisplay.localize(original); "
            "check(__assetCalls['/fujp/guide_display.config']==before,'malformed guide cached once');"
        )

    # Inject a late normalization failure after one guide field has already matched; no partial copy may escape.
    case_names += ["species conversion error falls back to original text", "guide late conversion error preserves original object atomically", "proxy codex and pages are untouched"]
    chunks.append(
        "case('species conversion error fallback'); __speciesCurrent=" + lua_literal(species) + "; __setAssets(); "
        "local source='The descendants of Humans who fled Earth in the face of a natural disaster.'; "
        "check(fuJapaneseSpeciesDisplay.description('aegi','unknown conversion warmup')=='unknown conversion warmup','species valid dictionary preloaded'); "
        "local oldGsub=string.gsub; string.gsub=function() error('injected normalize failure') end; "
        "check(fuJapaneseSpeciesDisplay.description('aegi',source)==source,'species conversion fallback'); string.gsub=oldGsub;"
    )
    ffguide_entries = guides["guides"]["ffguide"]
    first_page = next(entry for entry in ffguide_entries if entry["field"] == "contentPages")
    second_field = next(entry for entry in ffguide_entries if entry["field"] == "description")
    atomic_codex = {
        "id": "ffguide",
        "contentPages": {first_page["index"]: first_page["source"]},
        "description": second_field["source"],
    }
    chunks.append(
        "case('guide late conversion atomic fallback'); __guideCurrent=" + lua_literal(guides) + "; __setAssets(); "
        "local original=" + lua_literal(atomic_codex) + "; "
        "local warm=fuJapaneseGuideDisplay.localize(original); "
        "check(warm.contentPages[" + str(first_page["index"]) + "]==" + lua_literal(first_page["translation"])
        + " and warm.description==" + lua_literal(second_field["translation"]) + ",'guide real dictionary preloaded'); "
        "local oldGsub=string.gsub; local calls=0; "
        "string.gsub=function(...) calls=calls+1; if calls==4 then error('late normalize failure') end; return oldGsub(...) end; "
        "local result=fuJapaneseGuideDisplay.localize(original); string.gsub=oldGsub; "
        "check(calls==4,'guide failure injected during second field comparison count='..tostring(calls)); check(result==original,'guide late failure same object'); "
        "check(original.contentPages[" + str(first_page["index"]) + "]==" + lua_literal(first_page["source"])
        + " and original.description==" + lua_literal(second_field["source"]) + ",'guide late failure no partial mutation'); "
        "local retry=fuJapaneseGuideDisplay.localize(original); check(retry~=original and retry.contentPages[" + str(first_page["index"]) + "]=="
        + lua_literal(first_page["translation"]) + " and retry.description==" + lua_literal(second_field["translation"])
        + ",'guide retry translates both staged fields');"
    )
    chunks.append(
        "case('proxy codex and pages untouched'); __guideCurrent=" + lua_literal(guides) + "; __setAssets(); "
        "local reads,writes=0,0; local proxy=setmetatable({id='ffguide'},{__index=function() reads=reads+1; return 'How to Play' end,__newindex=function() writes=writes+1 end}); "
        "check(fuJapaneseGuideDisplay.localize(proxy)==proxy,'proxy root identity'); check(reads==0 and writes==0,'proxy root callbacks untouched'); "
        "local pages=setmetatable({[1]='To read this codex, use your ^orange;Personal Tricorder^reset; and click the Book icon.'},{__index=function() reads=reads+1 end,__newindex=function() writes=writes+1 end}); "
        "local original={id='ffguide',contentPages=pages}; check(fuJapaneseGuideDisplay.localize(original)==original,'proxy pages codex identity'); "
        "check(reads==0 and writes==0,'proxy page callbacks untouched');"
    )
    chunks.append("check(__warnings>0,'throwing warning logger exercised and swallowed'); __caseCount=__cases; __assertionCount=__assertions;")
    return setup, "\n".join(chunks), case_names


def main() -> int:
    # Never leave an old passing report current if a fresh run fails.
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.unlink(missing_ok=True)
    species = json.loads(SPECIES_CONFIG.read_text(encoding="utf-8"))
    guides = json.loads(GUIDE_CONFIG.read_text(encoding="utf-8"))
    species_src = SPECIES_SOURCE.read_bytes()
    guide_src = GUIDE_SOURCE.read_bytes()
    setup, suite, case_names = build_suite(species, guides)
    runtime_results = []
    for version, dll_path in DLLS.items():
        if not dll_path.is_file():
            raise FileNotFoundError(dll_path)
        lua = Lua(dll_path, version)
        try:
            lua.run(setup, "initialize Lua fallback harness")
            lua.run(species_src, "load species helper source")
            lua.run(guide_src, "load guide helper source")
            lua.run(suite, "extra display fallback regression suite")
            actual_case_count = lua.integer_global("__caseCount")
            actual_assertion_count = lua.integer_global("__assertionCount")
        finally:
            lua.close()
        if actual_case_count != len(case_names):
            raise AssertionError(f"Lua {version}: reported {actual_case_count} cases, expected {len(case_names)}")
        runtime_results.append({
            "luaVersion": version,
            "dll": source_meta(dll_path),
            "caseCount": actual_case_count,
            "assertionCount": actual_assertion_count,
            "result": "passed",
        })

    report = {
        "schemaVersion": 1,
        "status": "passed",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "test": source_meta(Path(__file__).resolve()),
        "caseCount": len(case_names),
        "cases": case_names,
        "runtimes": runtime_results,
        "sources": [source_meta(SPECIES_SOURCE), source_meta(GUIDE_SOURCE)],
        "configs": [source_meta(SPECIES_CONFIG), source_meta(GUIDE_CONFIG)],
        "configuredEntryCounts": {
            "speciesDescriptionsAndNames": sum(len(item["descriptions"]) + len(item["names"]) for item in species["species"].values()),
            "guideFieldsAndPages": sum(len(entries) for entries in guides["guides"].values()),
        },
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(REPORT.resolve()), "caseCount": report["caseCount"], "runtimes": runtime_results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"test failed: {exc}", file=sys.stderr)
        raise
