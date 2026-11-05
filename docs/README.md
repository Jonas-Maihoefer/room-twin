# Dokumentationsübersicht – Room Twin

**Architekturstatus: entschieden.** Room Twin wird als **eigene iOS-App mit Apples RoomPlan-SDK und direkter Backend-Anbindung** umgesetzt. Offene Fragen zu einzelnen Bibliotheken oder Schnittstellendetails ändern diese Festlegung nicht.

## Architektur

1. [Verbindliche Systemarchitektur](architecture/architecture.md) – Komponenten, Verantwortlichkeiten, MVP-Umfang und Integrationsgrenzen.
2. [Systemablauf](architecture/system-flow.md) – ein Datenfluss vom Raumscan zum Modell in der App.
3. [Technikstack](architecture/tech-stack.md) – feste Anforderungen und zu validierende Implementierungstechnologien.

## Verifikation

- [iOS-/RoomPlan-Integration und Ende-zu-Ende-Tests](testing/ios-roomplan-validation.md) – Nachweis der realen Scan-zu-Modell-Pipeline auf einem unterstützten Gerät.

## Aktueller Stand

Dieses Repository enthält noch keine Implementierung von App oder Backend. Die beschriebenen Abläufe und Testfälle sind **Zielzustand bzw. Testplan**, nicht schon erfolgreich getestete Funktionen.
