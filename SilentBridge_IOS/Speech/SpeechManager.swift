import Foundation
import AVFoundation

/// Text-to-Speech manager using AVSpeechSynthesizer with automatic locale matching and voice selection.
public final class SpeechManager: NSObject, AVSpeechSynthesizerDelegate, @unchecked Sendable {
    private let synthesizer = AVSpeechSynthesizer()
    
    public override init() {
        super.init()
        synthesizer.delegate = self
    }
    
    public func speak(text: String, language: SupportedLanguage, rate: Float = 0.5, pitch: Float = 1.0) {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.rate = rate * AVSpeechUtteranceDefaultSpeechRate * 2.0
        utterance.pitchMultiplier = pitch
        
        // Select best available voice for language BCP-47 tag
        if let voice = selectBestVoice(bcp47Tag: language.bcp47Tag) {
            utterance.voice = voice
        } else {
            utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        }
        
        // Configure Audio Session for active playback
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
        try? AVAudioSession.sharedInstance().setActive(true)
        
        synthesizer.speak(utterance)
    }
    
    public func stop() {
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
    }
    
    private func selectBestVoice(bcp47Tag: String) -> AVSpeechSynthesisVoice? {
        let voices = AVSpeechSynthesisVoice.speechVoices().filter { $0.language == bcp47Tag }
        if let femaleVoice = voices.first(where: { $0.gender == .female }) {
            return femaleVoice
        }
        return voices.first ?? AVSpeechSynthesisVoice(language: bcp47Tag)
    }
}
