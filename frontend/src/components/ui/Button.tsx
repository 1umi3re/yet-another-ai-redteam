import clsx from "clsx";
import { ButtonHTMLAttributes, forwardRef, ReactNode } from "react";
import { Loader2 } from "lucide-react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = "primary", size = "md", loading, icon, className, children, disabled, ...rest }, ref
) {
  const v = {
    primary: "btn-primary", secondary: "btn-secondary", ghost: "btn-ghost", danger: "btn-danger",
  }[variant];
  const s = size === "sm" ? "!px-2.5 !py-1.5 !text-xs" : "";
  return (
    <button ref={ref} className={clsx(v, s, className)} disabled={disabled || loading} {...rest}>
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {children}
    </button>
  );
});
