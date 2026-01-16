import React, { useState, useEffect } from "react";

interface SystemPromptEditorProps {
  userId: string;
  apiUrl: string;
}

export const SystemPromptEditor: React.FC<SystemPromptEditorProps> = ({
  userId,
  apiUrl,
}) => {
  const [customPrompt, setCustomPrompt] = useState("");
  const [defaultPrompt, setDefaultPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [useCustom, setUseCustom] = useState(false);

  useEffect(() => {
    loadPrompts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, apiUrl]);

  const loadPrompts = async () => {
    try {
      setIsLoading(true);

      // デフォルトプロンプトを取得
      const defaultResponse = await fetch(
        `${apiUrl}/api/system-prompt/default`,
      );
      const defaultData = await defaultResponse.json();
      setDefaultPrompt(defaultData.default_prompt);

      // ユーザープロファイルからカスタムプロンプトを取得
      const profileResponse = await fetch(
        `${apiUrl}/api/extended-profile/${userId}`,
      );
      const profileData = await profileResponse.json();

      if (profileData.profile.profile_settings.custom_system_prompt) {
        setCustomPrompt(
          profileData.profile.profile_settings.custom_system_prompt,
        );
        setUseCustom(true);
      } else {
        setCustomPrompt(defaultData.default_prompt);
        setUseCustom(false);
      }
    } catch (error) {
      console.error("Error loading prompts:", error);
      setMessage("プロンプトの読み込みに失敗しました");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);

      // プロファイルを取得
      const profileResponse = await fetch(
        `${apiUrl}/api/extended-profile/${userId}`,
      );
      const profileData = await profileResponse.json();

      // カスタムプロンプトを更新
      profileData.profile.profile_settings.custom_system_prompt = useCustom
        ? customPrompt
        : null;

      // プロファイルを保存
      await fetch(`${apiUrl}/api/extended-profile/${userId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(profileData.profile),
      });

      setMessage("システムプロンプトを保存しました");
    } catch (error) {
      console.error("Error saving prompt:", error);
      setMessage("保存に失敗しました: " + (error as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setCustomPrompt(defaultPrompt);
    setMessage("デフォルトプロンプトに戻しました");
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
        ⚙️ システムプロンプト設定
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
        <label
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: "12px",
            fontSize: "14px",
            cursor: "pointer",
          }}
        >
          <input
            type="checkbox"
            checked={useCustom}
            onChange={(e) => setUseCustom(e.target.checked)}
            style={{ marginRight: "8px" }}
          />
          カスタムプロンプトを使用する
        </label>

        <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
          <button
            onClick={handleSave}
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
            保存
          </button>
          <button
            onClick={handleReset}
            disabled={isLoading}
            style={{
              padding: "8px 16px",
              backgroundColor: "#f59e0b",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            デフォルトに戻す
          </button>
          <button
            onClick={loadPrompts}
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
            再読込
          </button>
        </div>

        <div style={{ marginBottom: "12px" }}>
          <div
            style={{
              padding: "8px",
              backgroundColor: "#fef3c7",
              borderRadius: "4px",
              fontSize: "12px",
              marginBottom: "8px",
            }}
          >
            💡 使用可能な変数: {"{ai_name}"}, {"{ai_personality}"},{" "}
            {"{user_context}"}, {"{conversation_context}"},{" "}
            {"{response_pattern}"}
          </div>
        </div>

        <textarea
          value={useCustom ? customPrompt : defaultPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          disabled={!useCustom}
          placeholder="システムプロンプトを入力してください"
          style={{
            width: "100%",
            height: "400px",
            padding: "12px",
            border: "1px solid #d1d5db",
            borderRadius: "4px",
            fontSize: "13px",
            fontFamily: "monospace",
            resize: "vertical",
            backgroundColor: useCustom ? "white" : "#f3f4f6",
            color: useCustom ? "black" : "#6b7280",
          }}
        />
      </div>

      <div
        style={{
          marginTop: "12px",
          padding: "12px",
          backgroundColor: "#e0e7ff",
          borderRadius: "4px",
          fontSize: "12px",
        }}
      >
        <strong>ヒント:</strong>
        <ul style={{ marginTop: "8px", paddingLeft: "20px" }}>
          <li>
            カスタムプロンプトを使用すると、AIの性格や応答スタイルを自由にカスタマイズできます
          </li>
          <li>変数を使うことで、ユーザー情報や会話履歴を動的に埋め込めます</li>
          <li>デフォルトに戻すボタンで、いつでも元のプロンプトに戻せます</li>
        </ul>
      </div>
    </div>
  );
};
