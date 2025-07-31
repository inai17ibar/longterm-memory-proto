import React, { useState, useEffect } from 'react';

function App() {
  const [currentMessage, setCurrentMessage] = useState('');
  const [messages, setMessages] = useState<Array<{user_message: string, ai_response: string}>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [userId, setUserId] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [userInfo, setUserInfo] = useState<any>(null);
  const [isExporting, setIsExporting] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // ユーザーIDを生成または取得
    let storedUserId = localStorage.getItem('counseling_user_id');
    if (!storedUserId) {
      storedUserId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('counseling_user_id', storedUserId);
    }
    setUserId(storedUserId);
    
    // 過去の会話履歴とユーザー情報を読み込み
    loadConversationHistory(storedUserId);
    loadUserData(storedUserId);
  }, []);

  const loadUserData = async (uid: string) => {
    try {
      const response = await fetch(`${API_URL}/api/users/${uid}`);
      if (response.ok) {
        const userData = await response.json();
        setUserInfo(userData);
      }
    } catch (error) {
      console.log('No existing user data found');
    }
  };

  const loadConversationHistory = async (uid: string) => {
    try {
      const response = await fetch(`${API_URL}/api/conversations/${uid}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.conversations || []);
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          message: currentMessage
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      const newMessage = {
        user_message: currentMessage,
        ai_response: data.response
      };

      setMessages(prev => [...prev, newMessage]);
      setCurrentMessage('');

      // ユーザー情報が更新された場合、再読み込み
      if (data.user_info_updated) {
        loadUserData(userId);
      }
    } catch (error) {
      setError('メッセージの送信に失敗しました。もう一度お試しください。');
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickMessage = (message: string) => {
    setCurrentMessage(message);
  };

  const clearConversation = async () => {
    if (!window.confirm('会話履歴を削除しますか？この操作は取り消せません。')) return;

    try {
      await fetch(`${API_URL}/api/users/${userId}`, {
        method: 'DELETE'
      });
      setMessages([]);
      setUserInfo(null);
      localStorage.removeItem('counseling_user_id');
      const newUserId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('counseling_user_id', newUserId);
      setUserId(newUserId);
    } catch (error) {
      setError('データの削除に失敗しました。');
    }
  };

  const exportConversations = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(`${API_URL}/api/export-conversations/${userId}`);
      if (response.ok) {
        const data = await response.json();
        
        const blob = new Blob([data.csv_data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('会話履歴のエクスポートに失敗しました');
      }
    } catch (error) {
      setError('エクスポート中にエラーが発生しました');
    } finally {
      setIsExporting(false);
    }
  };
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#faf5ff', padding: '16px' }}>
      <div style={{ maxWidth: '672px', margin: '0 auto' }}>
        {/* ヘッダー */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{ 
            fontSize: '24px', 
            fontWeight: 'bold', 
            color: '#1f2937', 
            marginBottom: '8px'
          }}>
            🕊️ メンタルヘルス カウンセリング
          </h1>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>あなたの心の健康をサポートします</p>
        </div>

        {/* メインコンテンツエリア */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* プレースホルダーカード */}
          <div style={{
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #f3f4f6',
            padding: '24px'
          }}>
            <h2 style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '16px' }}>
              カウンセリング チャット
            </h2>
            
            {/* チャットエリア */}
            <div style={{ 
              height: '320px', 
              border: '1px solid #e5e7eb', 
              borderRadius: '8px', 
              marginBottom: '16px',
              padding: '16px',
              backgroundColor: '#f9fafb',
              overflowY: 'auto'
            }}>
              {messages.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '120px' }}>
                  <p>こんにちは。お話をお聞かせください。</p>
                  <p style={{ fontSize: '12px', marginTop: '8px' }}>
                    あなたの名前、趣味、お仕事などについて教えていただければ、より良いサポートができます。
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {messages.map((message, index) => (
                    <div key={index}>
                      {/* ユーザーメッセージ */}
                      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
                        <div style={{
                          backgroundColor: '#3b82f6',
                          color: 'white',
                          padding: '8px 12px',
                          borderRadius: '16px',
                          maxWidth: '70%',
                          fontSize: '14px'
                        }}>
                          {message.user_message}
                        </div>
                      </div>
                      {/* AIレスポンス */}
                      <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                        <div style={{
                          backgroundColor: '#e5e7eb',
                          color: '#1f2937',
                          padding: '8px 12px',
                          borderRadius: '16px',
                          maxWidth: '70%',
                          fontSize: '14px'
                        }}>
                          {message.ai_response}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                      <div style={{
                        backgroundColor: '#e5e7eb',
                        color: '#6b7280',
                        padding: '8px 12px',
                        borderRadius: '16px',
                        fontSize: '14px'
                      }}>
                        入力中...
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* エラー表示 */}
            {error && (
              <div style={{
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '16px'
              }}>
                <p style={{ color: '#dc2626', fontSize: '14px' }}>{error}</p>
              </div>
            )}

            {/* よくある相談ボタン */}
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>よくある相談:</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                <button 
                  onClick={() => handleQuickMessage('気分転換の方法')}
                  disabled={isLoading}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '9999px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    opacity: isLoading ? 0.5 : 1
                  }}>
                  気分転換の方法
                </button>
                <button 
                  onClick={() => handleQuickMessage('不安な気持ち')}
                  disabled={isLoading}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '9999px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    opacity: isLoading ? 0.5 : 1
                  }}>
                  不安な気持ち
                </button>
              </div>
            </div>

            {/* 入力エリア */}
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="メッセージを入力してください..."
                disabled={isLoading}
                style={{
                  flex: 1,
                  padding: '8px 16px',
                  border: '1px solid #d1d5db',
                  borderRadius: '9999px',
                  outline: 'none',
                  fontSize: '14px',
                  opacity: isLoading ? 0.5 : 1
                }}
              />
              <button 
                onClick={sendMessage}
                disabled={isLoading || !currentMessage.trim()}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '9999px',
                  cursor: 'pointer',
                  opacity: (isLoading || !currentMessage.trim()) ? 0.5 : 1
                }}>
                {isLoading ? '送信中...' : '送信'}
              </button>
            </div>
          </div>

          {/* 記憶された情報カード */}
          <div style={{
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #f3f4f6',
            padding: '24px'
          }}>
            <h2 style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '16px' }}>
              記憶された情報
            </h2>
            {userInfo ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {userInfo.name && (
                  <div>
                    <span style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280' }}>名前:</span>
                    <p style={{ fontSize: '14px', marginTop: '2px' }}>{userInfo.name}</p>
                  </div>
                )}
                {userInfo.job && (
                  <div>
                    <span style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280' }}>職業:</span>
                    <p style={{ fontSize: '14px', marginTop: '2px' }}>{userInfo.job}</p>
                  </div>
                )}
                {userInfo.hobbies && userInfo.hobbies.length > 0 && (
                  <div>
                    <span style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280' }}>趣味:</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                      {userInfo.hobbies.map((hobby: string, index: number) => (
                        <span key={index} style={{
                          display: 'inline-block',
                          padding: '2px 8px',
                          fontSize: '12px',
                          backgroundColor: '#dbeafe',
                          color: '#1e40af',
                          borderRadius: '9999px'
                        }}>
                          {hobby}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p style={{ fontSize: '14px', color: '#6b7280' }}>
                まだ情報が記録されていません。会話を通じて情報を教えてください。
              </p>
            )}
          </div>

          {/* 設定カード */}
          <div style={{
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #f3f4f6',
            padding: '24px'
          }}>
            <h2 style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '16px' }}>
              設定
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button 
                onClick={clearConversation}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                🗑️ 会話履歴を削除
              </button>
              <button 
                onClick={exportConversations}
                disabled={isExporting}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  backgroundColor: '#f3f4f6',
                  color: '#374151',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  opacity: isExporting ? 0.5 : 1
                }}
              >
                📥 {isExporting ? 'エクスポート中...' : '会話履歴をCSVでダウンロード'}
              </button>
              <p style={{ fontSize: '12px', color: '#6b7280', textAlign: 'center', marginTop: '8px' }}>
                ユーザーID: {userId.slice(-8)}...
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;