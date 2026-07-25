import { type InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, ...props }, ref) => {
    const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div>
        <label htmlFor={inputId} className="block text-sm font-medium text-surface-200 mb-1.5">
          {label}
        </label>
        <input ref={ref} id={inputId} className="input-field" {...props} />
        {error && <p className="field-error">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
