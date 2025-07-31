import React from 'react';

export const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ children, ...props }) => (
  <button {...props} style={{ padding: '0.5em 1em', borderRadius: 4, border: '1px solid #ccc', background: '#f5f5f5', cursor: 'pointer' }}>
    {children}
  </button>
); 