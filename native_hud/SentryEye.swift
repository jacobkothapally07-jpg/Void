import Foundation
import AVFoundation
import Vision
import AppKit

class SentryEye: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    let session = AVCaptureSession()
    let videoOutput = AVCaptureVideoDataOutput()
    var frameCount = 0
    let framesToWarmUp = 4
    var frameCaptured = false
    var completion: ((Int, String?) -> Void)?
    var outputPath: String = "/tmp/jarvis_sentry_capture.jpg"
    let queue = DispatchQueue(label: "camera_queue")
    
    func captureAndAnalyze(outputFile: String, completion: @escaping (Int, String?) -> Void) {
        self.outputPath = outputFile
        self.completion = completion
        
        session.beginConfiguration()
        session.sessionPreset = .medium
        
        let discovery = AVCaptureDevice.DiscoverySession(
            deviceTypes: [.builtInWideAngleCamera],
            mediaType: .video,
            position: .unspecified
        )
        let device = discovery.devices.first(where: { $0.localizedName.contains("FaceTime") })
            ?? discovery.devices.first
            ?? AVCaptureDevice.default(for: .video)
        
        guard let validDevice = device else {
            completion(0, nil)
            return
        }
        
        guard let input = try? AVCaptureDeviceInput(device: validDevice), session.canAddInput(input) else {
            completion(0, nil)
            return
        }
        session.addInput(input)
        
        videoOutput.alwaysDiscardsLateVideoFrames = true
        videoOutput.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32BGRA)]
        videoOutput.setSampleBufferDelegate(self, queue: queue)
        
        guard session.canAddOutput(videoOutput) else {
            completion(0, nil)
            return
        }
        session.addOutput(videoOutput)
        session.commitConfiguration()
        
        session.startRunning()
    }
    
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        frameCount += 1
        if frameCount < framesToWarmUp {
            return
        }
        guard !frameCaptured else { return }
        frameCaptured = true
        session.stopRunning()
        
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else {
            completion?(0, nil)
            return
        }
        
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else {
            completion?(0, nil)
            return
        }
        
        // Save JPEG
        let nsImage = NSImage(cgImage: cgImage, size: NSSize(width: cgImage.width, height: cgImage.height))
        if let tiffData = nsImage.tiffRepresentation,
           let rep = NSBitmapImageRep(data: tiffData),
           let jpgData = rep.representation(using: .jpeg, properties: [:]) {
            try? jpgData.write(to: URL(fileURLWithPath: outputPath))
        }
        
        // Detect faces using Apple Vision
        let request = VNDetectFaceRectanglesRequest { (req, err) in
            let count = req.results?.count ?? 0
            self.completion?(count, self.outputPath)
        }
        
        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        do {
            try handler.perform([request])
        } catch {
            completion?(0, outputPath)
        }
    }
}

let sentry = SentryEye()
var finished = false
var detectedFaces = 0
var savedPath: String? = nil

let targetPath = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "/tmp/jarvis_sentry_capture.jpg"

sentry.captureAndAnalyze(outputFile: targetPath) { faces, path in
    detectedFaces = faces
    savedPath = path
    finished = true
}

let startTime = Date()
while !finished && Date().timeIntervalSince(startTime) < 8.0 {
    RunLoop.current.run(until: Date().addingTimeInterval(0.05))
}

let jsonResult = [
    "status": finished ? "success" : "timeout",
    "faces_detected": "\(detectedFaces)",
    "snapshot_path": savedPath ?? ""
]

if let jsonData = try? JSONSerialization.data(withJSONObject: jsonResult, options: .prettyPrinted),
   let jsonString = String(data: jsonData, encoding: .utf8) {
    print(jsonString)
}
exit(finished ? 0 : 1)
