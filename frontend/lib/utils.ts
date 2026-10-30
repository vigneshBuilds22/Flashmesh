import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const fmt = (n: number) => n.toLocaleString("en-US");
export const usd = (n: number) => (n < 0.01 ? `$${n.toFixed(5)}` : `$${n.toFixed(3)}`);
