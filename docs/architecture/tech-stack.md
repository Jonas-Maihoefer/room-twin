# Technikstack – Room Twin

**Die Systemarchitektur ist festgelegt:** eigene iOS-App, Apple RoomPlan zur Erfassung, direkter Upload an ein Backend zur Geometrie- und Asset-Verarbeitung sowie GLB als MVP-Ergebnis. Nicht alle konkreten Frameworks und Bibliotheken sind schon technisch validiert.

[Systemarchitektur](architecture.md) · [Systemablauf](system-flow.md) · [Testplan](../testing/ios-roomplan-validation.md)

## Verbindliche technische Vorgaben

| Bereich | Festlegung |
|---|---|
| Client | **Eigene iOS-App** mit integrierter Scanfunktion |
| Erfassung | **Apple RoomPlan-SDK**, native iOS-Anbindung und kompatibles LiDAR-Gerät |
| Datentransfer | **Direkter API-Upload aus der App** mit semantischen Raum- und Objektdaten |
| Verarbeitung | Backend-Pipeline für Geometrie, Ersatz-Assets und 3D-Szene |
| MVP-Ergebnis | **GLB**, abruf- und teilbar über die App |
| Weiterer Ausbau | In-App-Viewer und -Editor erst nach dem MVP |

## Geplante, noch zu validierende Umsetzungstechnologien

| Bereich | Ausgangspunkt | Zu prüfen |
|---|---|---|
| App-Oberfläche | React Native + Expo | Native Module, Build-Workflow und iOS-Kompatibilität |
| RoomPlan-Anbindung | Native Swift-Bridge bzw. geeigneter Wrapper, etwa `expo-roomplan` | SDK-Abdeckung, Kompatibilität und Funktionsfähigkeit auf echtem Gerät |
| Backend-Sprache | Python | Datentransformationen und Geometriebearbeitung |
| Backend-API | FastAPI | Validierter Upload, Status, Fehler und Ergebnisabruf |
| 3D-Verarbeitung | trimesh, ggf. ergänzende Werkzeuge | Transformationen, Modellimport, Szenenaufbau und stabiler GLB-Export |
| Ersatzmodelle | Lokale GLB-Asset-Bibliothek | Kategorien, Skalierung, Lizenzen und Laufzeit |

Diese Kandidaten sind **Implementierungsentscheidungen innerhalb der beschlossenen Architektur**, keine zur Wahl stehenden Systemvarianten. Insbesondere darf die bloße Verfügbarkeit eines RoomPlan-Wrappers nicht als erfolgreich nachgewiesene Gerätekompatibilität gelten.

## Datenformate

- **Erfassung:** strukturierte RoomPlan-Ergebnisse. Die App mappt diese in ein mit dem Backend abgestimmtes, versioniertes API-Format.
- **Interne Verarbeitung:** Räume, Oberflächen, Öffnungen und Objekte mit Kategorien, IDs, Dimensionen und Transformationen.
- **MVP-Ausgabe:** GLB als transportierbare 3D-Szene.
- **Weitere Formate:** nur auf gesonderte Anforderung; etwa BLEND könnte eine zusätzliche Verarbeitung erfordern.

## Entwicklungsumgebung

RoomPlan muss auf unterstützter Apple-Hardware erprobt werden. Bei Expo ist für native Module ein eigener **Development Build** nötig; Expo Go allein genügt nicht. Der Geräte-Build und sein Signing sind früh nachzuweisen. Die reale End-to-End-Pipeline wird anhand des [Testplans](../testing/ios-roomplan-validation.md) geprüft.
