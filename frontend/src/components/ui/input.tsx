import React from 'react';

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>((props, ref) => (
  <input ref={ref} {...props} style={{ padding: '0.5em', borderRadius: 4, border: '1px solid #ccc', width: '100%' }} />
));
Input.displayName = 'Input'; 