import SwiftUI

public struct ConnectionView: View {
    @EnvironmentObject var env: AppEnvironment
    
    public init() {}
    
    public var body: some View {
        List {
            Section {
                HStack(spacing: SBTheme.Spacing.medium) {
                    Image(systemName: env.connectionState.isConnected ? "antenna.radiowaves.left.and.right.circle.fill" : "antenna.radiowaves.left.and.right.slash")
                        .font(.system(size: 40))
                        .foregroundColor(env.connectionState.isConnected ? SBTheme.Colors.success : SBTheme.Colors.danger)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("SilentBridge ESP32 Glove")
                            .font(.headline)
                        Text(env.connectionState.rawValue)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.vertical, 8)
            } header: {
                Text("Connection Status")
            }
            
            Section {
                if env.discoveredDevices.isEmpty {
                    VStack(spacing: 8) {
                        ProgressView()
                        Text("Searching for SilentBridge BLE Gloves...")
                            .font(.footnote)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 16)
                } else {
                    ForEach(env.discoveredDevices) { device in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(device.name)
                                    .font(.headline)
                                Text(device.address)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            
                            Button(device.isConnected ? "Disconnect" : "Connect") {
                                if device.isConnected {
                                    env.disconnectDevice()
                                } else {
                                    env.connectDevice(address: device.address)
                                }
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(device.isConnected ? SBTheme.Colors.danger : SBTheme.Colors.primary)
                        }
                    }
                }
            } header: {
                Text("Available Devices")
            } footer: {
                Text("Ensure your ESP32 SilentBridge glove is powered on and advertising over Bluetooth Low Energy (BLE UART).")
            }
        }
        .navigationTitle("Glove Connection")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Scan") {
                    env.refreshDevices()
                }
            }
        }
    }
}
