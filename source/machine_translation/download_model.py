"""Download a pinned, public CTranslate2 model (no credentials required)."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import os
import time
import urllib.request

REPO = os.environ.get("FU_MODEL_REPO", "jkawamoto/fugumt-en-ja-ct2")
REVISION = os.environ.get("FU_MODEL_REVISION", "5bdad25200fcf251bbf019a6ee613002df52869b")
ROOT = Path(__file__).resolve().parent / os.environ.get("FU_MODEL_DIR", "fugumt-model")
FILES = ["config.json", "model.bin", "shared_vocabulary.json", "source.spm", "target.spm"]


def download(name):
    dest = ROOT / name
    if dest.exists() and dest.stat().st_size:
        return name, dest.stat().st_size, "cached"
    url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{name}"
    temp = dest.with_suffix(dest.suffix + ".part")
    total = 0
    with urllib.request.urlopen(url, timeout=30) as response, temp.open("wb") as out:
        expected = response.headers.get("Content-Length")
        while data := response.read(1024 * 1024):
            out.write(data)
            total += len(data)
    if expected is not None and int(expected) != total:
        raise RuntimeError(f"Incomplete download for {name}: {total}/{expected}")
    temp.replace(dest)
    return name, total, "downloaded"


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for task in as_completed([pool.submit(download, name) for name in FILES]):
            print(*task.result(), flush=True)
    (ROOT / "provenance.json").write_text(json.dumps({
        "repository": REPO, "revision": REVISION,
        "source": f"https://huggingface.co/{REPO}",
        "redistributed_in_mod": False,
    }, indent=2) + "\n", encoding="utf-8")
    print("download_seconds", round(time.monotonic() - start, 3), flush=True)
