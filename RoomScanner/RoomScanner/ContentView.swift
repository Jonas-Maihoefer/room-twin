//
//  ContentView.swift
//  RoomScanner
//
//  Created by An Vinh Hoang on 11.11.26.
//

import SwiftUI
import RoomPlan
import ARKit

struct ContentView: View {
    @State private var amscannen = false
    let supp = RoomCaptureSession.isSupported
    
    var body: some View {
        if !amscannen {
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
        } else {
            VStack {
                ScannerView()
                Button("Abbrechen") {
                    amscannen = false
                }
            }
            .padding()
        }
        
        
    }
}

#Preview {
    ContentView()
}
