import React, { useState, useEffect } from "react";

interface MemoryNode {
  id: string;
  label: string;
  type: string;
  importance: number;
  timestamp: string;
}

interface MemoryEdge {
  source: string;
  target: string;
  weight: number;
  reason: string;
}

interface MemoryInsightsProps {
  userId: string;
  apiUrl: string;
}

export const MemoryInsights: React.FC<MemoryInsightsProps> = ({
  userId,
  apiUrl,
}) => {
  const [summary, setSummary] = useState<any>(null);
  const [graph, setGraph] = useState<{
    nodes: MemoryNode[];
    edges: MemoryEdge[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      // 記憶の要約取得
      const summaryResponse = await fetch(
        `${apiUrl}/api/memories/${userId}/summary?days=30`,
      );
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setSummary(summaryData.summary);
      }

      // 記憶グラフ取得
      const graphResponse = await fetch(
        `${apiUrl}/api/memories/${userId}/graph`,
      );
      if (graphResponse.ok) {
        const graphData = await graphResponse.json();
        setGraph(graphData.graph);
      }
    } catch (err) {
      console.error("Error loading memory insights:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId && isExpanded) {
      loadData();
    }
  }, [userId, isExpanded]);

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      concerns: "#ef4444",
      goals: "#10b981",
      symptoms: "#f59e0b",
      triggers: "#f97316",
      coping_methods: "#3b82f6",
      emotional_state: "#ec4899",
      work_status: "#6b7280",
      support_system: "#14b8a6",
    };
    return colors[type] || "#9ca3af";
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      concerns: "悩み",
      goals: "目標",
      symptoms: "症状",
      triggers: "ストレス",
      coping_methods: "対処法",
      emotional_state: "感情",
      work_status: "仕事",
      support_system: "サポート",
    };
    return labels[type] || type;
  };

  return (
    <div
      style={{
        background: "white",
        borderRadius: "16px",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
        border: "2px solid #10b981",
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
            color: "#059669",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          🧩 記憶の統合・関連性
        </h2>
        <div style={{ display: "flex", gap: "8px" }}>
          {isExpanded && (
            <button
              onClick={loadData}
              disabled={loading}
              style={{
                padding: "6px 12px",
                backgroundColor: "#10b981",
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
          {/* 記憶の要約 */}
          {summary && summary.has_data && (
            <div>
              <h3
                style={{
                  fontSize: "16px",
                  fontWeight: "600",
                  color: "#475569",
                  marginBottom: "12px",
                }}
              >
                📝 過去30日間の記憶要約
              </h3>
              <div
                style={{
                  padding: "12px",
                  backgroundColor: "#f0fdf4",
                  borderRadius: "8px",
                  border: "1px solid #bbf7d0",
                  marginBottom: "12px",
                }}
              >
                <div
                  style={{
                    fontSize: "13px",
                    color: "#059669",
                    marginBottom: "8px",
                  }}
                >
                  記憶総数: <strong>{summary.total_memories}件</strong> （
                  {summary.period_days}日間）
                </div>
              </div>

              {/* カテゴリ別要約 */}
              <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
              >
                {Object.entries(summary.by_type || {}).map(
                  ([type, data]: [string, any]) => (
                    <div
                      key={type}
                      style={{
                        padding: "10px 12px",
                        backgroundColor: "#fafafa",
                        borderRadius: "6px",
                        border: "1px solid #e5e7eb",
                        borderLeft: `4px solid ${getTypeColor(type)}`,
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "4px",
                        }}
                      >
                        <span
                          style={{
                            fontSize: "13px",
                            fontWeight: "600",
                            color: "#1e293b",
                          }}
                        >
                          {getTypeLabel(type)}
                        </span>
                        <span style={{ fontSize: "11px", color: "#6b7280" }}>
                          {data.count}件
                        </span>
                      </div>
                      <div
                        style={{
                          fontSize: "12px",
                          color: "#64748b",
                          lineHeight: "1.5",
                        }}
                      >
                        {data.summary}
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}

          {/* 記憶の関連性グラフ（簡易版） */}
          {graph && graph.nodes && graph.nodes.length > 0 && (
            <div>
              <h3
                style={{
                  fontSize: "16px",
                  fontWeight: "600",
                  color: "#475569",
                  marginBottom: "12px",
                }}
              >
                🕸️ 記憶の関連性ネットワーク
              </h3>
              <div
                style={{
                  padding: "16px",
                  backgroundColor: "#f8fafc",
                  borderRadius: "12px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div
                  style={{
                    fontSize: "13px",
                    color: "#475569",
                    marginBottom: "12px",
                  }}
                >
                  ノード数: {graph.nodes.length} | 関連性: {graph.edges.length}
                  件
                </div>

                {/* ノードリスト（重要度順） */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  {graph.nodes.slice(0, 10).map((node) => {
                    // このノードに関連するエッジを検索
                    const relatedEdges = graph.edges.filter(
                      (edge) =>
                        edge.source === node.id || edge.target === node.id,
                    );

                    return (
                      <div
                        key={node.id}
                        style={{
                          padding: "8px 10px",
                          backgroundColor: "white",
                          borderRadius: "6px",
                          border: "1px solid #e5e7eb",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "start",
                            marginBottom: "4px",
                          }}
                        >
                          <div style={{ flex: 1 }}>
                            <span
                              style={{
                                padding: "2px 6px",
                                backgroundColor: getTypeColor(node.type),
                                color: "white",
                                borderRadius: "4px",
                                fontSize: "10px",
                                fontWeight: "500",
                                marginRight: "6px",
                              }}
                            >
                              {getTypeLabel(node.type)}
                            </span>
                            <span
                              style={{ fontSize: "12px", color: "#1e293b" }}
                            >
                              {node.label}
                            </span>
                          </div>
                          <div
                            style={{
                              fontSize: "10px",
                              color: "#9ca3af",
                              whiteSpace: "nowrap",
                              marginLeft: "8px",
                            }}
                          >
                            重要度 {Math.round(node.importance * 100)}%
                          </div>
                        </div>
                        {relatedEdges.length > 0 && (
                          <div
                            style={{
                              fontSize: "11px",
                              color: "#6b7280",
                              marginTop: "4px",
                            }}
                          >
                            🔗 {relatedEdges.length}件の関連記憶
                            {relatedEdges.slice(0, 2).map((edge, idx) => (
                              <span
                                key={idx}
                                style={{
                                  marginLeft: "4px",
                                  fontSize: "10px",
                                  color: "#9ca3af",
                                }}
                              >
                                ({edge.reason})
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {graph.nodes.length > 10 && (
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#9ca3af",
                      textAlign: "center",
                      marginTop: "8px",
                    }}
                  >
                    他 {graph.nodes.length - 10}件の記憶
                  </div>
                )}
              </div>
            </div>
          )}

          {/* データなし表示 */}
          {!loading &&
            (!summary || !summary.has_data) &&
            (!graph || graph.nodes.length === 0) && (
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
                  まだ十分な記憶データがありません。
                  <br />
                  会話を重ねると、記憶の統合と関連性が分析されます。
                </p>
              </div>
            )}
        </div>
      )}

      {!isExpanded && (
        <p style={{ fontSize: "13px", color: "#6b7280", textAlign: "center" }}>
          クリックして記憶の統合と関連性を表示
        </p>
      )}
    </div>
  );
};
