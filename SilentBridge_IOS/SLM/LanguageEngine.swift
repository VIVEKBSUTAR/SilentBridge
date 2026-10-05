import Foundation

/// Core orchestrator for the sign language sentence reconstruction pipeline.
public final class LanguageEngine: Sendable {
    private let interpreter = IntentInterpreter()
    private let promptBuilder = PromptBuilder()
    private let validator = SemanticValidator()
    
    private let greetingMap: [String: String] = [
        "HELLO": "Hello.",
        "HI": "Hi.",
        "GOOD_MORNING": "Good morning."
    ]
    private let closingMap: [String: String] = [
        "THANK_YOU": "Thank you.",
        "THANKS": "Thanks.",
        "BYE": "Goodbye.",
        "GOODBYE": "Goodbye."
    ]
    private let confirmationMap: [String: String] = [
        "YES": "Yes.",
        "OK": "Okay.",
        "CORRECT": "Correct."
    ]
    private let negationMap: [String: String] = [
        "NO": "No.",
        "NOT": "Not.",
        "INCORRECT": "Incorrect."
    ]
    
    public init() {}
    
    public func reconstructSentence(tokens: [String]) async -> String {
        guard !tokens.isEmpty else { return "" }
        
        let upper = tokens.map { $0.trimmingCharacters(in: .whitespacesAndNewlines).uppercased() }
        
        // --- Fast-path for single deterministic tokens ---
        if upper.count == 1 {
            let token = upper.first!
            if let mapped = confirmationMap[token] ?? negationMap[token] ?? greetingMap[token] ?? closingMap[token] {
                return mapped
            }
        }
        
        // Separate greeting / closing from core tokens
        let greetingPrefix = upper.first(where: { greetingMap.keys.contains($0) }).flatMap { greetingMap[$0] }
        let closingSuffix = upper.first(where: { closingMap.keys.contains($0) }).flatMap { closingMap[$0] }
        
        let greetingTokens = Set(upper.filter { greetingMap.keys.contains($0) })
        let closingTokens = Set(upper.filter { closingMap.keys.contains($0) })
        let coreTokens = upper.filter { !greetingTokens.contains($0) && !closingTokens.contains($0) }
        
        if coreTokens.isEmpty {
            let sentence = [greetingPrefix, closingSuffix].compactMap { $0 }.joined(separator: " ")
            return sentence.isEmpty ? upper.joined(separator: " ") : sentence
        }
        
        // Parse core structure
        let structure = interpreter.interpret(tokens: coreTokens)
        
        // Rule-based sentence construction (offline-first fallback guaranteed)
        let coreSentence = NaturalSentenceBuilder.build(structure: structure)
        let isValid = validator.isValid(generated: coreSentence, structure: structure, originalTokens: coreTokens + ["hello", "thank", "you"])
        
        let sentence = isValid ? coreSentence : NaturalSentenceBuilder.build(structure: structure)
        return [greetingPrefix, sentence, closingSuffix].compactMap { $0 }.joined(separator: " ")
    }
}
