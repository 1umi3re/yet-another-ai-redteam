import clsx from "clsx";
import { ReactNode } from "react";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("card", className)}>{children}</div>;
}
export function CardHeader({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("px-5 pt-5 pb-3 border-b border-gray-100", className)}>{children}</div>;
}
export function CardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("p-5", className)}>{children}</div>;
}
export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 className={clsx("text-sm font-semibold text-gray-900", className)}>{children}</h2>;
}
export function CardDescription({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={clsx("text-xs text-gray-500 mt-0.5", className)}>{children}</p>;
}
