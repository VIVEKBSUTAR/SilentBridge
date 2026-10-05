import Foundation

public struct SemanticValidator: Sendable {
    private let allowedHelperWords: Set<String> = [
        "a", "an", "the", "is", "am", "are", "to", "of", "for",
        "on", "in", "with", "and", "or", "need", "want", "please",
        "give", "me", "some", "do", "does", "did", "have", "has",
        "can", "could", "will", "would", "should", "may", "might",
        "i", "you", "we", "he", "she", "they", "it", "my", "your",
        "urgently", "now", "help", "get", "go", "come", "here",
        "where", "what", "how", "who", "there", "this", "that"
    ]
    
    public init() {}
    
    public func isValid(generated: String, structure: ParsedStructure, originalTokens: [String]) -> Bool {
        guard !generated.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return false }
        
        let lowerGen = generated.lowercased()
        
        // 1. Mandatory Object verification: If original tokens had object concepts,
        // they must be represented in the generated text.
        for obj in structure.objects {
            let lowerObj = obj.lowercased()
            if !lowerGen.contains(lowerObj) {
                return false
            }
        }
        
        // 2. Token overlap verification
        var tokenSet = Set<String>()
        for t in originalTokens {
            let lower = t.lowercased()
            if lower.contains("_") {
                lower.split(separator: "_").forEach { tokenSet.insert(String($0)) }
            } else {
                tokenSet.insert(lower)
            }
        }
        
        let matchCount = tokenSet.filter { lowerGen.contains($0) }.count
        if matchCount >= 1 { return true }
        
        // Secondary: check if all words are helper words
        let words = lowerGen.components(separatedBy: CharacterSet.alphanumerics.inverted).filter { !$0.isEmpty }
        let unknownCount = words.filter { !allowedHelperWords.contains($0) && $0.count > 1 }.count
        return unknownCount == 0
    }
}
