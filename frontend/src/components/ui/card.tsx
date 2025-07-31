import React from 'react';

export const Card: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div 
    className={className} 
    style={{ 
      background: 'white', 
      borderRadius: '16px', 
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
      border: '1px solid #f3f4f6', 
      padding: '24px' 
    }}
  >
    {children}
  </div>
);
export const CardHeader: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div 
    className={className} 
    style={{ 
      borderBottom: '1px solid #f3f4f6', 
      paddingBottom: '12px', 
      marginBottom: '16px' 
    }}
  >
    {children}
  </div>
);
export const CardTitle: React.FC<{ className?: string; style?: React.CSSProperties; children: React.ReactNode }> = ({ className, style, children }) => (
  <h2 
    className={className} 
    style={{ 
      fontWeight: 'bold', 
      fontSize: '18px',
      ...style
    }}
  >
    {children}
  </h2>
);
export const CardContent: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={className}>{children}</div>
); 