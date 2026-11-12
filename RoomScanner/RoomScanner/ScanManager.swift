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
    
    weak var arSession: ARSession?
    weak var rcv: RoomCaptureView?
    
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
        rcv?.captureSession.stop()
        stopSammeln()
    }
    
    func neuerScanOrdner() {
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
                speichereFrame()
                try? await Task.sleep(for: .seconds(0.5))
            }
        }
    }

    func stopSammeln() {
        sammelTask?.cancel()
        sammelTask = nil
    }
    
    func speichereFrame() {
        guard let ordner = scanOrdner,
              let frame = arSession?.currentFrame
        else { return }
        frameNummer += 1
    
        let name = String(format: "frame_%04d.jpg", frameNummer)

        let datei = ordner.appending(path: "frames").appending(path: name)

        let bild = CIImage(cvPixelBuffer: frame.capturedImage)
        let farbraum = CGColorSpace(name: CGColorSpace.sRGB)!

        do {
            if let jpg = kontext.jpegRepresentation(of: bild, colorSpace: farbraum, options: [:]) {
                try jpg.write(to: datei)
            }
        } catch {
            print("Fehler beim Speichern: \(error)")
        }
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
                dateien: ["room.usdz", "room.json", "metadata.json"]
            )
            let metaDaten = try encoder.encode(meta)
            try metaDaten.write(to: metaDatei)
            
            usdzURL = usdzDatei
            exportDateien = [usdzDatei, jsonDatei, metaDatei]
            
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
