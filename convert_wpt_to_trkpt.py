"""Batch convert <wpt> -> <trkpt> inside <trkseg> for Google Maps import.

GPS Visualizer outputs waypoints inside <trkseg>, which violates the GPX 1.1
schema and Google Maps silently drops the track. This rewrites every <wpt ...>
</wpt> pair inside <trkseg> as <trkpt ...></trkpt>.
"""

from pathlib import Path

ROOTS = [Path("Hotspot Routes/gpx"), Path("Pokestop Marathons/gpx")]
total_files = 0
total_points = 0

for gpx in (p for root in ROOTS for p in root.rglob("*.gpx")):
    text = gpx.read_text(encoding="utf-8")
    new_text = text.replace("<wpt ", "<trkpt ").replace("</wpt>", "</trkpt>")
    if new_text == text:
        continue
    points = text.count("<wpt ")
    gpx.write_text(new_text, encoding="utf-8")
    total_files += 1
    total_points += points
    print(f"{gpx}: {points} points converted")

print(f"\nDone: {total_files} files, {total_points} points")