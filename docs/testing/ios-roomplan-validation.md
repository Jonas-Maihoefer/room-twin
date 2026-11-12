# Testplan – Native RoomPlan-App und USDZ-Ersatzmodelle

**Status (12.11.2026):** Ein echter Scan mit der **Swift-/SwiftUI-App** ist gelungen. Die vollständige Kette **iPhone → FastAPI → Python/OpenUSD → ersetzte USDZ → iPhone** ist noch **nicht** implementiert oder nachgewiesen.

[Architektur](../architecture/architecture.md) · [Systemablauf](../architecture/system-flow.md) · [Technikstack](../architecture/tech-stack.md)

## Bereits vorliegende Nachweise

- Die native App unter `RoomScanner/` (übernommen aus dem Branch `roomplanarkitapp`) verwendet Apples RoomPlan und ARKit; für echte Scans werden Xcode/macOS und ein unterstütztes LiDAR-Gerät benötigt.
- Der erste reale Scan liegt in `backend/testdata/`: `room.usdz`, `room.json` und `metadata.json`. Laut Metadaten wurde er am **11.11.2026** auf einem iPhone mit **iOS 27.0.1** aufgezeichnet; Meter und Y-up-Koordinaten sind angegeben.
- Das JSON enthält vier Wände, einen Boden, zwei Türen, ein Fenster und acht erkannte Objekte (drei Stühle, zwei Tische, zwei Stauraum-Objekte und ein Bett).
- Die App kann bereits lokal exportierte USDZ-Dateien über Quick Look anzeigen und Dateien teilen. **Ein Backend-Upload wurde noch nicht getestet, da er nicht implementiert ist.**

## Testfälle für den Backend-Prototyp (noch offen)

| Test | Erwartung |
| --- | --- |
| USDZ öffnen | `usd-core` lädt die vollständige Szene einschließlich ihrer internen USDA-/USDC-Referenzen |
| UUID-Abgleich | Objekte aus `room.json` werden den entsprechenden USD-Prims eindeutig zugeordnet |
| Modellauswahl | Passende Kategorie/Attribute führen zu einem gültigen Modell aus dem Katalog |
| Platzierung | Position, Drehung, Skalierung, Achsen und Einheiten stimmen mit dem erkannten Objekt überein |
| Bestandsschutz | Wände, Boden, Türen, Fenster und nicht ersetzte Objekte bleiben erhalten |
| Fehlendes Modell | Original-Platzhalter bleibt erhalten, Fehler wird dokumentiert |
| Verpackung | Neue `.usdz` ist selbstständig ladbar und enthält alle referenzierten Geometrien/Materialien |
| Darstellung | Ergebnis lässt sich in einem unabhängigen USDZ-Viewer sowie auf dem iPhone plausibel prüfen |
| Robustheit | Defekte Archive, falsche IDs, zu große Dateien und inkonsistente Metadaten werden kontrolliert abgewiesen |

Regressions- und Geometrieprüfungen gegen `backend/testdata/` sind erforderlich. Der Apple-Katalog ist nur ein erster Referenzsatz; er deckt nicht alle erkannten Möbel des Testscans ab.

## End-to-End-Testfälle (erst nach API-Integration)

1. Scan mit der Swift-App starten, abschließen und die drei Quelldateien erzeugen.
2. Über die künftig implementierte und abgesicherte FastAPI-Schnittstelle USDZ, JSON und Metadaten übertragen.
3. Verarbeitungsstatus, Fehlermeldungen und Ergebnisbereitstellung prüfen.
4. Nachweislich mindestens ein Möbelstück durch ein detailliertes Asset ersetzen, ohne Raumgeometrie zu beschädigen.
5. Fertige **USDZ** auf das iPhone laden, mit Quick Look ansehen und teilen.
6. Netzwerkausfall, ungültige Dateien, fehlende Berechtigungen und einen zweiten Scan testen.

Ergebnis je Lauf mit Gerätemodell, iOS-Version, App-Commit, Backend-Commit, Testscan und Auffälligkeiten dokumentieren. Private Räume und Kamerabilder nicht veröffentlichen.

## MVP-Abnahme

Erst wenn **nativer RoomPlan-Scan → FastAPI-Upload → Python/`usd-core`-Möbelersetzung → gültige neue USDZ → Anzeige/Teilen auf dem iPhone** nachweislich funktioniert, ist die gesamte Pipeline abgenommen.

Der reale Ausgangsscan erfüllt bereits die **Capture-/Export-Voraussetzung**, ersetzt aber weder einen Backend-Test noch einen vollständigen Ende-zu-Ende-Test.
