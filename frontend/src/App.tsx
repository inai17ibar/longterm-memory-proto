import React, { useState, useEffect } from 'react';
import { MemoryDisplay } from './MemoryDisplay';

function App() {
  const [currentMessage, setCurrentMessage] = useState('');
  const [messages, setMessages] = useState<Array<{user_message: string, ai_response: string}>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [userId, setUserId] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [userInfo, setUserInfo] = useState<{
    user_id: string;
    name?: string;
    hobbies?: string[];
    job?: string;
    other_info?: Record<string, any>;
    memory_items?: Array<{
      type: string;
      content: string;
      timestamp: string;
      source: string;
    }>;
  } | null>(null);
  const [langchainMemories, setLangchainMemories] = useState<Array<{
    id: string;
    content: string;
    memory_type: string;
    importance_score_original: number;
    importance_score_current: number;
    days_ago: number;
    timestamp: string;
    metadata: Record<string, any>;
  }>>([]);
  const [isExporting, setIsExporting] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

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

    // LangChain記憶を取得
    try {
      const memoryResponse = await fetch(`${API_URL}/api/memories/${uid}`);
      if (memoryResponse.ok) {
        const memoryData = await memoryResponse.json();
        setLangchainMemories(memoryData.memories || []);
      }
    } catch (error) {
      console.log('No LangChain memories found');
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
        console.log('User info was updated, reloading...'); // デバッグログ
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

  const clearChatHistory = async () => {
    if (!window.confirm('チャット履歴をクリアしますか？記憶された情報は保持されます。')) return;

    try {
      await fetch(`${API_URL}/api/conversations/${userId}`, {
        method: 'DELETE'
      });
      setMessages([]);
    } catch (error) {
      setError('チャット履歴のクリアに失敗しました。');
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
              height: '500px',
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
                          fontSize: '14px',
                          whiteSpace: 'pre-wrap'
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
                          fontSize: '14px',
                          whiteSpace: 'pre-wrap'
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
                <button 
                  onClick={() => handleQuickMessage('睡眠の問題')}
                  disabled={isLoading}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '9999px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    opacity: isLoading ? 0.5 : 1
                  }}>
                  睡眠の問題
                </button>
                <button 
                  onClick={() => handleQuickMessage('復職への不安')}
                  disabled={isLoading}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: '#f59e0b',
                    color: 'white',
                    border: 'none',
                    borderRadius: '9999px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    opacity: isLoading ? 0.5 : 1
                  }}>
                  復職への不安
                </button>
                <button 
                  onClick={() => handleQuickMessage('体調の変化')}
                  disabled={isLoading}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: '#ef4444',
                    color: 'white',
                    border: 'none',
                    borderRadius: '9999px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    opacity: isLoading ? 0.5 : 1
                  }}>
                  体調の変化
                </button>
                <button 
                  onClick={() => handleQuickMessage('人間関係の悩み')}
                  disabled={isLoading}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: '#8b5cf6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '9999px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    opacity: isLoading ? 0.5 : 1
                  }}>
                  人間関係の悩み
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

          {/* 記憶された情報カード（LangChainベース） */}
          <div style={{
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #f3f4f6',
            padding: '24px'
          }}>
            <h2 style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '16px' }}>
              🧠 記憶された情報（重要度順）
            </h2>
            {langchainMemories.length > 0 ? (
              <MemoryDisplay memories={langchainMemories} userInfo={userInfo} />
            ) : userInfo ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {/* 基本情報セクション */}
                <div style={{ padding: '12px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#2d3748', marginBottom: '8px' }}>
                    👤 基本情報
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {userInfo.name && (
                      <div>
                        <span style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280' }}>名前:</span>
                        <p style={{ fontSize: '14px', marginTop: '2px', whiteSpace: 'pre-wrap' }}>{userInfo.name}</p>
                      </div>
                    )}
                    {userInfo.job && (
                      <div>
                        <span style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280' }}>職業:</span>
                        <p style={{ fontSize: '14px', marginTop: '2px', whiteSpace: 'pre-wrap' }}>{userInfo.job}</p>
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
                </div>

                {/* カテゴリ別記憶情報 */}
                {userInfo.memory_items && userInfo.memory_items.length > 0 && (
                  <div>
                    {/* 悩み・心配事 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'concerns').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#991b1b', marginBottom: '8px' }}>
                          💭 悩み・心配事
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'concerns')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#7f1d1d', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 目標・願望 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'goals').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#14532d', marginBottom: '8px' }}>
                          🎯 目標・願望
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'goals')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#15803d', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 性格・特徴 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'personality').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#fef3c7', borderRadius: '8px', border: '1px solid #fde68a', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#92400e', marginBottom: '8px' }}>
                          ⭐ 性格・特徴
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'personality')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#a16207', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 重要な体験 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'experiences').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#ede9fe', borderRadius: '8px', border: '1px solid #c4b5fd', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#5b21b6', marginBottom: '8px' }}>
                          📚 重要な体験
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'experiences')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#6b21a8', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 家族・人間関係 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'family').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#ecfdf5', borderRadius: '8px', border: '1px solid #a7f3d0', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#065f46', marginBottom: '8px' }}>
                          👥 家族・人間関係
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'family')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#047857', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 症状・体調 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'symptoms').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#fef7ff', borderRadius: '8px', border: '1px solid #f3e8ff', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#7c2d92', marginBottom: '8px' }}>
                          🩺 症状・体調
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'symptoms')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#86198f', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* ストレス要因 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'triggers').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#fff7ed', borderRadius: '8px', border: '1px solid #fed7aa', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#c2410c', marginBottom: '8px' }}>
                          ⚠️ ストレス要因
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'triggers')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#ea580c', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 対処法 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'coping_methods').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#f0f9ff', borderRadius: '8px', border: '1px solid #bae6fd', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#0c4a6e', marginBottom: '8px' }}>
                          🛠️ 対処法・リラックス方法
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'coping_methods')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#0284c7', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* サポート体制 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'support_system').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#14532d', marginBottom: '8px' }}>
                          🤝 サポート体制
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'support_system')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#15803d', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 医療・服薬情報 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'medication').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#fefce8', borderRadius: '8px', border: '1px solid #fde047', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#a16207', marginBottom: '8px' }}>
                          💊 医療・服薬情報
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'medication')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#ca8a04', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 勤務・復職状況 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'work_status').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>
                          💼 勤務・復職状況
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'work_status')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#64748b', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 日常・生活パターン */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'daily_routine').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#fdf4ff', borderRadius: '8px', border: '1px solid #e9d5ff', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#7c3aed', marginBottom: '8px' }}>
                          📅 日常・生活パターン
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'daily_routine')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#8b5cf6', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 感情状態 */}
                    {userInfo.memory_items.filter((item: any) => item.type === 'emotional_state').length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#dc2626', marginBottom: '8px' }}>
                          💭 感情状態
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => item.type === 'emotional_state')
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#b91c1c', padding: '4px 0', whiteSpace: 'pre-wrap' }}>
                                • {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* その他の情報 */}
                    {userInfo.memory_items.filter((item: any) => !['concerns', 'goals', 'personality', 'experiences', 'family', 'name', 'job', 'hobby', 'symptoms', 'triggers', 'coping_methods', 'support_system', 'medication', 'work_status', 'daily_routine', 'emotional_state'].includes(item.type)).length > 0 && (
                      <div style={{ padding: '12px', backgroundColor: '#f1f5f9', borderRadius: '8px', border: '1px solid #cbd5e1', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>
                          📝 その他の情報
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {userInfo.memory_items
                            .filter((item: any) => !['concerns', 'goals', 'personality', 'experiences', 'family', 'name', 'job', 'hobby', 'symptoms', 'triggers', 'coping_methods', 'support_system', 'medication', 'work_status', 'daily_routine', 'emotional_state'].includes(item.type))
                            .map((item: any, index: number) => (
                              <div key={index} style={{ fontSize: '14px', color: '#64748b', padding: '4px 0' }}>
                                • {item.type}: {item.content}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
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
                onClick={clearChatHistory}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  backgroundColor: '#f59e0b',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                🧹 チャット履歴をクリア
              </button>
              <p style={{ fontSize: '11px', color: '#6b7280', textAlign: 'center', margin: '0 8px' }}>
                ※記憶された情報は保持されます
              </p>
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
                🗑️ 完全にデータを削除
              </button>
              <p style={{ fontSize: '11px', color: '#6b7280', textAlign: 'center', margin: '0 8px' }}>
                ※記憶された情報も全て削除されます
              </p>
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