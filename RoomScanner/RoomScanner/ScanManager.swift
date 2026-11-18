//
//  ScanManager.swift
//  RoomScanner
//
//  Created by An Vinh Hoang on 11.11.26.
//

import SwiftUI
import RoomPlan
import ARKit
import Combine
import CoreImage

class ScanManager: NSObject, ObservableObject, RoomCaptureViewDelegate {
    
    @Published var usdzURL: URL?
    @Published var ergebnis: CapturedRoom?
    @Published var exportDateien: [URL] = []
    var meshAnker: [ARMeshAnchor] = []
    
    weak var arSession: ARSession?
    weak var rcv: RoomCaptureView?
    
    var frameInfos: [FrameInfo] = []
    var scanOrdner: URL?
    var scanZeit = ""
    var frameNummer = 0
    let kontext = CIContext()
    var sammelTask: Task<Void, Never>?
    
    override init(){
        super.init()
    }
    
    required init?(coder: NSCoder) {
        fatalError("wird nicht benutzt")
    }
    
    func captureView(shouldPresent roomDataForProcessing: CapturedRoomData, error: Error?) -> Bool {
        return true
    }
    
    func captureView(didPresent processedResult: CapturedRoom, error: Error?) {
        ergebnis = processedResult
        exportieren()
    }
    
    func encode(with coder: NSCoder) {
    }
    
    func stopScan() {
        // Mesh einsammeln, BEVOR die Session stoppt (danach rechnet ARKit nicht mehr weiter)
        meshAnker = arSession?.currentFrame?.anchors.compactMap { $0 as? ARMeshAnchor } ?? []
        rcv?.captureSession.stop()
        stopSammeln()
    }
    
    func neuerScanOrdner() {
        meshAnker = []
        frameInfos = []
        let formatierer = DateFormatter()
        formatierer.dateFormat = "yyyy-MM-dd_HH-mm-ss"
        let zeit = formatierer.string(from: Date())
        let dokumente = URL.documentsDirectory
        let ordner = dokumente.appending(path: "scan_\(zeit)")
        let frames = ordner.appending(path: "frames")
        
        
        do {
            try FileManager.default.createDirectory(at: frames, withIntermediateDirectories: true)
            scanOrdner = ordner
            scanZeit = zeit
            frameNummer = 0
        } catch {
            print("Fehler beim Anlegen: \(error)")
        }
        
    }
    
    func startSammeln() {
        neuerScanOrdner()
        sammelTask = Task {
            while !Task.isCancelled {
                meshEinschalten()
                speichereFrame()
                try? await Task.sleep(for: .seconds(0.5))
            }
        }
    }

    func stopSammeln() {
        sammelTask?.cancel()
        sammelTask = nil
    }
    
    func verwerfeScan() {
        stopSammeln()                                       // Bilder-Sammeln stoppen
        if let ordner = scanOrdner {                        // gibt es einen Ordner von diesem Scan?
            try? FileManager.default.removeItem(at: ordner) // dann komplett löschen, samt aller Frames
        }
        scanOrdner = nil                                    // vergessen, dass es ihn gab
        frameNummer = 0
        frameInfos = []
        meshAnker = []
    }
    
