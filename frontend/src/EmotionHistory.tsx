import React, { useState, useEffect } from "react";

interface EmotionRecord {
  id: string;
  timestamp: string;
  mood: number;
  energy: number;
  anxiety: number;
  primary_emotion: string;
  triggers: string[];
  notes: string;
}

interface Episode {
  id: string;
  title: string;
  content: string;
  emotion: string;
  emotion_intensity: number;
  timestamp: string;
  context: {
    location?: string;
    people?: string;
    time_period?: string;
  };
  importance_score: number;
}

interface EmotionHistoryProps {
  userId: string;
  apiUrl: string;
}

export const EmotionHistory: React.FC<EmotionHistoryProps> = ({
  userId,
  apiUrl,
}) => {
  const [emotionHistory, setEmotionHistory] = useState<EmotionRecord[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [trends, setTrends] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      // 感情履歴取得
      const emotionResponse = await fetch(
        `${apiUrl}/api/emotions/${userId}?days=7`,
      );
      if (emotionResponse.ok) {
        const emotionData = await emotionResponse.json();
        setEmotionHistory(emotionData.history || []);
      }

      // エピソード取得
      const episodesResponse = await fetch(
        `${apiUrl}/api/episodes/${userId}?limit=10`,
      );
      if (episodesResponse.ok) {
        const episodesData = await episodesResponse.json();
        setEpisodes(episodesData.episodes || []);
      }

      // トレンド取得
      const trendsResponse = await fetch(
        `${apiUrl}/api/emotions/${userId}/trends?days=7`,
      );
      if (trendsResponse.ok) {
        const trendsData = await trendsResponse.json();
        setTrends(trendsData.trends);
      }
    } catch (err) {
      console.error("Error loading emotion data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId && isExpanded) {
      loadData();
    }
  }, [userId, isExpanded]);

  const getEmotionColor = (emotion: string) => {
    const emotionColors: Record<string, string> = {
      happy: "#10b981",
      sad: "#3b82f6",
      anxious: "#f59e0b",
      angry: "#ef4444",
      frustrated: "#f97316",
      hopeful: "#14b8a6",
      neutral: "#6b7280",
    };
    return emotionColors[emotion] || "#6b7280";
  };

  const getScoreColor = (score: number, reverse: boolean = false) => {
    if (reverse) {
      // 不安の場合：低い方が良い
      return score >= 7 ? "#ef4444" : score >= 4 ? "#f59e0b" : "#10b981";
    }
    // 気分・エネルギーの場合：高い方が良い
    return score >= 7 ? "#10b981" : score >= 4 ? "#f59e0b" : "#ef4444";
  };

  return (
    <div
      style={{
        background: "white",
        borderRadius: "16px",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
        border: "2px solid #3b82f6",
        padding: "24px",
        marginTop: "24px",
      }}
    >
      {/* ヘッダー */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <h2
          style={{
            fontWeight: "bold",
            fontSize: "18px",
            color: "#1e40af",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          📈 感情履歴・エピソード記憶
        </h2>
        <div style={{ display: "flex", gap: "8px" }}>
          {isExpanded && (
            <button
              onClick={loadData}
              disabled={loading}
              style={{
                padding: "6px 12px",
                backgroundColor: "#3b82f6",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "12px",
                opacity: loading ? 0.5 : 1,
              }}
            >
              {loading ? "更新中..." : "🔄 更新"}
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              padding: "6px 12px",
              backgroundColor: "#6b7280",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "12px",
            }}
          >
            {isExpanded ? "▼ 閉じる" : "▶ 展開"}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* トレンド分析 */}
          {trends && trends.has_data && (
            <div
              style={{
                padding: "16px",
                backgroundColor: "#eff6ff",
                borderRadius: "12px",
                border: "1px solid #bfdbfe",
              }}
            >
              <h3
                style={{
                  fontSize: "16px",
                  fontWeight: "600",
                  color: "#1e40af",
                  marginBottom: "12px",
                }}
              >
                📊 過去7日間のトレンド
              </h3>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: "12px",
                  marginBottom: "12px",
                }}
              >
                <div style={{ textAlign: "center" }}>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#6b7280",
                      marginBottom: "4px",
                    }}
                  >
                    平均気分
                  </div>
                  <div
                    style={{
                      fontSize: "24px",
                      fontWeight: "bold",
                      color: getScoreColor(trends.averages.mood),
                    }}
                  >
                    {trends.averages.mood}
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#6b7280",
                      marginBottom: "4px",
                    }}
                  >
                    平均エネルギー
                  </div>
                  <div
                    style={{
                      fontSize: "24px",
                      fontWeight: "bold",
                      color: getScoreColor(trends.averages.energy),
                    }}
                  >
                    {trends.averages.energy}
                  </div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#6b7280",
                      marginBottom: "4px",
                    }}
                  >
                    平均不安
                  </div>
                  <div
                    style={{
                      fontSize: "24px",
                      fontWeight: "bold",
                      color: getScoreColor(trends.averages.anxiety, true),
                    }}
                  >
                    {trends.averages.anxiety}
                  </div>
                </div>
              </div>
              {trends.trend_analysis && (
                <div
                  style={{
                    padding: "8px 12px",
                    backgroundColor: "#dbeafe",
                    borderRadius: "6px",
                    fontSize: "13px",
                    color: "#1e40af",
                  }}
                >
                  📈 気分の変化:{" "}
                  <strong>{trends.trend_analysis.mood_trend}</strong>
                  {trends.trend_analysis.mood_change !== 0 && (
                    <span>
                      {" "}
                      ({trends.trend_analysis.mood_change > 0 ? "+" : ""}
                      {trends.trend_analysis.mood_change})
                    </span>
                  )}
                </div>
              )}
            </div>
          )}

          {/* エピソード記憶 */}
          {episodes.length > 0 && (
            <div>
              <h3
                style={{
                  fontSize: "16px",
                  fontWeight: "600",
                  color: "#475569",
                  marginBottom: "12px",
                }}
              >
                📖 重要なエピソード
              </h3>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                {episodes.map((episode) => (
                  <div
                    key={episode.id}
                    style={{
                      padding: "12px",
                      backgroundColor: "#f8fafc",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                      borderLeft: `4px solid ${getEmotionColor(
                        episode.emotion,
                      )}`,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "start",
                        marginBottom: "8px",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "14px",
                          fontWeight: "600",
                          color: "#1e293b",
                        }}
                      >
                        {episode.title}
                      </div>
                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          alignItems: "center",
                        }}
                      >
                        <span
                          style={{
                            padding: "2px 8px",
                            backgroundColor: getEmotionColor(episode.emotion),
                            color: "white",
                            borderRadius: "12px",
                            fontSize: "11px",
                            fontWeight: "500",
                          }}
                        >
                          {episode.emotion}
                        </span>
                        <span style={{ fontSize: "11px", color: "#6b7280" }}>
                          重要度: {Math.round(episode.importance_score * 100)}%
                        </span>
                      </div>
                    </div>
                    <div
                      style={{
                        fontSize: "13px",
                        color: "#475569",
                        marginBottom: "8px",
                      }}
                    >
                      {episode.content}
                    </div>
                    <div style={{ fontSize: "11px", color: "#9ca3af" }}>
                      {new Date(episode.timestamp).toLocaleString("ja-JP")}
                      {episode.context.time_period &&
                        ` • ${episode.context.time_period}`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 感情履歴チャート（簡易版） */}
          {emotionHistory.length > 0 && (
            <div>
              <h3
                style={{
                  fontSize: "16px",
                  fontWeight: "600",
                  color: "#475569",
                  marginBottom: "12px",
                }}
              >
                📉 感情の推移
              </h3>
              <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
              >
                {emotionHistory.slice(0, 5).map((record) => (
                  <div
                    key={record.id}
                    style={{
                      padding: "10px",
                      backgroundColor: "#fafafa",
                      borderRadius: "6px",
                      border: "1px solid #e5e7eb",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "6px",
                      }}
                    >
                      <div style={{ fontSize: "12px", color: "#6b7280" }}>
                        {new Date(record.timestamp).toLocaleString("ja-JP", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                      <div style={{ fontSize: "11px", color: "#9ca3af" }}>
                        気分: {record.mood} | エネルギー: {record.energy} |
                        不安: {record.anxiety}
                      </div>
                    </div>
                    {record.notes && (
                      <div
                        style={{
                          fontSize: "12px",
                          color: "#475569",
                          fontStyle: "italic",
                        }}
                      >
                        "{record.notes}"
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* データなし表示 */}
          {!loading && episodes.length === 0 && emotionHistory.length === 0 && (
            <div
              style={{
                padding: "24px",
                textAlign: "center",
                color: "#6b7280",
                backgroundColor: "#f9fafb",
                borderRadius: "12px",
                border: "1px solid #e5e7eb",
              }}
            >
              <p style={{ fontSize: "14px" }}>
                まだ記録されたデータがありません。
                <br />
                会話を通じて自動的に記録されます。
              </p>
            </div>
          )}
        </div>
      )}

      {!isExpanded && (
        <p style={{ fontSize: "13px", color: "#6b7280", textAlign: "center" }}>
          クリックして感情履歴とエピソードを表示
        </p>
      )}
    </div>
  );
};
