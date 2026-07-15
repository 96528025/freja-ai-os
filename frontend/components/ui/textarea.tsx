import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn("min-h-28 w-full resize-none rounded-md border border-black/10 bg-white p-4 text-base outline-none transition focus:border-coral focus:ring-2 focus:ring-coral/15 placeholder:text-black/35", className)}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";