    func speichereFrame() {
        guard let ordner = scanOrdner,
              let frame = arSession?.currentFrame,
              let tiefe = frame.sceneDepth
        else { return }
        frameNummer += 1
    
        let bildname = String(format: "frame_%04d.jpg", frameNummer)
        let tiefenname = String(format: "frame_%04d_depth.bin", frameNummer)
        let konfname = String(format: "frame_%04d_conf.bin", frameNummer)

        let framesOrdner = ordner.appending(path: "frames")
        
        let bildDatei = framesOrdner.appending(path: bildname)
        let tiefenDatei = framesOrdner.appending(path: tiefenname)
        let konfDatei = framesOrdner.appending(path: konfname)


        let bild = CIImage(cvPixelBuffer: frame.capturedImage)
        let farbraum = CGColorSpace(name: CGColorSpace.sRGB)!

        do {
            if let jpg = kontext.jpegRepresentation(of: bild, colorSpace: farbraum, options: [:]) {
                try jpg.write(to: bildDatei)
            }
            
            try rohdaten(von: tiefe.depthMap, bytesProPixel: 4).write(to: tiefenDatei)
            
            if let konf = tiefe.confidenceMap {
                let konfDaten = rohdaten(von: konf, bytesProPixel: 1)
                try konfDaten.write(to: konfDatei)
            }
            let info = FrameInfo(
                nummer: frameNummer,
                zeitstempel: frame.timestamp,
                bild: "frames/\(bildname)",
                tiefe: "frames/\(tiefenname)",
                konfidenz: tiefe.confidenceMap != nil ? "frames/\(konfname)" : nil,
                bildGroesse: [CVPixelBufferGetWidth(frame.capturedImage),
                              CVPixelBufferGetHeight(frame.capturedImage)],
                tiefenGroesse: [CVPixelBufferGetWidth(tiefe.depthMap),
                                CVPixelBufferGetHeight(tiefe.depthMap)],
                intrinsics: liste(frame.camera.intrinsics),
                kameraZuWelt: liste(frame.camera.transform)
            )
            frameInfos.append(info)
            
            
        } catch {
            print("Fehler beim Speichern: \(error)")
        }
    }
    
    func meshEinschalten() {
        
        guard let sesh = arSession,
        let konfig = sesh.configuration as? ARWorldTrackingConfiguration
        else {
            return
        }
        if konfig.sceneReconstruction == .meshWithClassification {
            return
        }
        let support = ARWorldTrackingConfiguration.supportsSceneReconstruction(.meshWithClassification)
            if !support {
                print("kein Support")
                return
            }
        konfig.sceneReconstruction = .meshWithClassification
        sesh.run(konfig)
        print("Mesh an")
        
            
    }
    // Name der ARKit-Klasse als Text, für die Gruppen in der OBJ-Datei
    func klassenName(_ k: ARMeshClassification) -> String {
        switch k {
        case .wall:    return "wall"
        case .floor:   return "floor"
        case .ceiling: return "ceiling"
        case .table:   return "table"
        case .seat:    return "seat"
        case .window:  return "window"
        case .door:    return "door"
        default:       return "none"
        }
    }

    // Schreibt alle Mesh-Stücke als eine OBJ-Datei (Weltkoordinaten, Gruppen = Klassen)
    func schreibeMesh(nach datei: URL) throws {
        var text = "# RoomScanner-Mesh (ARKit), Meter, ARKit-Welt (y nach oben), Gruppen = Klassen\n"
        var versatz = 0             // so viele Eckpunkte stehen schon in der Datei
        var letzteKlasse = ""

        for anker in meshAnker {
            let geo = anker.geometry

            // Eckpunkte: vom Mesh-Stück in Weltkoordinaten umrechnen
            for i in 0..<geo.vertices.count {
                let p = geo.eckpunkt(i)
                let w = anker.transform * SIMD4<Float>(p.x, p.y, p.z, 1)
                text += "v \(w.x) \(w.y) \(w.z)\n"
            }

            // Dreiecke: Nummern ab 1 und über die ganze Datei weitergezählt
            for i in 0..<geo.faces.count {
                let name = klassenName(geo.klasse(i))
                if name != letzteKlasse {           // neue Gruppe nur, wenn die Klasse wechselt
                    text += "g \(name)\n"
                    letzteKlasse = name
                }
                let d = geo.dreieck(i)
                text += "f \(d[0] + versatz + 1) \(d[1] + versatz + 1) \(d[2] + versatz + 1)\n"
            }

            versatz += geo.vertices.count
        }

        try text.write(to: datei, atomically: true, encoding: .utf8)
    }
    
    
    
    
    // Macht aus einem Tiefen- oder Konfidenzbild (CVPixelBuffer) rohe Bytes zum Speichern.
    func rohdaten(von map: CVPixelBuffer, bytesProPixel: Int) -> Data {
        CVPixelBufferLockBaseAddress(map, .readOnly)               // Speicher sperren, damit ARKit nicht gleichzeitig reinschreibt
        defer { CVPixelBufferUnlockBaseAddress(map, .readOnly) }   // am Ende der Funktion automatisch wieder freigeben

        let breite = CVPixelBufferGetWidth(map)                    // z. B. 256
        let hoehe = CVPixelBufferGetHeight(map)                    // z. B. 192
        let zeilenBytes = CVPixelBufferGetBytesPerRow(map)         // wie viele Bytes eine Zeile im Speicher belegt.
                                                                   // ACHTUNG: kann mehr sein als breite × bytesProPixel,
                                                                   // weil am Zeilenende manchmal "Polster-Bytes" sind
        let basis = CVPixelBufferGetBaseAddress(map)!.assumingMemoryBound(to: UInt8.self)
                                                                   // Zeiger auf den Anfang des Speichers, als einzelne Bytes

        var daten = Data(capacity: breite * hoehe * bytesProPixel) // leerer Datenblock, gleich passend groß reserviert
        for v in 0..<hoehe {                                       // Zeile für Zeile
            let zeile = basis + v * zeilenBytes                    // Anfang von Zeile v im Speicher
            daten.append(zeile, count: breite * bytesProPixel)     // nur die echten Pixel übernehmen, ohne Polster
        }
        return daten
    }

