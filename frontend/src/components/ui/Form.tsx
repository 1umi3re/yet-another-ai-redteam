import clsx from "clsx";
import {
  InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes,
  createContext, forwardRef, useContext, useId, ReactNode,
} from "react";

const FieldIdContext = createContext<string | undefined>(undefined);

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, id, ...rest }, ref) {
    const ctxId = useContext(FieldIdContext);
    return <input ref={ref} id={id ?? ctxId} className={clsx("input", className)} {...rest} />;
  }
);

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, id, children, ...rest }, ref) {
    const ctxId = useContext(FieldIdContext);
    return <select ref={ref} id={id ?? ctxId} className={clsx("input", className)} {...rest}>{children}</select>;
  }
);

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, id, ...rest }, ref) {
    const ctxId = useContext(FieldIdContext);
    return <textarea ref={ref} id={id ?? ctxId} className={clsx("input font-mono", className)} {...rest} />;
  }
);

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  const id = useId();
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      <FieldIdContext.Provider value={id}>{children}</FieldIdContext.Provider>
      {hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
    </div>
  );
}
