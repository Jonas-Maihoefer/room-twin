# Eingabe-Kompatibilität: Room Twin Scan → LiteReality-Agent

**Stand:** Room Twin `main` @ `4d09670`, LiteReality-Agent @ `28ffe1f` (gepinnt, siehe [UPSTREAM.md](UPSTREAM.md)).

**Ergebnis vorab:** Der Testdatensatz in `backend/testdata/` ist **nicht direkt kompatibel** mit LiteReality-Agent. Die Informationen sind größtenteils vorhanden, liegen aber in anderer Struktur, anderem Format und anderen Pfaden vor. Eine Umwandlung ist nötig.

Die Analyse basiert nur auf dem Quellcode. Ein Lauf mit echten Daten steht noch aus.

## Was Upstream erwartet

Quellen im Upstream-Klon (Pfade ab `src/litereality_agent/`):

- `pipeline/scene_init/ingest/preprocessing/vendor/litereality/scanner_capture.py`: `load_frame_info`, `load_scan_frames_no_video`
- `pipeline/scene_init/ingest/preprocessing/vendor/litereality/roomplan.py`: `extract_rgbd`
- `pipeline/scene_init/ingest/extract/extract_scene.py`: `copy_scan_files`

| Element | Erwarteter Name / Ort | Erwarteter Inhalt |
|---|---|---|
| Frame-Metadaten | `frame_NNNN.json`, **eine Datei pro Frame**, im Scan-Ordner | Schlüssel `cameraPoseARFrame` (4×4) und `intrinsics` (3×3) |
| RGB-Bild | `frame_NNNN.jpg`, im **selben Ordner wie die JSON-Datei** | Originalauflösung |
| Tiefenbild | `depth_NNNN.png` | mit OpenCV gelesen (`IMREAD_UNCHANGED`), Werte in Millimetern, im Code durch 1000 geteilt |
| Konfidenzbild | `conf_NNNN.png` | **Pflicht, sobald ein Tiefenbild existiert**, sonst Abbruch mit `Missing confidence image` |
| RoomPlan-Modell | `room.usdz` im Wurzelordner oder in `roomplan/` | RoomPlan-Ergebnis |
| Punktwolke | `textured_output.obj`, `pointcloud.pcd` oder Tiefenbilder | Eine der drei Quellen muss vorhanden sein |

Die Pose wird in Upstream zusätzlich in Y und Z gespiegelt (`pose_yz_flip` in `load_frame_info`).

## Was Room Twin liefert

Quelle: `backend/testdata/` auf `main`.

| Element | Inhalt |
|---|---|
| `room.usdz`, `room.json`, `metadata.json` | vorhanden |
| `mesh.obj` | ARKit-Netz mit Klassen, **keine** Punktwolke im Sinne der Upstream-Quellen |
| `frames.json` | **eine** Datei mit einer Liste aller 106 Frames |
| Frame-Einträge | Schlüssel: `nummer`, `zeitstempel`, `bild`, `tiefe`, `konfidenz`, `bildGroesse`, `tiefenGroesse`, `intrinsics`, `kameraZuWelt` |
| `test_frames/frame_NNNN.jpg` | RGB-Bilder, 1920 × 1440 |
| `test_frames/frame_NNNN_depth.bin` | Tiefe, `float32`, Meter, 256 × 192 |
| `test_frames/frame_NNNN_conf.bin` | Konfidenz, `uint8` (0, 1, 2), 256 × 192 |

Die Pfade in `frames.json` lauten `frames/frame_NNNN.jpg`, im Repo liegen die Dateien aber in `test_frames/`.

## Abgleich

