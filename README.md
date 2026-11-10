# Room Twin

Room Twin untersucht, wie aus einem indoor-LiDAR-Raumscan ein weiterverarbeitbares 3D-Modell entsteht. Der gewählte MVP-Ablauf ist eine eigene iOS-App mit Apple RoomPlan, strukturierte Scandaten an ein Backend, Möbelersatz und GLB-Download/Teilen.

## Dokumentation

- [Systemarchitektur](docs/architecture/architecture.md)
- [Technologie- und Validierungsstand](docs/architecture/tech-stack.md)
- [How to dev: Setup und täglicher Ablauf](docs/how-to-dev.md)
- [Windows-Setup, EAS-Signierung und Geräteprüfung](docs/development/windows.md)
- [Dokumentationsübersicht](docs/README.md)

## Aktueller Stand

Das Repository enthält ein Expo-Grundgerüst mit einem isolierten RoomPlan-Adapter und Scanbildschirm sowie ein FastAPI-Backend mit Health-Check und vorläufigem Scan-API-Vertrag. Der native Scanexport muss noch in einem EAS-Entwicklungsbuild auf einem physischen LiDAR-Gerät geprüft werden. Möbelersatz und GLB-Erzeugung sind noch nicht implementiert.
