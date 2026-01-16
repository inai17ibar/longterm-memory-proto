import React, { useState, useEffect } from "react";

interface ExtendedProfileManagerProps {
  userId: string;
  apiUrl: string;
}

export const ExtendedProfileManager: React.FC<ExtendedProfileManagerProps> = ({
  userId,
  apiUrl,
}) => {
  const [jsonInput, setJsonInput] = useState("");
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");

  const loadProfile = React.useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${apiUrl}/api/extended-profile/${userId}`);
      const data = await response.json();
      setJsonInput(JSON.stringify(data.profile, null, 2));
    } catch (error) {
      console.error("Error loading extended profile:", error);
      setMessage("プロファイルの読み込みに失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, [userId, apiUrl]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const loadSummary = async () => {
    try {
      const response = await fetch(
        `${apiUrl}/api/extended-profile/${userId}/summary`,
      );
      const data = await response.json();
      setSummary(data.summary);
    } catch (error) {
      console.error("Error loading summary:", error);
      setMessage("サマリーの読み込みに失敗しました");
    }
  };

  const handleUpdate = async () => {
    try {
      setIsLoading(true);
      const jsonData = JSON.parse(jsonInput);
      await fetch(`${apiUrl}/api/extended-profile/${userId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(jsonData),
      });
      setMessage("プロファイル更新完了");
      await loadProfile();
    } catch (error) {
      console.error("Error updating profile:", error);
      setMessage("更新に失敗しました: " + (error as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        backgroundColor: "#f9fafb",
        padding: "20px",
        borderRadius: "8px",
        marginBottom: "20px",
      }}
    >
      <h2
        style={{ fontWeight: "bold", fontSize: "18px", marginBottom: "16px" }}
      >
        📋 ユーザプロファイル管理
      </h2>

      {message && (
        <div
          style={{
            padding: "10px",
            marginBottom: "10px",
            backgroundColor: "#e0f2fe",
            borderRadius: "4px",
            fontSize: "14px",
          }}
        >
          {message}
        </div>
      )}

      <div style={{ marginBottom: "16px" }}>
        <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
          <button
            onClick={loadProfile}
            disabled={isLoading}
            style={{
              padding: "8px 16px",
              backgroundColor: "#3b82f6",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            プロファイル読込
          </button>
          <button
            onClick={handleUpdate}
            disabled={isLoading}
            style={{
              padding: "8px 16px",
              backgroundColor: "#10b981",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            プロファイル更新
          </button>
          <button
            onClick={loadSummary}
            disabled={isLoading}
            style={{
              padding: "8px 16px",
              backgroundColor: "#ec4899",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            サマリー表示
          </button>
        </div>

        <textarea
          value={jsonInput}
          onChange={(e) => setJsonInput(e.target.value)}
          placeholder="JSON形式のプロファイルデータを入力してください"
          style={{
            width: "100%",
            height: "300px",
            padding: "12px",
            border: "1px solid #d1d5db",
            borderRadius: "4px",
            fontSize: "12px",
            fontFamily: "monospace",
            resize: "vertical",
          }}
        />
      </div>

      {summary && (
        <div
          style={{
            marginTop: "16px",
            padding: "12px",
            backgroundColor: "#ffffff",
            border: "1px solid #d1d5db",
            borderRadius: "4px",
          }}
        >
          <h3
            style={{
              fontWeight: "bold",
              fontSize: "16px",
              marginBottom: "8px",
            }}
          >
            プロファイルサマリー（プロンプト用）
          </h3>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              fontSize: "13px",
              lineHeight: "1.6",
            }}
          >
            {summary}
          </pre>
        </div>
      )}
    </div>
  );
};
