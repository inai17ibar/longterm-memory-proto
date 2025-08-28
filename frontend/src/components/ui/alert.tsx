import React from 'react';

export const Alert: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={`border border-red-200 bg-red-50 rounded-xl p-4 ${className || ''}`}>{children}</div>
);
export const AlertDescription: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={`text-red-700 text-sm ${className || ''}`}>{children}</div>
); 