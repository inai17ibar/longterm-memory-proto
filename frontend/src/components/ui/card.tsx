import React from 'react';

export const Card: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={className} style={{ background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px #eee', padding: 16 }}>{children}</div>
);
export const CardHeader: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={className} style={{ borderBottom: '1px solid #eee', marginBottom: 8 }}>{children}</div>
);
export const CardTitle: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <h2 className={className} style={{ fontWeight: 'bold', fontSize: 18 }}>{children}</h2>
);
export const CardContent: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={className}>{children}</div>
); 