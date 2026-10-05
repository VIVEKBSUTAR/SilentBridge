import SwiftUI

public struct DiagnosticsView: View {
    @EnvironmentObject var env: AppEnvironment
    
    public init() {}
    
    public var body: some View {
        List {
            Section {
                HStack {
                    Text("Connection")
                    Spacer()
                    Text(env.connectionState.rawValue)
                        .foregroundColor(env.connectionState.isConnected ? SBTheme.Colors.success : SBTheme.Colors.danger)
                        .fontWeight(.bold)
                }
                
                HStack {
                    Text("Packet Stream Status")
                    Spacer()
                    Text(env.latestSensorFrame != nil ? "Receiving Data" : "No Packets")
                        .foregroundColor(env.latestSensorFrame != nil ? SBTheme.Colors.success : .secondary)
                }
                
                if let frame = env.latestSensorFrame {
                    HStack {
                        Text("Last Packet Timestamp")
                        Spacer()
                        Text("\(frame.timestamp) ms")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            } header: {
                Text("Bluetooth Telemetry")
            }
            
            if let frame = env.latestSensorFrame {
                Section {
                    sensorRow(name: "Thumb (ADC)", value: "\(frame.thumb)", max: 4095)
                    sensorRow(name: "Index (ADC)", value: "\(frame.index)", max: 4095)
                    sensorRow(name: "Middle (ADC)", value: "\(frame.middle)", max: 4095)
                    sensorRow(name: "Ring (ADC)", value: "\(frame.ring)", max: 4095)
                    sensorRow(name: "Little (ADC)", value: "\(frame.little)", max: 4095)
                } header: {
                    Text("Hall Finger Sensors (12-bit ADC)")
                }
                
                Section {
                    HStack {
                        Text("Acc X / Y / Z")
                        Spacer()
                        Text(String(format: "%.2f, %.2f, %.2f", frame.ax, frame.ay, frame.az))
                            .font(.subheadline.monospaced())
                    }
                    HStack {
                        Text("Gyro X / Y / Z")
                        Spacer()
                        Text(String(format: "%.2f, %.2f, %.2f", frame.gx, frame.gy, frame.gz))
                            .font(.subheadline.monospaced())
                    }
                    HStack {
                        Text("Pitch / Roll")
                        Spacer()
                        Text(String(format: "%.1f° / %.1f°", frame.pitch, frame.roll))
                            .font(.subheadline.monospaced())
                            .foregroundColor(SBTheme.Colors.primary)
                    }
                } header: {
                    Text("IMU 6-Axis Motion & Orientation")
                }
            }
            
            Section {
                HStack {
                    Text("Classifier Engine")
                    Spacer()
                    Text("BiLSTM Standard (100x13)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                HStack {
                    Text("Inference State")
                    Spacer()
                    Text(env.inferenceState.rawValue)
                        .font(.caption.weight(.bold))
                }
            } header: {
                Text("ML & Engine Pipeline")
            }
        }
        .navigationTitle("Diagnostics")
        .navigationBarTitleDisplayMode(.inline)
    }
    
    private func sensorRow(name: String, value: String, max: Int) -> some View {
        HStack {
            Text(name)
            Spacer()
            Text(value)
                .font(.subheadline.monospacedDigit().weight(.bold))
        }
    }
}
