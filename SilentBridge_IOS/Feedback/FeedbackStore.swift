import Foundation

/// Stores per-gesture feedback history using UserDefaults and computes running penalty multipliers.
public final class FeedbackStore: @unchecked Sendable {
    public static let windowSize: Int = 20
    private static let keyPrefix = "sb_history_"
    
    public init() {}
    
    /// Records a feedback event. isCorrect = true for Yes, false for No.
    public func recordFeedback(gestureName: String, isCorrect: Bool) {
        var history = getHistory(gestureName: gestureName)
        if history.count >= Self.windowSize {
            history.removeFirst()
        }
        history.append(isCorrect ? 1 : 0)
        saveHistory(gestureName: gestureName, history: history)
    }
    
    /// Returns penalty factor [0.0, 1.0] for a gesture based on recent wrong predictions.
    public func getPenaltyFactor(gestureName: String) -> Float {
        let history = getHistory(gestureName: gestureName)
        guard !history.isEmpty else { return 0.0 }
        let wrongCount = history.filter { $0 == 0 }.count
        return Float(wrongCount) / Float(Self.windowSize)
    }
    
    /// Returns confidence adjusted by gesture penalty factor.
    public func applyPenalty(gestureName: String, rawConfidence: Float) -> Float {
        let penalty = getPenaltyFactor(gestureName: gestureName)
        return max(0.0, rawConfidence * (1.0 - penalty))
    }
    
    /// Returns per-gesture stats: [gestureName: (correct, wrong)]
    public func getStats() -> [String: (correct: Int, wrong: Int)] {
        let defaults = UserDefaults.standard.dictionaryRepresentation()
        var stats: [String: (correct: Int, wrong: Int)] = [:]
        
        for key in defaults.keys where key.hasPrefix(Self.keyPrefix) {
            let gestureName = String(key.dropFirst(Self.keyPrefix.count))
            let history = getHistory(gestureName: gestureName)
            let correct = history.filter { $0 == 1 }.count
            let wrong = history.filter { $0 == 0 }.count
            stats[gestureName] = (correct: correct, wrong: wrong)
        }
        return stats
    }
    
    private func getHistory(gestureName: String) -> [Int] {
        let key = Self.keyPrefix + gestureName
        return UserDefaults.standard.array(forKey: key) as? [Int] ?? []
    }
    
    private func saveHistory(gestureName: String, history: [Int]) {
        let key = Self.keyPrefix + gestureName
        UserDefaults.standard.set(history, forKey: key)
    }
    
    public func clearHistory() {
        let defaults = UserDefaults.standard.dictionaryRepresentation()
        for key in defaults.keys where key.hasPrefix(Self.keyPrefix) {
            UserDefaults.standard.removeObject(forKey: key)
        }
    }
}
