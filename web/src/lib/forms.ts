import type { FieldValues, Path, UseFormReturn } from "react-hook-form";

import { errorMessage, isApiError } from "./api/errors";

export type ServerErrors<Field extends string> = {
  fieldErrors: [Field, string][];
  formError: string | null;
};

export function splitServerErrors<Field extends string>(
  error: unknown,
  fieldMap: Partial<Record<string, Field>>,
): ServerErrors<Field> {
  const fieldErrors: [Field, string][] = [];
  const unmatched: string[] = [];
  for (const { field, message } of isApiError(error) ? error.fields : []) {
    const formField = fieldMap[field];
    if (formField) {
      fieldErrors.push([formField, message]);
    } else {
      unmatched.push(message);
    }
  }
  const formError = fieldErrors.length > 0 && unmatched.length === 0 ? null : errorMessage(error);
  return { fieldErrors, formError };
}

export function showServerErrors<Values extends FieldValues>(
  form: UseFormReturn<Values>,
  error: unknown,
  fieldMap: Partial<Record<string, Path<Values>>>,
): void {
  const { fieldErrors, formError } = splitServerErrors(error, fieldMap);
  for (const [field, message] of fieldErrors) {
    form.setError(field, { type: "server", message });
  }
  if (formError) {
    form.setError("root.server", { type: "server", message: formError });
  }
}
