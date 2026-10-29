# Room Twin

> **Status: Architektur noch offen.** Die Architektur muss mit dem **Betreuer** abgestimmt werden. Die hier beschriebenen Wege sind Alternativen, keine bereits beschlossenen Implementierungen.

Room Twin untersucht, wie aus einem indoor-LiDAR-Raumscan ein weiterverarbeitbares 3D-Modell entsteht. Die Verarbeitung könnte erkannte Möbel anhand semantischer Raumdaten durch passende 3D-Assets ersetzen.

## Zwei mögliche Architekturen

| | Variante 1 | Variante 2 |
|---|---|---|
| Scanner | Bestehende iOS-Scanner-App | Eigene iOS-App mit Apple RoomPlan |
| Datentransfer | Export und manueller Upload | Direkte Übertragung zum Backend |
| Fokus | Verarbeitungspipeline möglichst früh entwickeln | Integriertes Nutzererlebnis |
| Status | Offen | Offen |

- [Architektur 1: Externe Scanner-App](docs/architecture/option-1-external-scanner.md)
- [Architektur 2: Eigene iOS-App](docs/architecture/option-2-integrated-ios-app.md)
- [Vergleich und Entscheidungspunkte](docs/architecture/decision.md)
- [Handytests: Warum sie benötigt werden](docs/testing/handytests.md)
- [Gesamte Dokumentationsübersicht](docs/README.md)

## Nächster Schritt

Ein [Handytest](docs/testing/handytests.md) prüft, ob Drittanbieter-Apps **kostenlos verwertbares RoomPlan-JSON** exportieren. Das [Testprotokoll liegt als PDF im Repository](test/architecture%20research/Room_Twin_Handytests_RoomPlan_JSON-1.pdf). Diese Ergebnisse unterstützen das Gespräch mit dem Betreuer; sie ersetzen die Entscheidung nicht.
