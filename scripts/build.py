"""Build reproducible Slabs2Blocks release archives with Python 3.11+."""
import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = "Slabs2Blocks-myzticdev-All-Versions.zip"
STABLE = "1.20.2-26.3"
PREVIEW = "26.4-snapshot-1-to-pre-1"
LEGACY = [
    ("1.13-1.13.2", 4, "1.13"),
    ("1.14-1.14.4", 4, "1.14"),
    ("1.15-1.15.2", 5, "1.14"),
    ("1.16-1.16.1", 5, "1.16"),
    ("1.16.2-1.16.5", 6, "1.16"),
    ("1.17-1.17.1", 7, "1.17"),
    ("1.18-1.18.1", 8, "1.17"),
    ("1.18.2", 9, "1.17"),
    ("1.19-1.19.3", 10, "1.19"),
    ("1.19.4", 12, "1.19"),
    ("1.20-1.20.1", 15, "1.20"),
]
# Inclusive format bounds and the last group of vanilla slabs available.
STABLE_OVERLAYS = [
    ((41, 0), (47, 2147483647), "1.20"),
    ((48, 0), (56, 2147483647), "1.21"),
    ((57, 0), (60, 2147483647), "1.21"),
    ((61, 0), (106, 2147483647), "1.21.4"),
    ((107, 1), (120, 2147483647), "26.2"),
    ((121, 0), (121, 0), "26.3"),
]
PREVIEW_OVERLAYS = [
    ((125, 0), (125, 0), "26.4-snapshot-5"),
    ((125, 1), (125, 1), "26.4-snapshot-6"),
    ((126, 0), (128, 1), "26.4-snapshot-7"),
]


def encode(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def catalogs():
    groups = json.loads((ROOT / "src/slabs.json").read_text())
    slabs = {}
    versions = {}
    for version, additions in groups.items():
        if slabs.keys() & additions.keys():
            raise ValueError(f"Duplicate slab in {version}")
        slabs.update(additions)
        versions[version] = slabs.copy()
    return versions


def recipes(slabs, fmt):
    folder = "recipe" if fmt >= 48 else "recipes"
    files = {}
    for slab, block in slabs.items():
        item = f"minecraft:{slab}"
        recipe = {
            "type": "minecraft:crafting_shaped",
            "pattern": ["SS"],
            "key": {"S": item if fmt >= 57 else {"item": item}},
            "result": {"id" if fmt >= 41 else "item": f"minecraft:{block}", "count": 1},
        }
        files[f"data/slabs2blocks/{folder}/{slab}.json"] = encode(recipe)
    return files


def pack(versions, base_version, fmt, overlays=(), preview=False):
    description = "Slabs2Blocks by myzticdev | Two matching slabs make one block."
    metadata = {"description": description}
    if not preview:
        metadata["pack_format"] = fmt
    if overlays:
        metadata.update(min_format=[fmt, 0], max_format=overlays[-1][1])
        if not preview:
            metadata["supported_formats"] = {"min_inclusive": fmt, "max_inclusive": 81}
    document = {"pack": metadata}
    base = recipes(versions[base_version], fmt)
    files = dict(base)
    entries = []
    for low, high, version in overlays:
        directory = f"overlay_{low[0]}_{low[1]}"
        entry = {"directory": directory, "min_format": low, "max_format": high}
        if not preview:
            entry["formats"] = {"min_inclusive": low[0], "max_inclusive": high[0]}
        entries.append(entry)
        for path, content in recipes(versions[version], low[0]).items():
            if base.get(path) != content:
                files[f"{directory}/{path}"] = content
    if entries:
        document["overlays"] = {"entries": entries}
    files["pack.mcmeta"] = encode(document)
    files["pack.png"] = (ROOT / "src/pack.png").read_bytes()
    return archive(files)


def archive(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for path, content in sorted(files.items()):
            entry = zipfile.ZipInfo(path)  # Fixed timestamp for reproducible releases.
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            bundle.writestr(entry, content, compress_type=zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def release_files():
    versions = catalogs()
    packs = {f"Slabs2Blocks-{name}.zip": pack(versions, base, fmt) for name, fmt, base in LEGACY}
    packs[f"Slabs2Blocks-{STABLE}.zip"] = pack(versions, "1.20", 18, STABLE_OVERLAYS)
    packs[f"Slabs2Blocks-{PREVIEW}.zip"] = pack(versions, "26.3", 122, PREVIEW_OVERLAYS, preview=True)
    packs["SHA256SUMS.txt"] = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(packs.items())
    ).encode()
    packs[MASTER] = archive(packs)
    return packs


if __name__ == "__main__":
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for filename, payload in release_files().items():
        (dist / filename).write_bytes(payload)
        print(filename)
