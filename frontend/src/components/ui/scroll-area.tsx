import React from "react";

export const ScrollArea: React.FC<{
  className?: string;
  children: React.ReactNode;
}> = ({ className, children }) => (
  <div
    className={`overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 ${
      className || ""
    }`}
  >
    {children}
  </div>
);
