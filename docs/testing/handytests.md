# Handytests – kostenlose RoomPlan-JSON-Exporte

> **Teststatus: geplant, noch keine Ergebnisse dokumentiert.** Das vorhandene PDF ist ein **Testprotokoll**, kein Beweis dafür, dass die Kandidaten tatsächlich geeignete JSON-Dateien liefern.

[Dokumentationsübersicht](../README.md) · [Architektur 1](../architecture/option-1-external-scanner.md) · [Architektur 2](../architecture/option-2-integrated-ios-app.md) · [Entscheidung](../architecture/decision.md)

**[Originales PDF-Testprotokoll im Repository öffnen](../../test/architecture%20research/Room_Twin_Handytests_RoomPlan_JSON-1.pdf)**

## Wofür brauchen wir den Test?

[Architektur 1](../architecture/option-1-external-scanner.md) funktioniert nur dann als einfacher Einstieg, wenn eine bestehende App **kostenlos verwertbare Raumdaten** exportieren kann. Ein JSON-Dateiname oder ein erfolgreicher Download allein reicht nicht. Die Pipeline benötigt semantische Objekt- und Geometriedaten. Die App-Store-Angaben sind noch nicht mit echten Exportdateien validiert.

## Testkandidaten laut PDF

| App | Recherche-/Planstand – **noch nicht bestätigt** |
|---|---|
| RoomTrace | JSON- und USDZ-Export beschrieben, angeblich kostenlos |
| RoomSheet | JSON-Export für Weiterverarbeitung beschrieben, angeblich kostenlos |
| LiDAR Room Scanner: Grundriss | RoomPlan-JSON und USDZ genannt; kostenlose Scans begrenzt |
| FIMIT (optional) | JSON genannt; Gratis-Export unklar |

App-Store-Links, Voraussetzungen und ausführliche Testschritte stehen im [PDF](../../test/architecture%20research/Room_Twin_Handytests_RoomPlan_JSON-1.pdf). Kosten und Exportumfang **auf dem Gerät verifizieren**.

## Praktische Durchführung

1. LiDAR-fähiges iPhone und einen überschaubaren Raum mit Tisch/Stuhl, Tür/Fenster vorbereiten. Datum, iPhone-Modell, iOS- und App-Version erfassen.
2. Möglichst **denselben Raum** mit RoomTrace und RoomSheet scannen. Danach ggf. die beiden weiteren Apps prüfen.
3. JSON **ohne Kauf** exportieren; wenn möglich auch USDZ als visuelle Referenz.
4. Dateien auf einen Entwicklungsrechner übertragen und eindeutig benennen.
5. JSON in einem Editor oder Parser öffnen, prüfen, ob es valide und inhaltlich aussagekräftig ist.
6. Erfasste Möbel und Raumgeometrie mit dem echten Raum abgleichen.
7. Die Ergebnisse dokumentieren und anschließend mit dem Betreuer besprechen.

Für eine schnelle JSON-Syntaxprüfung: `python -m json.tool scan.json` (prüft **nicht** die inhaltliche Eignung).

## Konkrete technische Checkliste

| Kriterium | Bedeutung |
|---|---|
| Valides JSON | Automatisch lesbar |
| Möbelkategorien (chair, table, …) | Passende 3D-Assets auswählen |
| 3D-Dimensionen | Modellskalierung |
| Position, Orientierung, Transformation | Möbel korrekt platzieren |
| Wände, Öffnungen, ggf. Boden | Raumgeometrie aufbauen |
| Mehrere Objekte unterscheidbar | Spätere Zuordnung und Editierung |
| Kostenlos und wiederholbar | Realistische Nutzung ohne unklare Schranken |

**Wichtig:** Ein Drittanbieter-JSON kann vom Apple-RoomPlan-Schema abweichen; gegebenenfalls ist ein kleiner Konverter nötig.

## Ergebnistabelle zum Nachtragen

| App | JSON kostenlos? | Möbel/Geometrie vollständig? | Transformationsdaten? | Ergebnis |
|---|---|---|---|---|
| RoomTrace | Offen | Offen | Offen | Nicht getestet |
| RoomSheet | Offen | Offen | Offen | Nicht getestet |
| LiDAR Room Scanner: Grundriss | Offen | Offen | Offen | Nicht getestet |
| FIMIT | Offen | Offen | Offen | Nicht getestet |

## Konsequenz für die Entscheidung

**Wenn** die Tests brauchbare JSON-Dateien ergeben, ist die [Architektur 1](../architecture/option-1-external-scanner.md) als einfacher MVP-Einstieg plausibel. **Wenn nicht**, muss die Datenbeschaffung über weitere Scanner oder [Architektur 2](../architecture/option-2-integrated-ios-app.md) neu bewertet werden. Die Entscheidung selbst bleibt [mit dem Betreuer offen](../architecture/decision.md).

**Datenschutz:** Das Repository ist öffentlich. Keine privaten oder vertraulichen Innenraumscans ohne Freigabe hochladen; lieber freigegebene/anonymisierte Fixtures verwenden.
