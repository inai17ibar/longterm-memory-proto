import React from "react";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, style, ...props }, ref) => (
  <input
    ref={ref}
    className={className}
    style={{
      width: "100%",
      padding: "8px 16px",
      border: "1px solid #d1d5db",
      borderRadius: "9999px",
      outline: "none",
      fontSize: "14px",
      ...style,
    }}
    {...props}
  />
));
Input.displayName = "Input";
