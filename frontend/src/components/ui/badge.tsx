import React from 'react';

export const Badge: React.FC<{ children: React.ReactNode; className?: string; variant?: string }> = ({ children, className }) => (
  <span className={`inline-block px-2 py-1 text-xs rounded bg-gray-200 ${className || ''}`}>{children}</span>
); 