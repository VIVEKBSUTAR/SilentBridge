import Foundation

public struct ParsedStructure: Sendable {
    public var intent: GestureIntent
    public var greeting: String?
    public var closing: String?
    public var subject: String?
    public var objects: [String]
    public var verbs: [String]
    public var isEmergency: Bool
    
    public init(
        intent: GestureIntent,
        greeting: String? = nil,
        closing: String? = nil,
        subject: String? = nil,
        objects: [String] = [],
        verbs: [String] = [],
        isEmergency: Bool = false
    ) {
        self.intent = intent
        self.greeting = greeting
        self.closing = closing
        self.subject = subject
        self.objects = objects
        self.verbs = verbs
        self.isEmergency = isEmergency
    }
}

public struct IntentInterpreter: Sendable {
    private let greetingKeywords: Set<String> = ["HELLO", "HI", "GOOD_MORNING"]
    private let emergencyKeywords: Set<String> = ["HELP", "MEDICINE", "DANGER", "HURT", "ACCIDENT", "DOCTOR"]
    private let confirmationKeywords: Set<String> = ["YES", "OK", "CORRECT"]
    private let negationKeywords: Set<String> = ["NO", "NOT", "INCORRECT"]
    private let closingKeywords: Set<String> = ["THANK_YOU", "BYE", "GOODBYE", "THANKS"]
    private let subjectsList: Set<String> = ["I", "YOU", "WE", "HE", "SHE", "THEY"]
    private let verbsList: Set<String> = ["NEED", "WANT", "PLEASE", "GIVE", "GO", "COME", "GET", "LIKE"]
    
    public init() {}
    
    public func interpret(tokens: [String]) -> ParsedStructure {
        guard !tokens.isEmpty else {
            return ParsedStructure(intent: .unknown)
        }
        
        let tokensUpper = tokens.map { $0.trimmingCharacters(in: .whitespacesAndNewlines).uppercased() }
        
        var greeting: String? = nil
        var closing: String? = nil
        var subject: String? = nil
        var objects: [String] = []
        var verbs: [String] = []
        var isEmergency = false
        
        for token in tokensUpper {
            if greetingKeywords.contains(token) {
                greeting = token
            } else if closingKeywords.contains(token) {
                closing = token
            } else if subjectsList.contains(token) {
                subject = token
            } else if verbsList.contains(token) {
                verbs.append(token)
            } else if emergencyKeywords.contains(token) {
                isEmergency = true
                if token == "HELP" || token == "MEDICINE" {
                    objects.append(token)
                }
            } else {
                if token != "ALL" {
                    objects.append(token)
                }
            }
        }
        
        let intent: GestureIntent
        if isEmergency {
            intent = .emergency
        } else if greeting != nil && tokensUpper.count == 1 {
            intent = .greeting
        } else if closing != nil && tokensUpper.count == 1 {
            intent = .closing
        } else if tokensUpper.contains(where: { confirmationKeywords.contains($0) }) {
            intent = .confirmation
        } else if tokensUpper.contains(where: { negationKeywords.contains($0) }) {
            intent = .negation
        } else if tokensUpper.contains(where: { $0 == "WANT" || $0 == "NEED" || $0 == "PLEASE" || $0 == "I" }) {
            intent = .request
        } else if tokensUpper.contains(where: { $0 == "YOU" || $0 == "WHERE" || $0 == "WHAT" || $0 == "HOW" }) {
            intent = .question
        } else {
            intent = .request
        }
        
        return ParsedStructure(
            intent: intent,
            greeting: greeting,
            closing: closing,
            subject: subject,
            objects: objects,
            verbs: verbs,
            isEmergency: isEmergency
        )
    }
}
