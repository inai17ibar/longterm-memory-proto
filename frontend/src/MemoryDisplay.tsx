import React from 'react';

interface Memory {
  id: string;
  content: string;
  memory_type: string;
  importance_score: number;
  timestamp: string;
  metadata: Record<string, any>;
}

interface MemoryDisplayProps {
  memories: Memory[];
  userInfo: {
    name?: string;
    job?: string;
    hobbies?: string[];
  } | null;
}

const categoryConfig: Record<string, { icon: string, label: string, bgColor: string, borderColor: string, textColor: string }> = {
  'concerns': { icon: '💭', label: '悩み・心配事', bgColor: '#fef2f2', borderColor: '#fecaca', textColor: '#991b1b' },
  'goals': { icon: '🎯', label: '目標・願望', bgColor: '#f0fdf4', borderColor: '#bbf7d0', textColor: '#14532d' },
  'emotional_state': { icon: '💫', label: '感情状態', bgColor: '#fef2f2', borderColor: '#fecaca', textColor: '#dc2626' },
  'symptoms': { icon: '🩺', label: '症状・体調', bgColor: '#fef7ff', borderColor: '#f3e8ff', textColor: '#7c2d92' },
  'triggers': { icon: '⚠️', label: 'ストレス要因', bgColor: '#fff7ed', borderColor: '#fed7aa', textColor: '#c2410c' },
  'coping_methods': { icon: '🛠️', label: '対処法', bgColor: '#f0f9ff', borderColor: '#bae6fd', textColor: '#0c4a6e' },
  'work_status': { icon: '💼', label: '勤務状況', bgColor: '#f8fafc', borderColor: '#e2e8f0', textColor: '#475569' },
  'support_system': { icon: '🤝', label: 'サポート', bgColor: '#f0fdf4', borderColor: '#bbf7d0', textColor: '#14532d' },
  'medication': { icon: '💊', label: '医療情報', bgColor: '#fefce8', borderColor: '#fde047', textColor: '#a16207' },
  'daily_routine': { icon: '📅', label: '生活パターン', bgColor: '#fdf4ff', borderColor: '#e9d5ff', textColor: '#7c3aed' },
  'personality': { icon: '⭐', label: '性格', bgColor: '#fef3c7', borderColor: '#fde68a', textColor: '#92400e' },
  'experiences': { icon: '📚', label: '重要な体験', bgColor: '#ede9fe', borderColor: '#c4b5fd', textColor: '#5b21b6' },
  'family': { icon: '👥', label: '家族・人間関係', bgColor: '#ecfdf5', borderColor: '#a7f3d0', textColor: '#065f46' },
};

export const MemoryDisplay: React.FC<MemoryDisplayProps> = ({ memories, userInfo }) => {
  // 記憶をタイプ別にグループ化
  const memoryByType: Record<string, Memory[]> = {};
  memories.forEach(memory => {
    if (!memoryByType[memory.memory_type]) {
      memoryByType[memory.memory_type] = [];
    }
    memoryByType[memory.memory_type].push(memory);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* 基本情報 */}
      {userInfo && (userInfo.name || userInfo.job || (userInfo.hobbies && userInfo.hobbies.length > 0)) && (
        <div style={{ padding: '12px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#2d3748', marginBottom: '8px' }}>
            👤 基本情報
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
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
        </div>
      )}

      {/* カテゴリ別記憶表示 */}
      {Object.entries(memoryByType).map(([type, typeMemories]) => {
        const config = categoryConfig[type] || {
          icon: '📝',
          label: type,
          bgColor: '#f1f5f9',
          borderColor: '#cbd5e1',
          textColor: '#475569'
        };

        return (
          <div
            key={type}
            style={{
              padding: '12px',
              backgroundColor: config.bgColor,
              borderRadius: '8px',
              border: `1px solid ${config.borderColor}`
            }}
          >
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: config.textColor, marginBottom: '8px' }}>
              {config.icon} {config.label}
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {typeMemories.map((memory) => (
                <div
                  key={memory.id}
                  style={{
                    fontSize: '14px',
                    color: config.textColor,
                    padding: '4px 0',
                    whiteSpace: 'pre-wrap',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start'
                  }}
                >
                  <span>• {memory.content}</span>
                  <span
                    style={{
                      fontSize: '11px',
                      padding: '2px 6px',
                      backgroundColor: 'rgba(0,0,0,0.1)',
                      borderRadius: '4px',
                      marginLeft: '8px',
                      whiteSpace: 'nowrap'
                    }}
                    title={`重要度: ${(memory.importance_score * 100).toFixed(0)}%`}
                  >
                    {(memory.importance_score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};
