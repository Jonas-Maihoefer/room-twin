# Systemarchitektur – eigene iOS-App mit RoomPlan

> **Verbindliche Architektur:** Room Twin besteht aus einer eigenen iOS-App mit Apples RoomPlan-SDK und einem angebundenen Backend zur 3D-Modellgenerierung. Die App lädt strukturierte Scandaten direkt über die API hoch.

[Dokumentationsübersicht](../README.md) · [Systemablauf](system-flow.md) · [Technikstack](tech-stack.md) · [Testplan](../testing/ios-roomplan-validation.md)

## Zielbild

Die **Room-Twin-iOS-App** erfasst den Raum mit RoomPlan und liest die von Apple bereitgestellten semantischen Raum- und Objektdaten aus. Sie überführt diese Daten in ein mit dem Backend abgestimmtes Übertragungsformat und sendet sie **direkt über die API**. Das Backend erstellt unter Verwendung einer 3D-Asset-Bibliothek eine Szene und stellt das Ergebnis als **GLB** bereit. Die App kann das Modell herunterladen und teilen.

## Komponenten und Zuständigkeiten

| Komponente | Verantwortung |
|---|---|
| Eigene iOS-App | Scan starten/abschließen, Fortschritt und Fehler anzeigen, Daten aufbereiten und an die API senden, Ergebnis abrufen/teilen |
| Native RoomPlan-Integration | LiDAR-basierte Erfassung und Zugriff auf semantische Daten mit Apples RoomPlan-SDK |
| Datenmodell für den Upload | Raumflächen, Objektkategorien, Dimensionen und räumliche Transformationen konsistent abbilden |
| Backend-API | Upload annehmen und validieren, Verarbeitung starten, Fehler behandeln und Ergebnis bereitstellen |
| Geometrie-/Asset-Pipeline | Raumgeometrie interpretieren, Ersatz-Assets auswählen, skalieren, transformieren und in eine Szene einsetzen |
| 3D-Asset-Bibliothek | Geeignete Modelle für erkannte Objektkategorien bereitstellen |
| Modell-Export | Eine nutzbare **GLB-Datei** generieren |

## Verbindlicher Ablauf

1. Nutzer startet und beendet die Erfassung **innerhalb der Room-Twin-App** auf einem unterstützten LiDAR-fähigen iOS-Gerät.
2. Die App erhält strukturierte RoomPlan-Daten zu Raumflächen, Öffnungen und erkannten Objekten.
3. Die App erzeugt daraus einen vereinbarten API-Payload. Das RoomPlan-SDK definiert **nicht automatisch das endgültige Backend-JSON-Schema**.
4. Die App überträgt den Payload direkt und abgesichert an das Backend.
5. Das Backend prüft Eingabedaten und Koordinatensysteme, verarbeitet Raumgeometrie und setzt passende 3D-Assets ein.
6. Das Backend stellt eine GLB-Datei bereit, die die App abruft und herunterladbar/teilbar macht.

Der [Systemablauf](system-flow.md) zeigt die Schritte als Diagramm.

## Schnittstellen und Datenqualität

Die semantischen Scandaten müssen, soweit von RoomPlan erfasst, Raum- und Oberflächengeometrie, Öffnungen, Objektkategorien, Abmessungen, Positionen und Orientierungen erhalten. Maßstäbe und Koordinatensysteme sind zwischen App, Backend und Asset-Bibliothek konsistent zu definieren.

**Noch auszuarbeiten innerhalb dieser Architektur:** versioniertes API-Datenformat, Endpunkte, Fehlermodell, Uploadgrößen und Timeouts, Authentifizierung, temporäre Speicherung und Ergebnisabruf. Diese Implementierungsdetails stellen die Architektur nicht infrage.

## Umfang des ersten MVP

**Machbarkeitsnachweis:** `Scan in eigener App → RoomPlan-Daten → direkter Backend-Upload → korrekt platziertes Ersatz-Asset → GLB → Download/Teilen in der App`.

Ein integrierter 3D-Viewer/Editor ist eine **optionale spätere Erweiterung** und nicht Bestandteil des ersten MVP. Zusätzliche Exportformate wie BLEND gehören zunächst ebenfalls nicht dazu.

## Voraussetzungen und Risiken

- **Gerät:** Ein mit RoomPlan kompatibles, LiDAR-fähiges iPhone bzw. iPad mit unterstützter iOS-Version ist für reale Scans erforderlich.
- **Native Anbindung:** RoomPlan erfordert iOS-native Integration. Bei Expo reicht Expo Go nicht; ein eigener Development Build ist nötig.
- **Signierung:** Tests auf einem physischen Gerät benötigen einen passend signierten Build; eine App-Store-Veröffentlichung ist dafür nicht erforderlich.
- **Datenqualität:** Unvollständige Erkennung und fehlende Angaben müssen kontrolliert behandelt und anhand realer Räume überprüft werden.
- **Datenschutz:** Indoor-Scans können sensible Informationen enthalten. Übertragung absichern und keine privaten Scans unkontrolliert ins öffentliche Repository übernehmen.

Die konkrete Wahl einzelner Implementierungsbibliotheken und erforderliche Machbarkeitstests sind im [Technikstack](tech-stack.md) und [Testplan](../testing/ios-roomplan-validation.md) dokumentiert.
