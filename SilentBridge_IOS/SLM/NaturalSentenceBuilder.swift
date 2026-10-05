import Foundation

public enum NaturalSentenceBuilder {
    public static func build(structure: ParsedStructure) -> String {
        let subject = structure.subject
        let objects = structure.objects.map { $0.lowercased() }
        let intent = structure.intent
        
        let subj: String
        if subject == nil || subject?.lowercased() == "none" {
            subj = "I"
        } else if subject?.lowercased() == "i" {
            subj = "I"
        } else {
            subj = subject?.capitalized ?? "I"
        }
        
        let objectPhrase: String
        switch objects.count {
        case 0: objectPhrase = ""
        case 1: objectPhrase = objects[0]
        case 2: objectPhrase = "\(objects[0]) and \(objects[1])"
        default:
            objectPhrase = objects.dropLast(1).joined(separator: ", ") + " and \(objects.last!)"
        }
        
        switch intent {
        case .emergency:
            if objectPhrase.isEmpty || objectPhrase.contains("help") {
                return "Please help me!"
            } else {
                return "I urgently need \(objectPhrase)!"
            }
        case .question:
            if objectPhrase.isEmpty {
                return "What do you need?"
            } else {
                return "Do you need \(objectPhrase)?"
            }
        case .confirmation:
            return "Yes."
        case .negation:
            return "No."
        case .greeting:
            return "Hello."
        case .closing:
            return "Thank you."
        default: // .request / .unknown
            if objectPhrase.isEmpty {
                return "\(subj) need help."
            } else {
                return "\(subj) need \(objectPhrase)."
            }
        }
    }
}
