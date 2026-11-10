# Testplan – RoomPlan in der eigenen iOS-App

**Status: geplant; noch nicht durchgeführt.** Der Testplan dient der Verifikation der festgelegten Architektur: eigene iOS-App mit Apple RoomPlan und direkter Backend-Anbindung.

[Systemarchitektur](../architecture/architecture.md) · [Systemablauf](../architecture/system-flow.md) · [Technikstack](../architecture/tech-stack.md)

## Testziel

Ein realer Raum wird in der eigenen App gescannt, die erfassten semantischen Daten werden direkt an die Backend-API übertragen und dort in ein GLB-Modell umgesetzt. Mindestens ein erkanntes Objekt wird durch ein geeignetes, korrekt positioniertes und skaliertes 3D-Asset ersetzt.

## Voraussetzungen

- Von RoomPlan unterstütztes LiDAR-fähiges iPhone oder iPad mit passender iOS-Version.
- Auf dem Gerät installierter, signierter App-Build mit nativer RoomPlan-Integration; bei Expo ein **Development Build**, nicht nur Expo Go.
- Erreichbares Test-Backend, abgestimmtes Upload-Schema und geeignete Ersatz-Assets.
- Test-Raum mit messbaren Objekten und Flächen; Einwilligung zur Datennutzung.
- Für gespeicherte Testdaten ausschließlich freigegebene oder anonymisierte Beispiele verwenden.

## Testfälle

| Schritt | Erwartetes Ergebnis |
|---|---|
| App starten | App läuft auf echtem Gerät; Berechtigungen und Fehlerzustände sind verständlich |
| Scan durchführen | RoomPlan-Scan lässt sich starten, abschließen und auslesen |
| Raumdaten inspizieren | Kategorien, Abmessungen, Positionen, Orientierungen und Flächen sind nachvollziehbar |
| API-Payload erzeugen | Schema ist gültig und Einheiten/Koordinatentransformationen bleiben konsistent |
| Direkt hochladen | App überträgt die Daten an die API; Uploadfehler werden behandelt |
| Assets einsetzen | Backend platziert mindestens ein Ersatz-Asset im erwarteten Maßstab und an der richtigen Position |
| GLB generieren | Datei kann unabhängig geöffnet und auf Plausibilität geprüft werden |
| Ergebnis bereitstellen | Die App kann die GLB-Datei herunterladen und teilen |
| Fehlerfälle auslösen | Fehlende Berechtigungen, ungültige Daten, Netzwerkunterbrechung und Serverfehler sind kontrolliert behandelbar |

## Qualitätssicherung

Raumgeometrie, Wände/Öffnungen, Möbelkategorien, Abmessungen, Positionen und Rotationen mit dem realen Raum vergleichen. Fehlende oder falsch erkannte Merkmale dokumentieren. Freigegebene, anonymisierte API-Fixtures sind hilfreich für reproduzierbare Backendtests; sie ersetzen **keine reale Geräteintegration**.

Für jeden Testlauf Datum, Gerätemodell, iOS-Version, App-Build, RoomPlan-/Wrapper-Version, Backend-Commit und Ergebnisse je Testfall dokumentieren. Ggf. nur unbedenkliche, freigegebene Artefakte verlinken.

## MVP-Abnahmekriterium

Der Ablauf **Scan in eigener App → strukturierte Daten → direkter Upload → Ersatz-Asset → GLB → Download/Teilen** funktioniert auf einem realen unterstützten Gerät. Die Lage und Skalierung mindestens eines Ersatzobjekts sind überprüft.

**Dieses Kriterium gilt erst nach einem dokumentierten erfolgreichen Test als erfüllt.**
