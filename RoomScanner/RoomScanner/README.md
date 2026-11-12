# RoomScanner

iOS-App (Swift, RoomPlan + ARKit), die einen Raum mit dem LiDAR-Scanner des iPhones scannt und die Daten für die Digital-Twin-Pipeline exportiert.

## Export-Struktur

```
scan_YYYY-MM-DD_HH-mm-ss/
├── README.md            diese Datei
├── metadata.json        Infos zum Scan
├── room.json            RoomPlan-Ergebnis (semantisch)
├── room.usdz            RoomPlan-Ergebnis (3D-Modell)
├── frames.json          Kamera-Parameter und Pose pro Frame
└── frames/
    ├── frame_0001.jpg           Kamerabild
    ├── frame_0001_depth.bin     Tiefenbild
    ├── frame_0001_conf.bin      Konfidenz
    ├── frame_0002.jpg
    └── …
```

## Die Dateien im Detail

### `metadata.json`

| Feld | Bedeutung |
|---|---|
| `scanID` | Name des Scan-Ordners |
| `datum` | Startzeit des Scans (`YYYY-MM-DD_HH-mm-ss`) |
| `geraet` | Gerätetyp, z. B. `iPhone` |
| `iosVersion` | iOS-Version, z. B. `26.2` |
| `einheit` | immer `Meter` |
| `koordinatensystem` | Kurzbeschreibung, siehe unten |
| `dateien` | Liste der enthaltenen Dateien |

### `room.json`

Das RoomPlan-Ergebnis (`CapturedRoom`), von Apple direkt als JSON exportiert. Es enthält Listen wie `walls`, `doors`, `windows`, `openings`, `floors` und `objects`. Jedes Element hat unter anderem:

| Feld | Bedeutung |
|---|---|
| `identifier` | eindeutige ID |
| `category` | Art des Elements, als Objekt mit **einem Schlüssel**: `{"wall": {}}`, `{"window": {}}`, `{"table": {}}`, `{"chair": {}}`, `{"storage": {}}` … Bei Türen steht darin auch, ob sie offen ist: `{"door": {"isOpen": true}}` |
| `dimensions` | Größe in Metern: `[Breite, Höhe, Tiefe]` |
| `transform` | 4×4-Matrix, **spaltenweise** (16 Zahlen): Position und Drehung im Raum. Die Position steht in den Einträgen 12, 13, 14 |
| `confidence` | ebenfalls als Objekt: `{"high": {}}`, `{"medium": {}}` oder `{"low": {}}` |

Beispiel für ein Objekt (gekürzt):

```json
{
  "identifier": "A7743BD1-…",
  "category": { "storage": {} },
  "confidence": { "low": {} },
  "dimensions": [1.20, 0.69, 0.42],
  "transform": [ 16 Zahlen ]
}
```

In Python liefert `next(iter(element["category"]))` den Namen als Text, hier `"storage"`.

Das genaue Schema legt Apple fest und kann sich mit neuen iOS-Versionen leicht ändern.

### `room.usdz`

Vereinfachtes 3D-Modell von RoomPlan: Wände als Flächen, Möbel als Boxen. Lässt sich am Mac per Quick Look anschauen und in Blender oder Unity (mit USD-Importer) öffnen.

### `frames.json`

```json
{
  "hinweise": [ "…" ],
  "frames": [
    {
      "nummer": 1,
      "zeitstempel": 95697.75,
      "bild": "frames/frame_0001.jpg",
      "tiefe": "frames/frame_0001_depth.bin",
      "konfidenz": "frames/frame_0001_conf.bin",
      "bildGroesse": [1920, 1440],
      "tiefenGroesse": [256, 192],
      "intrinsics": [ 9 Zahlen ],
      "kameraZuWelt": [ 16 Zahlen ]
    }
  ]
}
```

| Feld | Bedeutung |
|---|---|
| `zeitstempel` | ARKit-Zeit des Frames in Sekunden |
| `bildGroesse` | `[Breite, Höhe]` des Kamerabilds |
| `tiefenGroesse` | `[Breite, Höhe]` des Tiefenbilds |
| `intrinsics` | Kamera-Matrix 3×3, **spaltenweise**. Gilt für `bildGroesse`, für das Tiefenbild mit `tiefenBreite / bildBreite` skalieren |
| `kameraZuWelt` | 4×4-Matrix, **spaltenweise**. Wandelt Kamera-Koordinaten in Welt-Koordinaten um |
| `konfidenz` | kann `null` sein, falls es für dieses Frame keine Konfidenzkarte gab |

Frames ohne Tiefenbild werden gar nicht gespeichert.

### `frames/frame_XXXX.jpg`

Kamerabild in sRGB, typischerweise 1920 × 1440. **Sensor-Ausrichtung (Querformat), nicht gedreht.** Bitte nicht drehen, sonst passen Bild, Tiefe und Intrinsics nicht mehr zusammen.

### `frames/frame_XXXX_depth.bin`

Rohdaten des LiDAR-Tiefenbilds:
- `float32`, **little-endian**
- Entfernung in **Metern**
- Zeile für Zeile, Größe laut `tiefenGroesse` (typisch 256 × 192 = **196.608 Bytes**)
- ebenfalls in Sensor-Ausrichtung

### `frames/frame_XXXX_conf.bin`

Konfidenz zu jedem Tiefenpixel:
- `uint8`, Werte `0` = niedrig, `1` = mittel, `2` = hoch
- Zeile für Zeile, gleiche Größe wie das Tiefenbild (typisch **49.152 Bytes**)

## Koordinatensysteme

- **Welt (ARKit):** Meter, rechtshändig, **y zeigt nach oben** (Schwerkraft). Der Ursprung ist die Position des iPhones beim Start des Scans. `room.json` und alle Frames liegen im **selben** Weltkoordinatensystem.
- **Kamera (ARKit):** x nach rechts, y nach oben, z nach hinten. Die Kamera **schaut in −z**. Bezieht sich auf das Sensor-Querformat.
- **Bildpixel:** `u` nach rechts, `v` nach unten, Ursprung oben links.
- **Matrizen** werden **spaltenweise** gespeichert (wie in Swift/simd). In NumPy: `np.array(liste).reshape(n, n).T`
