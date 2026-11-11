//
//  ScannerView.swift
//  RoomScanner
//
//  Created by An Vinh Hoang on 11.11.26.
//

import SwiftUI
import RoomPlan
import ARKit

struct ScannerView: UIViewRepresentable {
    
    func makeUIView(context: Context) -> RoomCaptureView {
        let ars = ARSession()
        let ansicht = RoomCaptureView(frame: .zero, arSession: ars)
        
        let konfig = RoomCaptureSession.Configuration()
        ansicht.captureSession.run(configuration: konfig)
        
        return ansicht
        
    }
    
    
    func updateUIView(_ uiView: RoomCaptureView, context: Context) {
        
    }
    
    static func dismantleUIView(_ uiView: RoomCaptureView, coordinator: Coordinator) {
        uiView.captureSession.stop()
    }
}

