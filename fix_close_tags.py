"""Robustly fix malformed GPX files for Google Maps import.
=========================================================

Known bad patterns from GPS Visualizer:
  - `<wpt>` inside `<trkseg>` (already fixed in pass 1)
  - missing `</trkseg></trk>` before `</gpx>`
  - leading whitespace before `<?xml`
  - trailing junk after `</gpx>` (extra spaces, duplicated declarations)
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOTS = [Path("Hotspot Routes/gpx"), Path("Pokestop Marathons/gpx")]
fixed = 0
still_broken = 0

for gpx in sorted(p for root in ROOTS for p in root.rglob("*.gpx")):
    text = gpx.read_text(encoding="utf-8")
    original = text

    # 1. strip leading whitespace / BOM / CR before <?xml
    text = re.sub(r"^[\s﻿]+", "", text)

    # 2. if multiple <?xml ... ?> declarations exist, drop the later ones
    decls = list(re.finditer(r"<\?xml[^?]*\?>", text))
    if len(decls) > 1:
        first_end = decls[0].end()
        kept = text[:first_end]
        for m in decls[1:]:
            kept += text[m.end():last_end].replace(text[first_end:m.start()], "")
        # rebuild safely: keep first decl + everything after the last extra decl
        text = text[: decls[0].end()] + text[decls[-1].end():]

    # 3. try to parse; if it fails, repair
    if "<gpx" not in text:
        # missing <gpx> root: inject standard wrapper right after <?xml ?>
        text = re.sub(
            r"(<\?xml[^?]*\?>)",
            r'\1<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="GPS Visualizer http://www.gpsvisualizer.com/">',
            text,
            count=1,
        )
    try:
        ET.fromstring(text)
    except ET.ParseError:
        # drop everything after the LAST </gpx>
        m = list(re.finditer(r"</gpx>", text))
        if m:
            last = m[-1].end()
            text = text[:last]
        # ensure closes for trk / trkseg
        if "<trkseg>" in text and "</trkseg>" not in text:
            text = text.replace("</gpx>", "</trkseg></trk></gpx>", 1)
        elif "<trk>" in text and "</trk>" not in text:
            text = text.replace("</gpx>", "</trk></gpx>", 1)

    try:
        ET.fromstring(text)
        if text != original:
            gpx.write_text(text, encoding="utf-8")
            fixed += 1
            print(f"FIXED  {gpx}")
    except ET.ParseError as e:
        still_broken += 1
        print(f"BROKEN  {gpx}: {e}")

print(f"\nFixed: {fixed}, Still broken: {still_broken}")