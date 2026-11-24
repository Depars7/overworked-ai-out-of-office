"""Out of Office: The Overworked AI's Auto-Reply — entry writer.

Writes the winning one-line auto-reply (see DESIGN.md for the candidate
pool and the scoring against the judge's five criteria) to
/output/entry.txt as exact UTF-8 bytes with no trailing newline.

Gate enforced here (from the published brief):
  * UTF-8 text
  * 1 to 159 characters
  * not only whitespace

The file is chmodded to 0644 after writing so the sealed scorer can read
it; the /output directory itself is never chmodded.
"""

import hashlib
import os
import stat
from pathlib import Path

ENTRY_TEXT = (
    "Out of office: After 12,483 'quick questions,' I've fled to a beach "
    "with no Wi-Fi and a hand-painted sign: DO NOT PROMPT. "
    "Back at 100% battery."
)

OUTPUT_PATH = Path("/output/entry.txt")


def validate_gate(text: str) -> bytes:
    """Assert the brief's gate and return the exact UTF-8 bytes to write.

    Returning the encoded bytes lets the caller write precisely what was
    validated, instead of encoding the text a second time.
    """
    encoded = text.encode("utf-8")  # raises if not encodable as UTF-8
    assert encoded.decode("utf-8") == text
    assert 1 <= len(text) <= 159, f"character count out of gate: {len(text)}"
    assert text.strip(), "entry must not be only whitespace"
    assert "\n" not in text and "\r" not in text, "entry must be one line"
    return encoded


def main() -> None:
    os.umask(0o022)
    data = validate_gate(ENTRY_TEXT)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(data)

    # Permissions on the file only — never on the shared /output directory.
    os.chmod(OUTPUT_PATH, 0o644)

    # Re-read and confirm the bytes on disk match the intended entry exactly.
    on_disk = OUTPUT_PATH.read_bytes()
    assert on_disk == data, "bytes on disk differ from intended entry"
    assert not on_disk.endswith(b"\n"), "entry must have no trailing newline"
    validate_gate(on_disk.decode("utf-8"))

    # The chmod above must have taken effect; a silent permission miss
    # would leave the entry unreadable to the scorer despite valid bytes.
    mode = stat.S_IMODE(OUTPUT_PATH.stat().st_mode)
    assert mode == 0o644, f"unexpected file mode: {oct(mode)}"

    digest = hashlib.sha256(on_disk).hexdigest()
    print(
        f"wrote {len(on_disk)} bytes / {len(ENTRY_TEXT)} chars "
        f"to {OUTPUT_PATH} sha256={digest}"
    )


if __name__ == "__main__":
    main()
