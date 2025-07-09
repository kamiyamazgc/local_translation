import Foundation

// 進捗状態を表す構造体
struct RSSProgressState: Codable {
    let status: String // idle, fetching, translating, completed, error
    let message: String
    let progress: Int // 0-100
    let total_articles: Int
    let processed_articles: Int
    let start_time: Double?
    let end_time: Double?
}

class APIService {
    static let shared = APIService()
    let baseURL = "http://127.0.0.1:8000"
    
    // 翻訳キャッシュ（永続化）
    private static var translationCache: [String: String] = [:]
    
    init() {
        // 永続キャッシュを読み込み
        loadPersistentCache()
    }
    
    // 永続キャッシュを読み込み
    private func loadPersistentCache() {
        if let data = UserDefaults.standard.data(forKey: "translationCache"),
           let cache = try? JSONDecoder().decode([String: String].self, from: data) {
            APIService.translationCache = cache
            print("Loaded \(cache.count) cached translations")
        }
    }
    
    // 永続キャッシュを保存
    private func savePersistentCache() {
        if let data = try? JSONEncoder().encode(APIService.translationCache) {
            UserDefaults.standard.set(data, forKey: "translationCache")
            print("Saved \(APIService.translationCache.count) cached translations")
        }
    }
    
    // キャッシュをクリアするメソッド
    static func clearTranslationCache() {
        translationCache.removeAll()
        UserDefaults.standard.removeObject(forKey: "translationCache")
    }
    
    // キャッシュされた翻訳を取得
    func getCachedTranslation(for url: String) -> String? {
        return APIService.translationCache[url]
    }

    func fetchRSS(completion: @escaping (Result<RSSResponse, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/rss") else { return }
        var request = URLRequest(url: url)
        // 通常のRSS取得は短めのタイムアウト
        request.timeoutInterval = 60 // 1分
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("API error:", error)
                completion(.failure(error))
                return
            }
            guard let data = data else {
                print("No data received")
                completion(.failure(NSError(domain: "NoData", code: 0)))
                return
            }
            print("API raw data:", String(data: data, encoding: .utf8) ?? "nil")
            do {
                let response = try JSONDecoder().decode(RSSResponse.self, from: data)
                completion(.success(response))
            } catch {
                print("Decoding error:", error)
                completion(.failure(error))
            }
        }.resume()
    }

    func reloadRSS(completion: @escaping (Result<RSSResponse, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/rss/reload") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        // RSSリロードは翻訳も含むため、タイムアウトを長めに設定
        request.timeoutInterval = 300 // 5分
        URLSession.shared.dataTask(with: request) { data, _, error in
            if let error = error {
                print("RSS reload error:", error)
                completion(.failure(error))
                return
            }
            guard let data = data else { 
                print("No data received from RSS reload")
                completion(.failure(NSError(domain: "NoData", code: 0)))
                return
            }
            do {
                let response = try JSONDecoder().decode(RSSResponse.self, from: data)
                completion(.success(response))
            } catch {
                print("RSS reload decoding error:", error)
                completion(.failure(error))
            }
        }.resume()
    }
    
    func getRSSProgress(completion: @escaping (Result<RSSProgressState, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/rss/status") else { return }
        var request = URLRequest(url: url)
        request.timeoutInterval = 10 // 進捗確認は短いタイムアウト
        URLSession.shared.dataTask(with: request) { data, _, error in
            if let error = error {
                print("Progress check error:", error)
                completion(.failure(error))
                return
            }
            guard let data = data else { 
                print("No data received from progress check")
                completion(.failure(NSError(domain: "NoData", code: 0)))
                return
            }
            do {
                let progress = try JSONDecoder().decode(RSSProgressState.self, from: data)
                completion(.success(progress))
            } catch {
                print("Progress decoding error:", error)
                completion(.failure(error))
            }
        }.resume()
    }

    func translateArticle(url: String, text: String, articlesBySource: [String: [Article]], completion: @escaping (Result<String, Error>) -> Void) {
        // キャッシュをチェック
        if let cachedTranslation = APIService.translationCache[url] {
            print("Cache hit for URL: \(url)")
            completion(.success(cachedTranslation))
            return
        }
        
        print("Cache miss for URL: \(url), making API request...")
        
        guard let endpoint = URL(string: "\(baseURL)/translate/article") else { return }
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 300
        let body: [String: Any] = [
            "url": url,
            "text": text
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        URLSession.shared.dataTask(with: request) { data, _, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            guard let data = data else { return }
            do {
                // 新しいレスポンス形式に対応
                struct TranslationResponse: Codable {
                    let original_text: String
                    let translated_text: String
                    let source: String
                    let title: String
                    let published: String?
                }
                
                let result = try JSONDecoder().decode(TranslationResponse.self, from: data)
                // キャッシュに保存
                APIService.translationCache[url] = result.translated_text
                // 永続キャッシュを保存
                self.savePersistentCache()
                print("Cached translation for URL: \(url)")
                completion(.success(result.translated_text))
            } catch {
                print("Translation response decoding error:", error)
                completion(.failure(error))
            }
        }.resume()
    }
} 