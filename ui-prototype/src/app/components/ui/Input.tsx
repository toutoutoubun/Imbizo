import { InputHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-[12px] text-secondary-text">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            'px-3 py-2 bg-input-background border border-input rounded-sm',
            'text-[14px] text-foreground',
            'focus:outline focus:outline-2 focus:outline-primary focus:border-transparent',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'transition-colors duration-100',
            error && 'border-destructive',
            className
          )}
          {...props}
        />
        {error && (
          <span className="text-[12px] text-destructive">{error}</span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
