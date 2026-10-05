import Foundation

/// Tutorial card data structure for learning sign language gestures.
public struct TutorialItem: Identifiable, Codable, Sendable, Equatable {
    public var id: Int
    public var word: String
    public var emoji: String
    public var youtubeId: String
    public var description: String
    public var handshape: String
    
    public init(id: Int, word: String, emoji: String, youtubeId: String, description: String, handshape: String) {
        self.id = id
        self.word = word
        self.emoji = emoji
        self.youtubeId = youtubeId
        self.description = description
        self.handshape = handshape
    }
    
    public var thumbnailUrl: URL? {
        URL(string: "https://img.youtube.com/vi/\(youtubeId)/hqdefault.jpg")
    }
    
    public var watchUrl: URL? {
        URL(string: "https://www.youtube.com/watch?v=\(youtubeId)")
    }
    
    public var embedUrl: URL? {
        URL(string: "https://www.youtube.com/embed/\(youtubeId)?autoplay=1&rel=0&modestbranding=1&playsinline=1")
    }
}
