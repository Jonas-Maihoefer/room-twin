# LiteReality-Agent PoC (Issue 18)

Experiment, getrennt von der OpenUSD-Pipeline in `backend/`.

- [UPSTREAM.md](UPSTREAM.md): welcher Upstream-Stand verwendet wird
- [INPUT_COMPATIBILITY.md](INPUT_COMPATIBILITY.md): welches Eingabeformat Upstream erwartet und wie unsere Daten umgewandelt werden

## Stand

Umgesetzt ist **nur ein Schritt**: Ein Scan aus unserem Scanner wird in das Eingabeformat von LiteReality-Agent umgewandelt. Die Upstream-Pipeline selbst, Deep Agents, LiteLLM, die GPU-Anbindung und der Kostenbericht fehlen noch.

## Einrichtung

Python 3.12 mit `numpy` und `opencv-python-headless`, am besten in einer eigenen Umgebung außerhalb des Projekts:

```bash
python -m venv ~/litereality-venv
~/litereality-venv/Scripts/python.exe -m pip install numpy opencv-python-headless
```

Auf Linux und macOS heißt das Programm `~/litereality-venv/bin/python`. Getestet ist nur Windows.

## Benutzung

Im Ordner `room-twin`:

```bash
python experiments/litereality-agent-poc/cli.py --scan backend/testdata --output ~/litereality-out
```

| Parameter | Bedeutung |
|---|---|
| `--scan` | Ordner mit `frames.json`, `room.usdz` und den Frame-Dateien |
| `--output` | Ausgabeordner. Bitte außerhalb von Git, damit keine Scan-Daten committet werden. |

Die Frame-Dateien werden über die Namen aus `frames.json` gefunden, egal in welchem Unterordner des Scan-Ordners sie liegen.

## Was das Programm tut

1. **Prüfen.** Gibt es den Scan-Ordner, `frames.json` und `room.usdz`, und gibt es für jedes Foto die drei Dateien (Bild, Tiefe, Konfidenz)? Wenn nicht, bricht das Programm ab, **bevor** es etwas schreibt.
2. **Umwandeln.** Pro Foto entstehen vier Dateien im Ausgabeordner, dazu `room.usdz`:
   `frame_NNNN.json`, `frame_NNNN.jpg`, `depth_NNNN.png`, `conf_NNNN.png`.

## Wiederaufnahme

Wird ein Lauf unterbrochen, startest du denselben Befehl nochmal. Ein Foto gilt als fertig, wenn alle vier Dateien im Ausgabeordner vorhanden sind. Fertige Fotos werden übersprungen. Fehlt von einem Foto eine Datei, wird es neu gemacht.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| `0` | alles gut |
| `2` | die Eingabe ist ungültig (Ordner oder Datei fehlt) |

## Bekannte Grenzen

- Das Programm prüft nur, ob die Dateien da sind, nicht, ob ihr Inhalt in Ordnung ist. Eine kaputte `frames.json` führt zu einem Absturz mit Fehlermeldung.
- Wird ein Lauf mitten in einer Datei abgebrochen, kann eine halbe Datei zurückbleiben. Dann den Ausgabeordner löschen und neu starten.
- Gleiche Dateinamen in verschiedenen Unterordnern werden nicht erkannt, es zählt der letzte gefundene.
- Es gibt keine automatischen Tests und keinen Parameter `--max-spend-usd`, weil dieser Schritt nichts kostet.
- Das Issue nennt als Beispiel `python -m ... run`. Hier ist es ein einzelnes Skript ohne Unterbefehle.
- `NEAR` und `FAR` der Projektionsmatrix (0,01 und 100) sind Annahmen und stehen nicht in den Scan-Daten.
- Die Prüfung der Pose-Konvention ist visuell und nur für einen Stuhl in zwei Frames erfolgt.
- Die Abhängigkeiten von Upstream sind noch nicht gepinnt.
