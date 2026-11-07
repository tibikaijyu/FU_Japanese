#!/usr/bin/env python3
"""Run the real Lua compatibility tests using an installed Lua shared library."""
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream", type=Path, help="FU repository directory")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    original = args.upstream.resolve() / "zb/zb_textTyper.lua"
    patched = here / "zb/zb_textTyper.lua"
    library = ctypes.util.find_library("lua5.4") or ctypes.util.find_library("lua5.3")
    if not library:
        raise SystemExit("Lua 5.3 or 5.4 shared library is required for this check.")
    lua = ctypes.CDLL(library)
    state_type = ctypes.c_void_p
    lua.luaL_newstate.restype = state_type
    lua.luaL_openlibs.argtypes = [state_type]
    lua.luaL_loadstring.argtypes = [state_type, ctypes.c_char_p]
    lua.luaL_loadstring.restype = ctypes.c_int
    lua.lua_pcallk.argtypes = [state_type, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             ctypes.c_longlong, ctypes.c_void_p]
    lua.lua_pcallk.restype = ctypes.c_int
    lua.lua_tolstring.argtypes = [state_type, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
    lua.lua_tolstring.restype = ctypes.c_void_p
    lua.lua_getglobal.argtypes = [state_type, ctypes.c_char_p]
    lua.lua_getglobal.restype = ctypes.c_int
    lua.lua_close.argtypes = [state_type]

    def get_string(state, position):
        length = ctypes.c_size_t()
        pointer = lua.lua_tolstring(state, position, ctypes.byref(length))
        if not pointer:
            return "(Lua returned a non-string value)"
        return ctypes.string_at(pointer, length.value).decode("utf-8", errors="replace")

    # JSON quoting is valid for these ASCII filesystem path strings in Lua.
    source = ("original_path = " + json.dumps(str(original)) + "\n"
              + "patched_path = " + json.dumps(str(patched)) + "\n"
              + (here / "test_compat.lua").read_text(encoding="utf-8"))
    state = lua.luaL_newstate()
    if not state:
        raise RuntimeError("Could not create a Lua state")
    try:
        lua.luaL_openlibs(state)
        result = lua.luaL_loadstring(state, source.encode("utf-8"))
        if result == 0:
            result = lua.lua_pcallk(state, 0, 0, 0, 0, None)
        if result:
            raise RuntimeError(get_string(state, -1))
        lua.lua_getglobal(state, b"compatReportJson")
        report = json.loads(get_string(state, -1))
    finally:
        lua.lua_close(state)
    report["upstream_sha256"] = hashlib.sha256(original.read_bytes()).hexdigest()
    report["patched_sha256"] = hashlib.sha256(patched.read_bytes()).hexdigest()
    report["limitations"] = "Lua logic test only; Starbound in-game rendering not exercised."
    output = here / "compatibility_test_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
