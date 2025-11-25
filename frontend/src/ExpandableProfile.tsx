import React, { useState } from 'react';

interface Memory {
  content: string;
  type: string;
  importance: number;
  added_at: string;
}

interface UserState {
  mood: number;
  energy: number;
  anxiety: number;
  last_session?: string;
}

interface ProfileSection {
  title: string;
  data?: Record<string, any>;
  memories?: Memory[];
  state?: UserState;
  defaultExpanded?: boolean;
}

interface ExpandableProfileProps {
  userId: string;
  apiUrl: string;
}

export const ExpandableProfile: React.FC<ExpandableProfileProps> = ({ userId, apiUrl }) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['basic-info'])
  );
  const [profileData, setProfileData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/profile/${userId}`);
      const data = await response.json();
      setProfileData(data);
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchProfile();
  }, [userId]);

  const renderSection = (sectionId: string, title: string, content: React.ReactNode) => {
    const isExpanded = expandedSections.has(sectionId);

    return (
      <div
        style={{
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          marginBottom: '12px',
          overflow: 'hidden',
          background: '#fff'
        }}
      >
        <button
          onClick={() => toggleSection(sectionId)}
          style={{
            width: '100%',
            padding: '16px',
            background: isExpanded ? '#f5f5f5' : '#fafafa',
            border: 'none',
            borderBottom: isExpanded ? '1px solid #e0e0e0' : 'none',
            textAlign: 'left',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 600,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => {
            (e.target as HTMLElement).style.background =
              isExpanded ? '#efefef' : '#f5f5f5';
          }}
          onMouseLeave={(e) => {
            (e.target as HTMLElement).style.background =
              isExpanded ? '#f5f5f5' : '#fafafa';
          }}
        >
          <span>{title}</span>
          <span
            style={{
              transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s',
              fontSize: '20px',
              color: '#666'
            }}
          >
            ▼
          </span>
        </button>

        {isExpanded && (
          <div style={{ padding: '16px', borderTop: '1px solid #e0e0e0' }}>
            {content}
          </div>
        )}
      </div>
    );
  };

  const renderMemoryList = (memories: Memory[], limit: number = 10) => {
    if (!memories || memories.length === 0) {
      return <p style={{ color: '#999', fontSize: '14px' }}>記憶がありません</p>;
    }

    return (
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {memories.slice(0, limit).map((memory, idx) => (
          <div
            key={idx}
            style={{
              padding: '12px',
              marginBottom: '8px',
              background: '#f9f9f9',
              borderLeft: `4px solid ${
                memory.importance >= 0.8
                  ? '#ff6b6b'
                  : memory.importance >= 0.5
                  ? '#ffd93d'
                  : '#95e1d3'
              }`,
              borderRadius: '4px',
              fontSize: '14px'
            }}
          >
            <div style={{ marginBottom: '4px' }}>
              <strong>{memory.type}</strong>
              <span
                style={{
                  marginLeft: '8px',
                  fontSize: '12px',
                  color: '#666',
                  background: '#e8e8e8',
                  padding: '2px 8px',
                  borderRadius: '3px'
                }}
              >
                重要度: {(memory.importance * 100).toFixed(0)}%
              </span>
            </div>
            <p style={{ margin: '0 0 4px 0', color: '#333' }}>
              {memory.content.substring(0, 100)}
              {memory.content.length > 100 ? '...' : ''}
            </p>
            <div style={{ fontSize: '12px', color: '#999' }}>
              {new Date(memory.added_at).toLocaleDateString('ja-JP')}
            </div>
          </div>
        ))}
        {memories.length > limit && (
          <div style={{ textAlign: 'center', color: '#999', fontSize: '12px', marginTop: '12px' }}>
            他 {memories.length - limit} 件
          </div>
        )}
      </div>
    );
  };

  if (!profileData) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        {loading ? '読み込み中...' : 'プロファイルを読み込んでください'}
      </div>
    );
  }

  const { profile = {} } = profileData;

  return (
    <div style={{ padding: '16px', background: '#fff', borderRadius: '8px' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '20px', color: '#333' }}>
        プロファイル & 記憶管理
      </h2>

      {/* 現在の状態 */}
      {renderSection(
        'current-state',
        '📊 現在の状態',
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>気分</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4CAF50' }}>
                {profile.current_mood || 5}/10
              </div>
              <div
                style={{
                  width: '100%',
                  height: '4px',
                  background: '#e0e0e0',
                  borderRadius: '2px',
                  marginTop: '8px',
                  overflow: 'hidden'
                }}
              >
                <div
                  style={{
                    width: `${((profile.current_mood || 5) / 10) * 100}%`,
                    height: '100%',
                    background: '#4CAF50'
                  }}
                />
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>エネルギー</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2196F3' }}>
                {profile.current_energy || 5}/10
              </div>
              <div
                style={{
                  width: '100%',
                  height: '4px',
                  background: '#e0e0e0',
                  borderRadius: '2px',
                  marginTop: '8px',
                  overflow: 'hidden'
                }}
              >
                <div
                  style={{
                    width: `${((profile.current_energy || 5) / 10) * 100}%`,
                    height: '100%',
                    background: '#2196F3'
                  }}
                />
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>不安度</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f44336' }}>
                {profile.current_anxiety || 5}/10
              </div>
              <div
                style={{
                  width: '100%',
                  height: '4px',
                  background: '#e0e0e0',
                  borderRadius: '2px',
                  marginTop: '8px',
                  overflow: 'hidden'
                }}
              >
                <div
                  style={{
                    width: `${((profile.current_anxiety || 5) / 10) * 100}%`,
                    height: '100%',
                    background: '#f44336'
                  }}
                />
              </div>
            </div>
          </div>
          <div style={{ marginTop: '16px', fontSize: '12px', color: '#999' }}>
            {profile.last_session_date &&
              `最終セッション: ${new Date(profile.last_session_date).toLocaleDateString('ja-JP')}`}
          </div>
        </div>
      )}

      {/* 基本情報 */}
      {renderSection(
        'basic-info',
        '👤 基本情報',
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          {profile.name && (
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>名前</div>
              <div style={{ fontSize: '14px', fontWeight: 500 }}>{profile.name}</div>
            </div>
          )}
          {profile.age && (
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>年齢</div>
              <div style={{ fontSize: '14px', fontWeight: 500 }}>{profile.age}</div>
            </div>
          )}
          {profile.job && (
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>職業</div>
              <div style={{ fontSize: '14px', fontWeight: 500 }}>{profile.job}</div>
            </div>
          )}
          {profile.location && (
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>住所</div>
              <div style={{ fontSize: '14px', fontWeight: 500 }}>{profile.location}</div>
            </div>
          )}
          {profile.hobbies && profile.hobbies.length > 0 && (
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>趣味</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
                {profile.hobbies.map((hobby: string, idx: number) => (
                  <span
                    key={idx}
                    style={{
                      background: '#e3f2fd',
                      color: '#1976d2',
                      padding: '4px 12px',
                      borderRadius: '16px',
                      fontSize: '12px'
                    }}
                  >
                    {hobby}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* メンタルヘルス情報 */}
      {renderSection(
        'mental-health',
        '🧠 メンタルヘルス情報',
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
          {profile.concerns && (
            <div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>悩み・不安</div>
              <div style={{ fontSize: '14px', background: '#fff3e0', padding: '8px', borderRadius: '4px' }}>
                {profile.concerns}
              </div>
            </div>
          )}
          {profile.goals && (
            <div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>目標</div>
              <div style={{ fontSize: '14px', background: '#e8f5e9', padding: '8px', borderRadius: '4px' }}>
                {profile.goals}
              </div>
            </div>
          )}
          {profile.symptoms && (
            <div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>症状</div>
              <div style={{ fontSize: '14px', background: '#fce4ec', padding: '8px', borderRadius: '4px' }}>
                {profile.symptoms}
              </div>
            </div>
          )}
          {profile.coping_methods && (
            <div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>対処法</div>
              <div style={{ fontSize: '14px', background: '#f3e5f5', padding: '8px', borderRadius: '4px' }}>
                {profile.coping_methods}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 重要な記憶（重要度0.8以上） */}
      {renderSection(
        'critical-memories',
        `🔴 重要な記憶 (${profile.critical_memories?.length || 0})`,
        renderMemoryList(profile.critical_memories || [], 5)
      )}

      {/* 一般的な記憶（重要度0.5-0.8） */}
      {renderSection(
        'important-memories',
        `🟡 通常の記憶 (${profile.important_memories?.length || 0})`,
        renderMemoryList(profile.important_memories || [], 10)
      )}

      {/* その他の記憶（重要度0.15-0.5） */}
      {renderSection(
        'regular-memories',
        `🟢 補足的な記憶 (${profile.regular_memories?.length || 0})`,
        renderMemoryList(profile.regular_memories || [], 15)
      )}
    </div>
  );
};
