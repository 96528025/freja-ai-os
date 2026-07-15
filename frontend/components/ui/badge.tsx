import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return <span className={cn("inline-flex items-center rounded-full bg-black/[0.05] px-2 py-1 text-xs font-medium text-black/65", className)} {...props} />;
}

