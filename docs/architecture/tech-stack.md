# Technologieoptionen – noch nicht entschieden

> **Korrektur:** Die ursprüngliche Fassung beschrieb React Native/Expo, FastAPI, trimesh und GLB als fest beschlossene Architektur. Tatsächlich sind dies **Kandidaten**. Die Auswahl erfolgt nach [Abstimmung mit dem Betreuer](decision.md).

[Dokumentation](../README.md) · [Architektur 1](option-1-external-scanner.md) · [Architektur 2](option-2-integrated-ios-app.md) · [Handytests](../testing/handytests.md)

## Datenerfassung und UI

| Vorschlag | Möglicher Einsatz | Offene Fragen |
|---|---|---|
| Bestehende LiDAR-/RoomPlan-App | **Architektur 1** | JSON wirklich kostenlos, vollständig, wiederholbar? → [Handytests](../testing/handytests.md) |
| Kleines Webtool oder CLI-Upload | Architektur 1 | Wie viel UI braucht ein MVP tatsächlich? |
| React Native + Expo | **Architektur 2** | Eignung des nativen RoomPlan-Wrappers, Builds/Signing |
| Apple RoomPlan über expo-roomplan | Architektur 2 | Native Exportdaten und SDK-Kompatibilität am iPhone testen |
| Three.js / React Three Fiber | Optionale spätere Ergänzung | Aufwendiges Mobile-3D-Rendering und Editing erst nach MVP prüfen |

## Backend (beide Varianten)

| Vorschlag | Nutzen | Status |
|---|---|---|
| Python | Datenparsing, Transformationen, Geometrie | Kandidat |
| FastAPI | Upload und Ergebnisbereitstellung | Kandidat; für ersten lokalen Test nicht zwingend |
| trimesh | 3D-Asset-Transformation, Szenenaufbau, GLB | Kandidat; konkrete Anforderungen zuerst testen |
| Lokale GLB-Asset-Bibliothek | Erste Ersatzmöbel | Einfacher Start ohne Cloud-Storage |
| Blender | Falls BLEND-Dateien zwingend nötig sind | Nicht beschlossen; eigener Verarbeitungsschritt möglich |

## Datenformate

- **Input:** idealerweise **semantisches RoomPlan-JSON**, optional **USDZ** als visuelle Referenz. Die tatsächlich verfügbare Struktur ist zunächst im [Handytest](../testing/handytests.md) zu prüfen.
- **Intern:** möglichst ein einfaches eigenes Modell von Räumen, Oberflächen und Objekten mit Kategorien, IDs, Dimensionen und Transformationen.
- **Output:** **GLB** als Kandidat für eine portable 3D-Datei; **BLEND** nur, falls es eine ausdrückliche Anforderung gibt.

Die alte Formulierung **„GLB ausschließlich“** trifft für eine Pipeline mit JSON- oder USDZ-Eingabe nicht zu. Ebenso sollte nicht angenommen werden, dass USDZ beliebig direkt in trimesh geladen oder als strukturiertes RoomPlan-JSON ersetzt werden kann.

[System-Flows](system-flow.md) · [Entscheidungsstand](decision.md)