| Punkt | Upstream | Room Twin | Status |
|---|---|---|---|
| RoomPlan-USDZ | `room.usdz` im Wurzelordner | `room.usdz` im Wurzelordner | ✅ passt |
| Frame-Metadaten | eine JSON-Datei **pro Frame** | `frame_NNNN.json` für alle 106 Frames erzeugt | ✅ umgesetzt (`cli.py`) |
| Pose-Schlüssel | `cameraPoseARFrame` | aus `kameraZuWelt` umbenannt | ✅ umgesetzt |
| Projektionsmatrix | `projectionMatrix` (4×4), Pflicht im Lader | aus den Intrinsics berechnet, Near 0,01 / Far 100 (Annahme) | ⚠️ Lader akzeptiert, Werte nicht geprüft |
| Intrinsics | `intrinsics`, reshape auf 3×3 | `intrinsics`, 9 Zahlen | ⚠️ Reihenfolge (spalten- oder zeilenweise) zu prüfen |
| Pose-Konvention | ARKit, wird in Upstream in Y/Z gespiegelt | ARKit, spaltenweise | ⚠️ nicht verifiziert |
| RGB-Bilder | im selben Ordner wie die JSON | `frame_NNNN.jpg` im Ausgabeordner kopiert | ✅ umgesetzt |
| Tiefe | `depth_NNNN.png`, mm | aus `.bin` (Meter) als uint16-PNG in mm | ✅ umgesetzt |
| Konfidenz | `conf_NNNN.png`, Pflicht | aus `.bin` (uint8) als PNG | ✅ umgesetzt |
| Lader-Test | `load_scan_frames_no_video` lädt den Ordner | 106 Frames geladen, ohne Fehler | ✅ bestanden |
| Auflösung | Intrinsics gelten für 1920 × 1440, Tiefe wird skaliert | 1920 × 1440 Bild, 256 × 192 Tiefe | ✅ Logik passt |
| Punktwolke | eine der drei Quellen nötig | nur `mesh.obj` | ⚠️ Umweg über Tiefenbilder nötig |

## Stand der Umwandlung

Umgesetzt in `experiments/litereality-agent-poc/cli.py` (Ausgabe außerhalb von Git):

1. ✅ Eine JSON-Datei pro Frame mit `cameraPoseARFrame`, `intrinsics` und `projectionMatrix`.
2. ✅ Tiefenbilder als PNG in Millimetern.
3. ✅ Konfidenzbilder als PNG.
4. ✅ Bilder im selben Ordner wie die Frame-Dateien.
5. ✅ Upstreams Lader lädt alle 106 Frames.
6. ⚠️ Pose- und Intrinsics-Konvention nicht verifiziert.

## Optionen

**Option A: Umwandlung im Backend.** Ein Skript erzeugt aus `frames.json` und den `.bin`-Dateien die Upstream-Struktur. Das ist schnell testbar, braucht aber eine exakt geprüfte Pose-Konvention.

**Option B: Scanner-Export anpassen.** Die iOS-App schreibt direkt das Upstream-Format. Das wäre sauberer, bedeutet aber Änderungen am Swift-Code. Das Issue schließt eine neue Aufnahme-Schnittstelle aus und verlangt dafür ein Folgeticket.

**Empfehlung:** Option A für den PoC, Option B als Folgeticket.

## Folgeticket (Vorschlag)

> **Scanner-Export an LiteReality-Agent anpassen.** Pro Frame eine Datei `frame_NNNN.json` mit `cameraPoseARFrame` und `intrinsics`. Tiefe als 16-Bit-PNG in Millimetern (`depth_NNNN.png`), Konfidenz als PNG (`conf_NNNN.png`). Alle Dateien eines Frames im selben Ordner. Die Pose-Konvention vorher an einem bekannten Beispiel prüfen.

## Wie die Werte umgewandelt werden

Quelle für alle Schritte: `experiments/litereality-agent-poc/cli.py`. Die Eingabedateien werden nie verändert. Der Ausgabeordner wird mit `--output` angegeben und sollte außerhalb von Git liegen.

**Grundregel zur Anordnung der Zahlen.** Unser Datensatz speichert 4×4- und 3×3-Matrizen spaltenweise. Upstream liest sie mit `reshape(...)` zeilenweise. Deshalb wird jede Matrix vor dem Schreiben transponiert und dann zeilenweise geschrieben. Upstream erhält so beim Lesen die ursprüngliche Matrix.

### Pro Frame `frame_NNNN.json` (Nummer mit 4 Stellen)

