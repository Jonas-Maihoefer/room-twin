# Architekturentscheidung – noch offen

> **Kein Beschluss.** Beide Architekturvarianten müssen mit dem Betreuer besprochen werden. Weder eine eigene iOS-App noch die Nutzung einer bestehenden Scanner-App ist bisher verbindlich vorgesehen.

[Dokumentationsübersicht](../README.md) · [Variante 1](option-1-external-scanner.md) · [Variante 2](option-2-integrated-ios-app.md) · [Handytests](../testing/handytests.md)

## Ausgangsfrage

Soll die Entwicklung zunächst möglichst schnell zu einer funktionierenden Scan-Verarbeitungspipeline führen oder schon im ersten Prototyp einen nahtlosen Scan-bis-Modell-Ablauf in einer eigenen App bieten?

| Kriterium | Architektur 1: externe App | Architektur 2: eigene iOS-App |
|---|---|---|
| Scannen | Bestehende LiDAR-App | Eigenes Frontend mit RoomPlan-SDK |
| Übergabe an Pipeline | Export und erneuter Import/Upload | Direkter Upload aus der App |
| Nutzbarkeit | Mehrere manuelle Schritte | Integrierter Ablauf |
| Früher Entwicklungsfokus | Backend und Modellqualität | Zusätzlich mobile UI, native Integration und Signing |
| Zentrales Risiko | Kostenloser vollständiger JSON-Export nicht bestätigt | Höherer Setup- und Integrationsaufwand |
| Ergebnis | Download/Dateiablage | In-App Download; Viewer/Editor optional später |

Die Einstufung des Entwicklungsaufwands ist eine **Einschätzung**, nicht das Ergebnis eines Benchmarks.

## Vor einer Entscheidung mit dem Betreuer klären

- Ist ein funktionsfähiger **Backend-Prototyp** wichtiger als eine integrierte Nutzeroberfläche?
- Wer wird das Produkt verwenden und wie oft scannen?
- Ist ein manueller Dateiexport/-upload akzeptabel?
- Welche Ausgabeformate sind verpflichtend: GLB und/oder BLEND?
- Welche Objektmetadaten müssen erhalten bleiben, damit Asset-Replacement funktioniert?
- Welche Geräte, Entwicklungsrechner, Signing-Möglichkeiten und Hosting-Ressourcen stehen bereit?
- Welche Datenschutzanforderungen gelten für Scan-Uploads und Beispieldaten?

## Bedeutung des Handytests

Der [Handytest](../testing/handytests.md) überprüft eine zentrale Annahme der **ersten** Architektur: Kann eine bereits erhältliche App kostenlos und wiederholbar JSON mit Möbelkategorien, Dimensionen, 3D-Transformationen und Raumgeometrie exportieren?

- **Ja:** Architektur 1 wird als schneller Pipeline-Einstieg realistischer.
- **Teilweise:** Fehlende Felder und Abweichungen dokumentieren, weitere Apps und Konvertierung prüfen.
- **Nein:** Weitere Datenquellen suchen oder Architektur 2 stärker gewichten.

Ein erfolgreicher Handytest bedeutet **nicht automatisch**, dass Architektur 1 gewählt wird.

## Entscheidungsprotokoll

| Feld | Stand |
|---|---|
| Entscheidung | **Offen** |
| Abstimmung mit Betreuer | **Ausstehend** |
| Ausgewertete Handytests | **Noch keine Ergebnisse dokumentiert** |
| Begründung / Beschlussdatum | Nach Gespräch ergänzen |

[System-Flows](system-flow.md) · [Technologieoptionen](tech-stack.md)