    // Wandelt Matrizen in einfache Zahlenlisten um, damit sie ins JSON passen.
    // Swift speichert Matrizen SPALTENWEISE, also auch die Liste spaltenweise.
    func liste(_ m: simd_float4x4) -> [Float] {
        [m.columns.0, m.columns.1, m.columns.2, m.columns.3]      // die 4 Spalten
            .flatMap { [$0.x, $0.y, $0.z, $0.w] }                 // jede Spalte in 4 Zahlen zerlegen und alles aneinanderhängen
    }
    func liste(_ m: simd_float3x3) -> [Float] {
        [m.columns.0, m.columns.1, m.columns.2]
            .flatMap { [$0.x, $0.y, $0.z] }
    }
    // Packt einen Ordner in eine ZIP-Datei, die daneben liegt.
    // z. B. .../scan_2026-11-12_13-30-00/  →  .../scan_2026-11-12_13-30-00.zip
    func zippen(_ ordner: URL) throws -> URL {
        let zielZip = ordner.deletingLastPathComponent()                        // eine Ebene hoch (Dokumente-Ordner)
                            .appending(path: "\(ordner.lastPathComponent).zip") // + "scan_….zip"
        try? FileManager.default.removeItem(at: zielZip)                        // falls es das ZIP schon gibt: weg damit

        var koordFehler: NSError?                                               // hier landet ein Fehler vom Koordinator
        var kopierFehler: Error?                                                // hier landet ein Fehler beim Kopieren

        NSFileCoordinator().coordinate(readingItemAt: ordner,
                                       options: .forUploading,                  // der Trick: "zum Hochladen vorbereiten"
                                       error: &koordFehler) { tempZip in        //   = iOS macht automatisch ein ZIP daraus
            // tempZip existiert NUR innerhalb dieser Klammern, danach löscht iOS es → sofort wegkopieren
            do {
                try FileManager.default.copyItem(at: tempZip, to: zielZip)
            } catch {
                kopierFehler = error
            }
        }

        if let f = koordFehler { throw f }                                      // Fehler? → an den Aufrufer weitergeben
        if let f = kopierFehler { throw f }
        return zielZip                                                          // Pfad zum fertigen ZIP
    }
    
