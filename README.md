# Room Twin

Room Twin entwickelt aus LiDAR-Raumscans weiterverarbeitbare 3D-Raummodelle. Die erkannten Räume und Einrichtungsgegenstände werden aufbereitet und erkannte Möbel durch passende 3D-Assets ersetzt.

## Verbindliche Architektur

**Room Twin wird als eigene iOS-App mit Apples RoomPlan-SDK umgesetzt.** Der Scan findet direkt in der App statt. Die App überträgt die strukturierten Scan-Daten über eine API an das Backend. Dort werden Raumgeometrie und Objekte verarbeitet, 3D-Assets platziert und ein 3D-Modell erzeugt. Die App stellt das Ergebnis zum Herunterladen und Teilen bereit.

```mermaid
flowchart LR
    A[Room-Twin-iOS-App mit RoomPlan] --> B[Direkter API-Upload]
    B --> C[Backend: Geometrie und Asset-Verarbeitung]
    C --> D[3D-Modell als GLB]
    D --> E[Download und Teilen in der App]
```

## MVP-Ziel

1. Scan über RoomPlan in der eigenen iOS-App auf einem unterstützten LiDAR-Gerät durchführen.
2. Semantische Raum- und Objektdaten mitsamt Abmessungen und Transformationen für die API aufbereiten und direkt übertragen.
3. Im Backend mindestens ein erkanntes Objekt durch ein passendes, korrekt skaliertes und positioniertes 3D-Asset ersetzen.
4. Das generierte Modell als GLB an die App zurückgeben und dort zum Herunterladen/Teilen anbieten.

Ein integrierter 3D-Viewer oder Editor ist eine spätere Erweiterung und **keine Voraussetzung für den MVP**.

## Projektstand

Die Architektur ist **entschieden und dokumentiert**. Das Repository enthält bisher Dokumentation, noch keine lauffähige iOS-App oder Backend-Pipeline. Konkrete Frameworks und Bibliotheken sind teilweise noch zu validieren; die Systemarchitektur selbst steht fest.

## Dokumentation

- [Systemarchitektur und MVP-Grenzen](docs/architecture/architecture.md)
- [Systemablauf und Datenfluss](docs/architecture/system-flow.md)
- [Technikstack: verbindliche Vorgaben und Implementierungsdetails](docs/architecture/tech-stack.md)
- [RoomPlan-iOS- und Ende-zu-Ende-Testplan](docs/testing/ios-roomplan-validation.md)
- [Dokumentationsübersicht](docs/README.md)
