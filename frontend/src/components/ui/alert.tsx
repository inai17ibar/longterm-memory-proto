import React from 'react';

export const Alert: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={className} style={{ border: '1px solid #fbb', background: '#fee', borderRadius: 4, padding: 8 }}>{children}</div>
);
export const AlertDescription: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={className}>{children}</div>
); 