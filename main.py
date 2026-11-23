#!/usr/bin/env python3
"""The Vacuum's Alibi: one deadpan line from a robot vacuum.

Writes the chosen line to /output/entry.txt (or $MAKEFUN_OUTPUT_DIR).
Pure stdlib, no network, no reads outside this repo.
"""

import os
import stat
import sys
import tempfile

LINE = (
    "My sensors classified that spot as load-bearing dust. "
    "Removing it would void the floor's warranty, collapse the room, "
    "and require a second pass. I checked twice."
)


def main() -> int:
    line = LINE
    if not line or not line.strip():
        print("error: line is empty or blank", file=sys.stderr)
        return 1
    if len(line) > 200:
        print(f"error: line is {len(line)} characters, over the 200 limit",
              file=sys.stderr)
        return 1
    if "\n" in line or "\r" in line:
        print("error: line must be a single line", file=sys.stderr)
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        print(f"error: cannot create output dir {out_dir}: {exc}",
              file=sys.stderr)
        return 1

    target = os.path.join(out_dir, "entry.txt")
    data = line.encode("utf-8")

    try:
        fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix=".entry-",
                                        suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, target)
        os.chmod(target, 0o644)
    except OSError as exc:
        print(f"error: failed to write {target}: {exc}", file=sys.stderr)
        return 1

    # Read back and verify bytes + mode.
    try:
        with open(target, "rb") as fh:
            back = fh.read()
        mode = stat.S_IMODE(os.stat(target).st_mode)
    except OSError as exc:
        print(f"error: failed to verify {target}: {exc}", file=sys.stderr)
        return 1
    if back != data:
        print("error: verification failed: bytes on disk differ",
              file=sys.stderr)
        return 1
    if mode != 0o644:
        print(f"error: verification failed: mode is {oct(mode)}, not 0644",
              file=sys.stderr)
        return 1

    print(f"wrote {target} ({len(line)} characters, mode 0644)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
