import React, { useState, useEffect } from "react";
import "./ModelSettings.css";

interface ModelSettingsProps {
  userId: string;
  apiUrl: string;
}

export const ModelSettings: React.FC<ModelSettingsProps> = ({
  userId,
  apiUrl,
}) => {
  const [model, setModel] = useState("gpt-4.1-mini-2025-04-14");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(500);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");

  // 設定を読み込み
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/model-settings/${userId}`);
        if (response.ok) {
          const data = await response.json();
          setModel(data.model || "gpt-4.1-mini-2025-04-14");
          setTemperature(data.temperature || 0.7);
          setMaxTokens(data.max_tokens || 500);
        }
      } catch (error) {
        console.error("Error loading model settings:", error);
      }
    };
    loadSettings();
  }, [userId, apiUrl]);

  const handleSave = async () => {
    try {
      setIsLoading(true);
      setMessage("");

      const response = await fetch(`${apiUrl}/api/model-settings/${userId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model,
          temperature,
          max_tokens: maxTokens,
        }),
      });

      if (response.ok) {
        setMessage("設定を保存しました");
      } else {
        setMessage("保存に失敗しました");
      }
    } catch (error) {
      console.error("Error saving settings:", error);
      setMessage("保存中にエラーが発生しました");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        background: "white",
        borderRadius: "16px",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
        border: "1px solid #f3f4f6",
        padding: "24px",
        marginBottom: "24px",
      }}
    >
      <h2
        style={{ fontWeight: "bold", fontSize: "18px", marginBottom: "16px" }}
      >
        ⚙️ GPTモデル設定
      </h2>

      {message && (
        <div
          style={{
            padding: "10px",
            marginBottom: "16px",
            backgroundColor:
              message.includes("失敗") || message.includes("エラー")
                ? "#fee2e2"
                : "#d1fae5",
            color:
              message.includes("失敗") || message.includes("エラー")
                ? "#dc2626"
                : "#065f46",
            borderRadius: "8px",
            fontSize: "14px",
          }}
        >
          {message}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* モデル選択 */}
        <div>
          <label
            htmlFor="model"
            style={{
              display: "block",
              fontSize: "14px",
              fontWeight: "500",
              marginBottom: "8px",
              color: "#374151",
            }}
          >
            モデル
          </label>
          <select
            id="model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="model-select"
          >
            <option value="gpt-4.1-2025-04-14">
              GPT-4.1 (2025年最新・最高性能)
            </option>
            <option value="gpt-4.1-mini-2025-04-14">
              GPT-4.1 mini (最新・バランス型)
            </option>
            <option value="gpt-4.1-nano-2025-04-14">
              GPT-4.1 nano (最新・超高速)
            </option>
            <option value="gpt-4o">GPT-4o (高性能)</option>
            <option value="gpt-4o-mini">GPT-4o-mini (高速・低コスト)</option>
            <option value="gpt-4-turbo">GPT-4 Turbo (安定版)</option>
            <option value="gpt-4">GPT-4 (オリジナル)</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo (旧世代)</option>
          </select>
          <p style={{ fontSize: "12px", color: "#6b7280", marginTop: "4px" }}>
            使用するOpenAI GPTモデルを選択してください
          </p>
        </div>

        {/* Temperature設定 */}
        <div>
          <label
            htmlFor="temperature"
            style={{
              display: "block",
              fontSize: "14px",
              fontWeight: "500",
              marginBottom: "8px",
              color: "#374151",
            }}
          >
            Temperature: {temperature.toFixed(2)}
          </label>
          <input
            id="temperature"
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            style={{ width: "100%" }}
          />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "12px",
              color: "#6b7280",
              marginTop: "4px",
            }}
          >
            <span>0.0 (一貫性重視)</span>
            <span>1.0 (バランス)</span>
            <span>2.0 (創造性重視)</span>
          </div>
          <p style={{ fontSize: "12px", color: "#6b7280", marginTop: "4px" }}>
            低い値: より一貫性のある応答 / 高い値: より創造的で多様な応答
          </p>
        </div>

        {/* Max Tokens設定 */}
        <div>
          <label
            htmlFor="maxTokens"
            style={{
              display: "block",
              fontSize: "14px",
              fontWeight: "500",
              marginBottom: "8px",
              color: "#374151",
            }}
          >
            最大トークン数: {maxTokens}
          </label>
          <input
            id="maxTokens"
            type="range"
            min="100"
            max="4000"
            step="100"
            value={maxTokens}
            onChange={(e) => setMaxTokens(parseInt(e.target.value))}
            style={{ width: "100%" }}
          />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "12px",
              color: "#6b7280",
              marginTop: "4px",
            }}
          >
            <span>100</span>
            <span>2000</span>
            <span>4000</span>
          </div>
          <p style={{ fontSize: "12px", color: "#6b7280", marginTop: "4px" }}>
            AIの応答の最大長を制御します（日本語で約
            {Math.floor(maxTokens * 0.6)}文字程度）
          </p>
        </div>

        {/* 保存ボタン */}
        <button
          onClick={handleSave}
          disabled={isLoading}
          style={{
            padding: "10px 20px",
            backgroundColor: "#3b82f6",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "500",
            opacity: isLoading ? 0.5 : 1,
          }}
        >
          {isLoading ? "保存中..." : "設定を保存"}
        </button>
      </div>
    </div>
  );
};
