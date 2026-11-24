import argparse
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

NEAR, FAR = 0.01, 100.0


def matrix_fuer_upstream(werte, groesse):
    matrix = np.array(werte, dtype=float).reshape(groesse, groesse)
    return matrix.T.flatten().tolist()


def projektionsmatrix(frame):
    breite, hoehe = frame["bildGroesse"]
    k = np.array(frame["intrinsics"], dtype=float).reshape(3, 3).T
    fx, fy, cx, cy = k[0, 0], k[1, 1], k[0, 2], k[1, 2]
    p = np.array(
        [
            [2 * fx / breite, 0, (breite - 2 * cx) / breite, 0],
            [0, 2 * fy / hoehe, -(hoehe - 2 * cy) / hoehe, 0],
            [0, 0, -(FAR + NEAR) / (FAR - NEAR), -2 * FAR * NEAR / (FAR - NEAR)],
            [0, 0, -1, 0],
        ]
    )
    return p.flatten().tolist()


def frame_meta(frame):
    return {
        "cameraPoseARFrame": matrix_fuer_upstream(frame["kameraZuWelt"], 4),
        "intrinsics": matrix_fuer_upstream(frame["intrinsics"], 3),
        "projectionMatrix": projektionsmatrix(frame),
    }


def tiefe_in_millimeter(pfad, breite, hoehe):
    meter = np.fromfile(pfad, dtype="<f4").reshape(hoehe, breite)
    return np.clip(np.round(meter * 1000.0), 0, 65535).astype(np.uint16)


def konfidenz_laden(pfad, breite, hoehe):
    return np.fromfile(pfad, dtype=np.uint8).reshape(hoehe, breite)


def ausgabe_dateien(ausgabe, nummer):
    return {
        "json": ausgabe / f"frame_{nummer:04d}.json",
        "foto": ausgabe / f"frame_{nummer:04d}.jpg",
        "tiefe": ausgabe / f"depth_{nummer:04d}.png",
        "konfidenz": ausgabe / f"conf_{nummer:04d}.png",
    }


def wandle_frame_um(frame, vorhanden, ausgabe):
    nummer = frame["nummer"]
    breite, hoehe = frame["tiefenGroesse"]
    dateien = ausgabe_dateien(ausgabe, nummer)

    tiefe = tiefe_in_millimeter(vorhanden[Path(frame["tiefe"]).name], breite, hoehe)
    konfidenz = konfidenz_laden(vorhanden[Path(frame["konfidenz"]).name], breite, hoehe)
    cv2.imwrite(str(dateien["tiefe"]), tiefe)
    cv2.imwrite(str(dateien["konfidenz"]), konfidenz)

    shutil.copyfile(vorhanden[Path(frame["bild"]).name], dateien["foto"])

    dateien["json"].write_text(json.dumps(frame_meta(frame)), encoding="utf-8")


parser = argparse.ArgumentParser(description="Scan umwandeln")
parser.add_argument("--scan", type=Path, required=True, help="Ordner mit dem Scan")
parser.add_argument("--output", type=Path, required=True, help="Ausgabeordner")
args = parser.parse_args()


problems = []

if not args.scan.is_dir():
    problems.append(f"Scan-Ordner existiert nicht: {args.scan}")
else:
    for name in ("frames.json", "room.usdz"):
        if not (args.scan / name).is_file():
            problems.append(f"Datei fehlt: {name}")

if problems:
    print("Eingabe ist nicht in Ordnung:", file=sys.stderr)
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    sys.exit(2)

frames = json.loads((args.scan / "frames.json").read_text(encoding="utf-8"))["frames"]

vorhanden = {pfad.name: pfad for pfad in args.scan.rglob("*") if pfad.is_file()}

for frame in frames:
    for schluessel in ("bild", "tiefe", "konfidenz"):
        dateiname = Path(frame[schluessel]).name
        if dateiname not in vorhanden:
            problems.append(f"Frame {frame['nummer']}: Datei fehlt: {dateiname}")

if problems:
    print("Eingabe ist nicht in Ordnung:", file=sys.stderr)
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    sys.exit(2)

print("Eingabe ist in Ordnung:", len(frames), "Fotos")


args.output.mkdir(parents=True, exist_ok=True)

shutil.copyfile(args.scan / "room.usdz", args.output / "room.usdz")

umgewandelt = 0
uebersprungen = 0
for frame in frames:
    if all(pfad.is_file() for pfad in ausgabe_dateien(args.output, frame["nummer"]).values()):
        uebersprungen += 1
        continue
    wandle_frame_um(frame, vorhanden, args.output)
    umgewandelt += 1

print(f"Fertig: {umgewandelt} umgewandelt, {uebersprungen} übersprungen, Ausgabe: {args.output}")
