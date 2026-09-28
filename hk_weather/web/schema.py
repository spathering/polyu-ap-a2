"""Small helpers for the versioned static data contract."""

import hashlib


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path, root, *, dtype=None, shape=None, offset=None):
    record = {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    if dtype is not None:
        record["dtype"] = dtype
    if shape is not None:
        record["shape"] = list(shape)
    if offset is not None:
        record["offset"] = int(offset)
    return record
