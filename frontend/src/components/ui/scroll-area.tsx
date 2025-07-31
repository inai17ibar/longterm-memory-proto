import React from 'react';

export const ScrollArea: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={className} style={{ overflowY: 'auto', maxHeight: 500 }}>{children}</div>
); 