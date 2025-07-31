import React from 'react';

export const Badge: React.FC<{ children: React.ReactNode; className?: string; variant?: string }> = ({ children, className }) => (
  <span className={`inline-block px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 ${className || ''}`}>{children}</span>
); 