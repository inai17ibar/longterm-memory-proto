import React, { useState, useEffect } from 'react';

interface UserProfile {
  user_id: string;
  name?: string;
  job?: string;
  hobbies?: string[];
  age?: string;
  location?: string;
  family?: string;
  concerns?: string;
  goals?: string;
  personality?: string;
  experiences?: string;
  symptoms?: string;
  triggers?: string;
  coping_methods?: string;
  support_system?: string;
  medication?: string;
  work_status?: string;
  daily_routine?: string;
  emotional_state?: string;
  created_at?: string;
  updated_at?: string;
}

interface UserState {
  mood?: number;
  energy?: number;
  anxiety?: number;
  main_topics?: string[];
  need?: string;
  modes?: string[];
  state_comment?: string;
  contextual_patterns?: Record<string, string>;
}

interface ProfileDebugProps {
  userId: string;
  apiUrl: string;
}

export const ProfileDebug: React.FC<ProfileDebugProps> = ({ userId, apiUrl }) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [userState, setUserState] = useState<UserState | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const loadProfileData = async () => {
    setLoading(true);
    setError('');

    try {
      // プロファイル取得
      const profileResponse = await fetch(`${apiUrl}/api/profile/${userId}`);
      if (profileResponse.ok) {
        const profileData = await profileResponse.json();
        setProfile(profileData.profile);
      } else if (profileResponse.status === 404) {
        setProfile(null);
      }

      // ユーザー状態取得
      const stateResponse = await fetch(`${apiUrl}/api/state/${userId}`);
      if (stateResponse.ok) {
        const stateData = await stateResponse.json();
        setUserState(stateData.state);
      } else if (stateResponse.status === 404) {
        setUserState(null);
      }
    } catch (err) {
      setError('データの取得に失敗しました');
      console.error('Error loading profile data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      loadProfileData();
    }
  }, [userId]);

  const renderProfileField = (label: string, value: any, emoji: string = '📝') => {
    if (!value) return null;

    const isArray = Array.isArray(value);
    const displayValue = isArray ? value.join(', ') : value;

    return (
      <div style={{
        padding: '8px 12px',
        backgroundColor: '#f8fafc',
        borderRadius: '6px',
        marginBottom: '8px',
        border: '1px solid #e2e8f0'
      }}>
        <div style={{
          fontSize: '12px',
          fontWeight: '600',
          color: '#475569',
          marginBottom: '4px'
        }}>
          {emoji} {label}
        </div>
        <div style={{
          fontSize: '13px',
          color: '#1e293b',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}>
          {displayValue}
        </div>
      </div>
    );
  };

  const renderStateMetric = (label: string, value: number | undefined, maxValue: number = 10) => {
    if (value === undefined || value === null) return null;

    const percentage = (value / maxValue) * 100;
    const color =
      value >= 7 ? '#ef4444' :
      value >= 4 ? '#f59e0b' :
      '#10b981';

    return (
      <div style={{ marginBottom: '12px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '4px'
        }}>
          <span style={{ fontSize: '13px', fontWeight: '500', color: '#475569' }}>
            {label}
          </span>
          <span style={{ fontSize: '13px', fontWeight: '600', color }}>
            {value}/{maxValue}
          </span>
        </div>
        <div style={{
          width: '100%',
          height: '8px',
          backgroundColor: '#e5e7eb',
          borderRadius: '4px',
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${percentage}%`,
            height: '100%',
            backgroundColor: color,
            transition: 'width 0.3s ease'
          }} />
        </div>
      </div>
    );
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '16px',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      border: '2px solid #8b5cf6',
      padding: '24px',
      marginTop: '24px'
    }}>
      {/* ヘッダー */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h2 style={{
          fontWeight: 'bold',
          fontSize: '18px',
          color: '#7c3aed',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          🔍 プロファイル・デバッグ情報
        </h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={loadProfileData}
            disabled={loading}
            style={{
              padding: '6px 12px',
              backgroundColor: '#8b5cf6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              opacity: loading ? 0.5 : 1
            }}
          >
            {loading ? '更新中...' : '🔄 更新'}
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              padding: '6px 12px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            {isExpanded ? '▼ 閉じる' : '▶ 展開'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '14px',
          color: '#dc2626'
        }}>
          {error}
        </div>
      )}

      {isExpanded && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* ユーザー状態分析 */}
          {userState && (
            <div style={{
              padding: '16px',
              backgroundColor: '#faf5ff',
              borderRadius: '12px',
              border: '1px solid #e9d5ff'
            }}>
              <h3 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: '#7c3aed',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                📊 現在の状態分析
              </h3>

              {/* メトリクス */}
              <div style={{ marginBottom: '16px' }}>
                {renderStateMetric('気分 (Mood)', userState.mood)}
                {renderStateMetric('エネルギー (Energy)', userState.energy)}
                {renderStateMetric('不安 (Anxiety)', userState.anxiety)}
              </div>

              {/* テキスト情報 */}
              {userState.main_topics && userState.main_topics.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '13px', fontWeight: '500', color: '#475569', marginBottom: '4px' }}>
                    主なテーマ:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {userState.main_topics.map((topic, index) => (
                      <span key={index} style={{
                        padding: '4px 10px',
                        backgroundColor: '#ddd6fe',
                        color: '#5b21b6',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {userState.need && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '13px', fontWeight: '500', color: '#475569', marginBottom: '4px' }}>
                    求めていること:
                  </div>
                  <div style={{
                    padding: '8px 12px',
                    backgroundColor: '#fef3c7',
                    borderRadius: '6px',
                    fontSize: '13px',
                    color: '#92400e'
                  }}>
                    {userState.need}
                  </div>
                </div>
              )}

              {userState.modes && userState.modes.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '13px', fontWeight: '500', color: '#475569', marginBottom: '4px' }}>
                    推奨モード:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {userState.modes.map((mode, index) => (
                      <span key={index} style={{
                        padding: '4px 10px',
                        backgroundColor: '#dbeafe',
                        color: '#1e40af',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {mode}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {userState.state_comment && (
                <div style={{
                  padding: '12px',
                  backgroundColor: '#f0f9ff',
                  borderRadius: '8px',
                  fontSize: '13px',
                  color: '#0c4a6e',
                  fontStyle: 'italic'
                }}>
                  💭 {userState.state_comment}
                </div>
              )}

              {/* 文脈パターン */}
              {userState.contextual_patterns && Object.keys(userState.contextual_patterns).length > 0 && (
                <div style={{ marginTop: '16px' }}>
                  <div style={{ fontSize: '13px', fontWeight: '500', color: '#475569', marginBottom: '8px' }}>
                    🔍 文脈パターン:
                  </div>
                  {Object.entries(userState.contextual_patterns).map(([key, value]) => (
                    <div key={key} style={{
                      padding: '8px 12px',
                      backgroundColor: '#fff7ed',
                      borderRadius: '6px',
                      marginBottom: '6px',
                      fontSize: '12px',
                      color: '#c2410c'
                    }}>
                      • {value}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ユーザープロファイル */}
          {profile ? (
            <div style={{
              padding: '16px',
              backgroundColor: '#f8fafc',
              borderRadius: '12px',
              border: '1px solid #e2e8f0'
            }}>
              <h3 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: '#475569',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                👤 ユーザープロファイル
              </h3>

              {/* 基本情報 */}
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#64748b', marginBottom: '8px' }}>
                  基本情報
                </h4>
                {renderProfileField('名前', profile.name, '👤')}
                {renderProfileField('年齢', profile.age, '🎂')}
                {renderProfileField('職業', profile.job, '💼')}
                {renderProfileField('趣味', profile.hobbies, '🎨')}
                {renderProfileField('居住地', profile.location, '🏠')}
                {renderProfileField('家族構成', profile.family, '👨‍👩‍👧‍👦')}
              </div>

              {/* メンタルヘルス情報 */}
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#64748b', marginBottom: '8px' }}>
                  メンタルヘルス情報
                </h4>
                {renderProfileField('現在の悩み', profile.concerns, '💭')}
                {renderProfileField('目標', profile.goals, '🎯')}
                {renderProfileField('性格', profile.personality, '⭐')}
                {renderProfileField('重要な体験', profile.experiences, '📚')}
                {renderProfileField('症状', profile.symptoms, '🩺')}
                {renderProfileField('ストレス要因', profile.triggers, '⚠️')}
                {renderProfileField('対処法', profile.coping_methods, '🛠️')}
                {renderProfileField('サポート体制', profile.support_system, '🤝')}
                {renderProfileField('服薬・通院', profile.medication, '💊')}
                {renderProfileField('勤務状況', profile.work_status, '💼')}
                {renderProfileField('日常生活', profile.daily_routine, '📅')}
                {renderProfileField('感情状態', profile.emotional_state, '💭')}
              </div>

              {/* メタデータ */}
              <div style={{
                padding: '12px',
                backgroundColor: '#f1f5f9',
                borderRadius: '8px',
                border: '1px solid #cbd5e1'
              }}>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  <div>作成日時: {profile.created_at ? new Date(profile.created_at).toLocaleString('ja-JP') : 'N/A'}</div>
                  <div>更新日時: {profile.updated_at ? new Date(profile.updated_at).toLocaleString('ja-JP') : 'N/A'}</div>
                </div>
              </div>
            </div>
          ) : (
            <div style={{
              padding: '24px',
              textAlign: 'center',
              color: '#6b7280',
              backgroundColor: '#f9fafb',
              borderRadius: '12px',
              border: '1px solid #e5e7eb'
            }}>
              <p style={{ fontSize: '14px' }}>
                プロファイル情報がまだ作成されていません。<br />
                会話を通じて情報が自動的に記録されます。
              </p>
            </div>
          )}

          {/* JSONデバッグ表示 */}
          <details style={{
            padding: '16px',
            backgroundColor: '#1f2937',
            borderRadius: '12px',
            color: '#e5e7eb'
          }}>
            <summary style={{
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              marginBottom: '12px',
              color: '#9ca3af'
            }}>
              📋 JSON デバッグデータ
            </summary>
            <div style={{
              marginTop: '12px',
              fontSize: '12px',
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
              backgroundColor: '#111827',
              padding: '12px',
              borderRadius: '8px',
              maxHeight: '400px',
              overflowY: 'auto'
            }}>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ color: '#10b981', fontWeight: '600', marginBottom: '4px' }}>
                  PROFILE:
                </div>
                {JSON.stringify(profile, null, 2)}
              </div>
              <div>
                <div style={{ color: '#3b82f6', fontWeight: '600', marginBottom: '4px' }}>
                  USER_STATE:
                </div>
                {JSON.stringify(userState, null, 2)}
              </div>
            </div>
          </details>
        </div>
      )}

      {!isExpanded && (
        <p style={{ fontSize: '13px', color: '#6b7280', textAlign: 'center' }}>
          クリックして詳細を表示
        </p>
      )}
    </div>
  );
};
