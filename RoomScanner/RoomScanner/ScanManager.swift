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


class ScanManager: NSObject, ObservableObject, RoomCaptureViewDelegate {
    
    @Published var usdzURL: URL?
    @Published var ergebnis: CapturedRoom?
    @Published var exportDateien: [URL] = []
    
    
    weak var rcv: RoomCaptureView?
    
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
    }
    
    func exportieren(){
        
        if let raum = ergebnis {
            let formatierer = DateFormatter()
            formatierer.dateFormat = "yyyy-MM-dd_HH-mm-ss"
            let zeit = formatierer.string(from: Date())
            let dokumente = URL.documentsDirectory
            let scanOrdner = dokumente.appending(path: "scan_\(zeit)")
            
            let usdzDatei = scanOrdner.appending(path: "room.usdz")
            let jsonDatei = scanOrdner.appending(path: "room.json")
            let metaDatei = scanOrdner.appending(path: "metadata.json")

            do {
                try FileManager.default.createDirectory(at: scanOrdner, withIntermediateDirectories: true)
                try raum.export(to: usdzDatei)
                
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                let raumDaten = try encoder.encode(raum)
                try raumDaten.write(to: jsonDatei)
                
                let meta = ScanMetadaten(
                    scanID: "scan_\(zeit)",
                    datum: zeit,
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