    func exportieren(){
        
        guard let raum = ergebnis, let scanOrdner = scanOrdner else { return }
        
        let usdzDatei = scanOrdner.appending(path: "room.usdz")
        let jsonDatei = scanOrdner.appending(path: "room.json")
        let metaDatei = scanOrdner.appending(path: "metadata.json")
        
        do {
            try raum.export(to: usdzDatei)
            
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            let raumDaten = try encoder.encode(raum)
            try raumDaten.write(to: jsonDatei)
            
            let meta = ScanMetadaten(
                scanID: "scan_\(scanZeit)",
                datum: scanZeit,
                geraet: UIDevice.current.model,
                iosVersion: UIDevice.current.systemVersion,
                einheit: "Meter",
                koordinatensystem: "ARKit, y-Achse nach oben",
                dateien: ["room.usdz", "room.json", "metadata.json","frames.json","frames/", "README.md", "mesh.obj"]
            )
            let metaDaten = try encoder.encode(meta)
            try metaDaten.write(to: metaDatei)
            
            let framesDatei = scanOrdner.appending(path: "frames.json")
            let alleFrames = FramesDatei(
                hinweise: [
                    "Matrizen spaltenweise (column-major)",
                    "kameraZuWelt: ARKit-Kamera → Welt; Kamera schaut in −z, y nach oben, x nach rechts",
                    "Bilder und Tiefe in Sensor-Ausrichtung (Querformat), nicht gedreht",
                    "intrinsics gelten für bildGroesse; für das Tiefenbild mit tiefenBreite/bildBreite skalieren",
                    "Tiefe: float32 little-endian, Meter, Zeile für Zeile (tiefenGroesse)",
                    "Konfidenz: uint8, 0 = niedrig, 1 = mittel, 2 = hoch"
                ],
                frames: frameInfos
            )
            
            let framemeta = try encoder.encode(alleFrames)
            try framemeta.write(to: framesDatei)
            try schreibeMesh(nach: scanOrdner.appending(path: "mesh.obj"))
            
            
            if let readme = Bundle.main.url(forResource: "README", withExtension: "md") {
                let readmeZiel = scanOrdner.appending(path: "README.md")
                try FileManager.default.copyItem(at: readme, to: readmeZiel)
            } else {
                print("README nicht in der App gefunden")
            }
            
            usdzURL = usdzDatei

            let zip = try zippen(scanOrdner)
            exportDateien = [zip]
            
            
        } catch {
            print("Fehler: \(error)")
        }
    }
    
}

struct ScanMetadaten: Codable {
    let scanID: String
    let datum: String
    let geraet: String
    let iosVersion: String
    let einheit: String
    let koordinatensystem: String
    let dateien: [String]
}


struct FrameInfo: Codable {
    let nummer: Int              // 1, 2, 3 …
    let zeitstempel: Double      // Zeit des Frames in Sekunden (von ARKit)
    let bild: String             // z. B. "frames/frame_0001.jpg"
    let tiefe: String            // z. B. "frames/frame_0001_depth.bin"
    let konfidenz: String?       // z. B. "frames/frame_0001_conf.bin" (Optional, falls es mal keine gibt)
    let bildGroesse: [Int]       // [Breite, Höhe] des Kamerabilds, z. B. [1920, 1440]
    let tiefenGroesse: [Int]     // [Breite, Höhe] des Tiefenbilds, z. B. [256, 192]
    let intrinsics: [Float]      // Kamera-Parameter, 3×3 = 9 Zahlen
    let kameraZuWelt: [Float]    // Position + Drehung des iPhones, 4×4 = 16 Zahlen
}

// Die ganze Datei frames.json: Hinweise fürs Backend + Liste aller Frames
struct FramesDatei: Codable {
    let hinweise: [String]
    let frames: [FrameInfo]
}


// Hilfsfunktionen, um die Rohdaten eines Mesh-Stücks auszulesen
extension ARMeshGeometry {
    // Eckpunkt Nummer i, in Koordinaten des Mesh-Stücks
    func eckpunkt(_ i: Int) -> SIMD3<Float> {
        let zeiger = vertices.buffer.contents().advanced(by: vertices.offset + vertices.stride * i)
        let p = zeiger.assumingMemoryBound(to: (Float, Float, Float).self).pointee
        return SIMD3<Float>(p.0, p.1, p.2)
    }

    // Dreieck Nummer i: die drei Eckpunkt-Nummern (ab 0, innerhalb dieses Stücks)
    func dreieck(_ i: Int) -> [Int] {
        let anfang = faces.buffer.contents().advanced(by: faces.indexCountPerPrimitive * faces.bytesPerIndex * i)
        return (0..<faces.indexCountPerPrimitive).map { n in
            Int(anfang.advanced(by: n * faces.bytesPerIndex).assumingMemoryBound(to: UInt32.self).pointee)
        }
    }

    // Klasse von Dreieck Nummer i (Wand, Boden, Tisch …)
    func klasse(_ i: Int) -> ARMeshClassification {
        guard let c = classification else { return .none }
        let zeiger = c.buffer.contents().advanced(by: c.offset + c.stride * i)
        let wert = Int(zeiger.assumingMemoryBound(to: UInt8.self).pointee)
        return ARMeshClassification(rawValue: wert) ?? .none
    }
}
