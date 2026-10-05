import Foundation
import CoreBluetooth
import Combine

/*
 ==========================================================================================
 ESP32 FIRMWARE COMPATIBILITY SPECIFICATION (iOS BLE UART PROTOCOL)
 ==========================================================================================
 Android SilentBridge uses Bluetooth Classic SPP (RFCOMM UUID 00001101-0000-1000-8000-00805F9B34FB).
 Standard iOS hardware requires Bluetooth Low Energy (BLE) GATT notification stream.

 To connect the ESP32 glove to iOS:
 1. Enable BLE GATT Server on ESP32 (e.g. NimBLE-Arduino or BLEDevice).
 2. Service UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E (Nordic UART Service or Custom Service)
 3. RX Characteristic (Notify): 6E400003-B5A3-F393-E0A9-E50E24DCCA9E
 4. Packet Delimiter: "\n" (newline character)
 5. Packet Frequency: 50 Hz (20 ms interval)
 6. Packet Format (JSON String):
    {
      "timestamp": 1690000000000,
      "thumb": 2048, "index": 1800, "middle": 1950, "ring": 2100, "little": 1900,
      "ax": 0.1, "ay": 0.2, "az": 9.8,
      "gx": 1.2, "gy": 0.5, "gz": -0.8,
      "pitch": 12.4, "roll": -4.2
    }
 ==========================================================================================
 */

public final class BluetoothManager: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate, @unchecked Sendable {
    
    // MARK: - Published Properties
    @Published public private(set) var connectionState: ConnectionState = .disconnected
    @Published public private(set) var discoveredDevices: [BluetoothDevice] = []
    @Published public private(set) var connectedPeripheral: CBPeripheral? = nil
    @Published public private(set) var latestFrame: SensorFrame? = nil
    @Published public private(set) var packetRate: Double = 0.0
    
    // MARK: - Combine Publishers
    public let sensorFrameSubject = PassthroughSubject<SensorFrame, Never>()
    
    // MARK: - CoreBluetooth Properties
    private var centralManager: CBCentralManager!
    private var activePeripheral: CBPeripheral?
    private var rxCharacteristic: CBCharacteristic?
    
    private let parser = SensorPacketParser()
    private var lineBuffer = ""
    private var packetCounter = 0
    private var lastRateCalculation = Date()
    
    // Service & Characteristic UUIDs
    public static let uartServiceUUID = CBUUID(string: "6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    public static let rxCharacteristicUUID = CBUUID(string: "6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
    
    public override init() {
        super.init()
        self.centralManager = CBCentralManager(delegate: self, queue: .main)
    }
    
    // MARK: - Public Control API
    
    public func startScanning() {
        guard centralManager.state == .poweredOn else { return }
        discoveredDevices.removeAll()
        connectionState = .connecting
        centralManager.scanForPeripherals(withServices: nil, options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
    }
    
    public func stopScanning() {
        centralManager.stopScan()
    }
    
    public func connect(to address: String) {
        if let peripheral = activePeripheral, peripheral.identifier.uuidString == address {
            connectPeripheral(peripheral)
        } else {
            startScanning()
        }
    }
    
    public func connectPeripheral(_ peripheral: CBPeripheral) {
        stopScanning()
        self.activePeripheral = peripheral
        peripheral.delegate = self
        connectionState = .connecting
        centralManager.connect(peripheral, options: nil)
    }
    
    public func disconnect() {
        if let peripheral = activePeripheral {
            centralManager.cancelPeripheralConnection(peripheral)
        }
        connectionState = .disconnected
        activePeripheral = nil
        rxCharacteristic = nil
    }
    
    // MARK: - CBCentralManagerDelegate
    
    public func centralManagerDidUpdateState(_ central: CBCentralManager) {
        switch central.state {
        case .poweredOn:
            startScanning()
        case .poweredOff, .unauthorized, .unsupported:
            connectionState = .disconnected
        default:
            break
        }
    }
    
    public func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String : Any], rssi RSSI: NSNumber) {
        let name = advertisementData[CBAdvertisementDataLocalNameKey] as? String ?? peripheral.name ?? "SilentBridge Glove"
        let uuid = peripheral.identifier.uuidString
        
        let device = BluetoothDevice(name: name, address: uuid, rssi: RSSI.intValue, isConnected: peripheral.state == .connected)
        
        if !discoveredDevices.contains(where: { $0.address == uuid }) {
            discoveredDevices.append(device)
            // Save peripheral reference for connection
            if name.lowercased().contains("silentbridge") || name.lowercased().contains("esp32") || name.lowercased().contains("glove") {
                self.activePeripheral = peripheral
            }
        }
    }
    
    public func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        self.connectedPeripheral = peripheral
        self.connectionState = .connected
        peripheral.discoverServices([Self.uartServiceUUID])
    }
    
    public func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        self.connectionState = .error
        self.activePeripheral = nil
    }
    
    public func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        self.connectionState = .disconnected
        self.connectedPeripheral = nil
        self.activePeripheral = nil
        self.rxCharacteristic = nil
    }
    
    // MARK: - CBPeripheralDelegate
    
    public func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let services = peripheral.services else { return }
        for service in services {
            peripheral.discoverCharacteristics([Self.rxCharacteristicUUID], for: service)
        }
    }
    
    public func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard let characteristics = service.characteristics else { return }
        for char in characteristics {
            if char.uuid == Self.rxCharacteristicUUID {
                self.rxCharacteristic = char
                peripheral.setNotifyValue(true, for: char)
            }
        }
    }
    
    public func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard let data = characteristic.value, let dataString = String(data: data, encoding: .utf8) else { return }
        
        lineBuffer.append(dataString)
        
        // Process full line packets separated by '\n'
        while let newlineIndex = lineBuffer.firstIndex(of: "\n") {
            let line = String(lineBuffer[..<newlineIndex]).trimmingCharacters(in: .whitespacesAndNewlines)
            lineBuffer.removeSubrange(..<lineBuffer.index(after: newlineIndex))
            
            if !line.isEmpty {
                processLinePacket(line)
            }
        }
    }
    
    private func processLinePacket(_ line: String) {
        guard let frame = parser.parse(jsonString: line) else { return }
        
        self.latestFrame = frame
        self.sensorFrameSubject.send(frame)
        
        packetCounter += 1
        let now = Date()
        let elapsed = now.timeIntervalSince(lastRateCalculation)
        if elapsed >= 1.0 {
            self.packetRate = Double(packetCounter) / elapsed
            packetCounter = 0
            lastRateCalculation = now
        }
    }
}
