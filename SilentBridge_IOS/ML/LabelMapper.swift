import Foundation

/// Maps numeric output classifier indices [0..12] to gesture word strings from label_map.json.
public final class LabelMapper: @unchecked Sendable {
    private var labels: [Int: String] = [:]
    
    public init() {
        loadLabels()
    }
    
    public func loadLabels() {
        guard let url = Bundle.main.url(forResource: "label_map", withExtension: "json") else {
            fallbackLabels()
            return
        }
        do {
            let data = try Data(contentsOf: url)
            let jsonMap = try JSONDecoder().decode([String: Int].self, from: data)
            var reverse: [Int: String] = [:]
            for (key, val) in jsonMap {
                reverse[val] = key
            }
            self.labels = reverse
        } catch {
            fallbackLabels()
        }
    }
    
    private func fallbackLabels() {
        self.labels = [
            0: "ALL", 1: "FOOD", 2: "HELLO", 3: "HELP", 4: "I",
            5: "MEDICINE", 6: "NEED", 7: "NO", 8: "THANK_YOU",
            9: "WANT", 10: "WATER", 11: "YES", 12: "YOU"
        ]
    }
    
    public func getLabel(for index: Int) -> String {
        labels[index] ?? "UNKNOWN"
    }
    
    public var allLabels: [String] {
        labels.sorted(by: { $0.key < $1.key }).map { $0.value }
    }
}
