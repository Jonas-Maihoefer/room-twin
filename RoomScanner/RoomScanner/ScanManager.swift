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
            let ordner = URL.documentsDirectory
            let datei = ordner.appending(path: "room.usdz")
            try? FileManager.default.removeItem(at: datei)
            do {
                try raum.export(to: datei)
                usdzURL = datei
                
            } catch {
                print("Fehler: \(error)")
            }
        }
    }
    
}
