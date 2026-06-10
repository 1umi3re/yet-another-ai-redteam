import clsx from "clsx";
import {
  InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes,
  createContext, forwardRef, useContext, useId, ReactNode,
} from "react";

type FieldContextValue = {
  id: string;
  describedBy?: string;
  invalid?: boolean;
  required?: boolean;
};

const FieldContext = createContext<FieldContextValue | undefined>(undefined);

function describedBy(explicit: string | undefined, field: FieldContextValue | undefined) {
  return [explicit, field?.describedBy].filter(Boolean).join(" ") || undefined;
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, id, required, "aria-describedby": ariaDescribedBy, "aria-invalid": ariaInvalid, ...rest }, ref) {
    const field = useContext(FieldContext);
    return (
      <input
        ref={ref}
        id={id ?? field?.id}
        required={required ?? field?.required}
        aria-describedby={describedBy(ariaDescribedBy, field)}
        aria-invalid={ariaInvalid ?? (field?.invalid || undefined)}
        className={clsx("input", className)}
        {...rest}
      />
    );
  }
);

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, id, children, required, "aria-describedby": ariaDescribedBy, "aria-invalid": ariaInvalid, ...rest }, ref) {
    const field = useContext(FieldContext);
    return (
      <select
        ref={ref}
        id={id ?? field?.id}
        required={required ?? field?.required}
        aria-describedby={describedBy(ariaDescribedBy, field)}
        aria-invalid={ariaInvalid ?? (field?.invalid || undefined)}
        className={clsx("input", className)}
        {...rest}
      >
        {children}
      </select>
    );
  }
);

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, id, required, "aria-describedby": ariaDescribedBy, "aria-invalid": ariaInvalid, ...rest }, ref) {
    const field = useContext(FieldContext);
    return (
      <textarea
        ref={ref}
        id={id ?? field?.id}
        required={required ?? field?.required}
        aria-describedby={describedBy(ariaDescribedBy, field)}
        aria-invalid={ariaInvalid ?? (field?.invalid || undefined)}
        className={clsx("input font-mono", className)}
        {...rest}
      />
    );
  }
);

export function Field({
  label,
  hint,
  error,
  required,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: ReactNode;
}) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedByIds = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
        {required && <span className="ml-1 text-red-500" aria-hidden="true">*</span>}
      </label>
      <FieldContext.Provider value={{ id, describedBy: describedByIds, invalid: !!error, required }}>
        {children}
      </FieldContext.Provider>
      {hint && <p id={hintId} className="mt-1 text-xs text-gray-500">{hint}</p>}
      {error && <p id={errorId} role="alert" className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
