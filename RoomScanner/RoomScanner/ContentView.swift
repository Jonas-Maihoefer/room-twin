//
//  ContentView.swift
//  RoomScanner
//
//  Created by An Vinh Hoang on 11.11.26.
//

import SwiftUI
import RoomPlan
import ARKit
import QuickLook

struct ContentView: View {
    @State private var amscannen = false
    @StateObject private var manager = ScanManager()
    @State private var vorschau: URL?
    let supp = RoomCaptureSession.isSupported
    
    var body: some View {
        
        if let raum = manager.ergebnis {
            VStack {
                Text("Scan fertig")
                Text("Wände = \(raum.walls.count)")
                Text("Türen = \(raum.doors.count)")
                Text("Fenster = \(raum.windows.count)")
                Text("Objekte = \(raum.objects.count)")
                Button("3D-Modell ansehen") {
                    vorschau = manager.usdzURL
                }
                .disabled(manager.usdzURL == nil)
                Button("Neu Scannen") {
                    manager.ergebnis = nil
                    amscannen = false
                    manager.usdzURL = nil
                }
            }
            .padding()
            .quickLookPreview($vorschau)
        } else if amscannen {
            VStack {
                ScannerView(manager: manager)
                Button("Abbrechen", role: .destructive) {
                    amscannen = false
                }
                Button("Fertig") {
                    manager.stopScan()
                }
            }
            .padding()
        } else {
            VStack {
                Text("RoomScanner")
                    .font(.largeTitle)
                Button("Scan Starten") {
                    amscannen = true
                }
                .disabled(!supp)
                if !supp {
                    Text("iPhone-Modell nicht unterstützt")
                        .foregroundStyle(.secondary)
                }
            }
            .padding()
        }
    }
}

#Preview {
    ContentView()
}