| Schlüssel | Quelle | Umwandlung | Anzahl Werte |
|---|---|---|---|
| `cameraPoseARFrame` | `kameraZuWelt` aus `frames.json` | 16 Zahlen als 4×4 lesen, transponieren, zeilenweise schreiben | 16 |
| `intrinsics` | `intrinsics` aus `frames.json` | 9 Zahlen als 3×3 lesen, transponieren, zeilenweise schreiben | 9 |
| `projectionMatrix` | berechnet aus den Intrinsics und `bildGroesse` (1920 × 1440) | siehe Formel unten, zeilenweise schreiben | 16 |

**Formel für `projectionMatrix`.** Mit `fx, fy, cx, cy` aus den (transponierten) Intrinsics, `W = 1920`, `H = 1440`, Near `N = 0,01` und Far `F = 100`:

```
[ 2·fx/W      0          (W − 2·cx)/W            0            ]
[ 0        2·fy/H       −(H − 2·cy)/H            0            ]
[ 0           0        −(F + N)/(F − N)   −2·F·N/(F − N)     ]
[ 0           0               −1                0            ]
```

Die zweite Zeile hatte beim ersten Versuch das falsche Vorzeichen (y gespiegelt) und in der zweiten Korrektur ein falsches Vorzeichen beim z-Anteil. Die Prüfung oben zeigt, dass die jetzige Fassung mit der direkten Rechnung aus den Intrinsics übereinstimmt.

**Annahmen, die nicht aus den Daten stammen:** Near `0,01` und Far `100`. Sie beeinflussen nur die z-Zeile der Matrix.

### Pro Frame: Bilder

| Datei | Quelle | Umwandlung |
|---|---|---|
| `frame_NNNN.jpg` | `test_frames/frame_NNNN.jpg` | unverändert kopiert, Ausrichtung nicht gedreht |
| `depth_NNNN.png` | `test_frames/frame_NNNN_depth.bin` | `float32`, 192 × 256, Meter → mit 1000 multiplizieren, runden, auf 0…65535 begrenzen, als `uint16` in Millimeter als PNG schreiben |
| `conf_NNNN.png` | `test_frames/frame_NNNN_conf.bin` | `uint8`, 192 × 256, unverändert als PNG schreiben (Werte 0, 1, 2) |

### Was nicht umgewandelt wird

- **`room.usdz`**: Wird unverändert in den Ausgabeordner kopiert (nur, wenn sie dort fehlt oder eine andere Größe hat). Upstream braucht sie für die Geometrie des Raums.
- **`mesh.obj`, `room.json`, `metadata.json`**: werden nicht verwendet.
- **Zeitstempel (`zeitstempel`)**: wird nicht übernommen.

### Prüfungen (Stand 24.11.2026)

1. **Rechnerischer Vergleich** der Projektion (Intrinsics gegen Projektionsmatrix, gleicher Punkt): Ergebnis stimmt überein.
2. **Upstreams Lader** (`load_scan_frames_no_video`) lädt alle 106 Frames ohne Fehler.
3. **Upstreams Projektion** (`project_point`) gegen unsere Formel über alle 8 Objekte aus `room.json` und alle 106 Frames: 540 Vergleiche vor der Kamera, maximale Abweichung 0,003 Pixel.
4. **Bildtest** mit einem Stuhl in Frame 32 und Frame 95: Der projizierte Mittelpunkt liegt auf dem Stuhl.

**Einschränkung:** Die Bildtests sind visuell und nur für einen Stuhl in zwei Frames. Das stützt die Konvention, ist aber kein vollständiger Beweis.

## Offene Punkte

- Ob die Intrinsics-Reihenfolge stimmt (Spalten- oder Zeilenweise). Das Skript geht von spaltenweise aus, das ist nicht verifiziert.
- Near (0,01) und Far (100) in der `projectionMatrix` sind Annahmen. Sie sind nicht in den Daten enthalten.
- Konsistenztest: Ein Punkt, der über die Intrinsics projiziert wird, sollte im Bild dieselbe Stelle treffen wie über die Projektionsmatrix.
- Ob die Pose-Konvention aus Option A korrekte Geometrie liefert. Das zeigt erst ein Lauf.
- Ob alle 106 Frames eine gültige Pose haben.
- Ob der öffentliche Beispielscan aus `LiteReality/example-scans` besser passt. Das muss der Pflichtlauf zeigen.
    