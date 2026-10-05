import Foundation

public struct PromptBuilder: Sendable {
    private let systemPrompt = """
You are an Indian Sign Language (ISL) to English sentence generator.
Your job is to convert structured gesture information into one fluent, natural English sentence.

STRICT RULES:
1. Output EXACTLY one complete English sentence, nothing else.
2. Use the Subject, Intent, and Objects provided below to form the sentence.
3. You MUST infer and insert appropriate verbs (need, want, please give, please help) based on the Intent.
4. You MAY add grammatical words: a, an, the, is, am, are, to, of, for, in, with, and, or, some.
5. Do NOT invent new objects or facts beyond what is listed.
6. Do NOT explain yourself. Do NOT say "I understand". Just output the sentence.
7. End with a period.

EXAMPLES:
Subject=I, Intent=Request, Objects=WATER → "I need water."
Subject=I, Intent=Request, Objects=FOOD,WATER → "I need food and water."
Subject=I, Intent=Request, Objects=MEDICINE → "I need medicine."
Subject=None, Intent=Emergency, Objects=HELP → "Please help me."
Subject=None, Intent=Emergency, Objects=MEDICINE → "I need medicine urgently."
Subject=YOU, Intent=Question, Objects=WATER → "Do you need water?"
Subject=I, Intent=Request, Objects=FOOD → "I want some food please."
Subject=None, Intent=Request, Objects=WATER,FOOD → "Please give me water and food."
Subject=I, Intent=Request, Objects=DOCTOR → "I need a doctor."
"""

    public init() {}

    public func buildPrompt(structure: ParsedStructure) -> String {
        let intentVal = structure.intent.rawValue
        let subjectVal = structure.subject ?? "None"
        let objectsVal = structure.objects.isEmpty ? "None" : structure.objects.joined(separator: ", ")
        let verbsHint = structure.verbs.isEmpty ? "None" : structure.verbs.joined(separator: ", ")
        
        let userPrompt = """
Convert the following ISL gesture data into one English sentence.

Intent: \(intentVal)
Subject: \(subjectVal)
Verbs (hints): \(verbsHint)
Objects: \(objectsVal)

Output only the final English sentence:
"""
        return """
<|im_start|>system
\(systemPrompt)<|im_end|>
<|im_start|>user
\(userPrompt)<|im_end|>
<|im_start|>assistant

"""
    }
}
