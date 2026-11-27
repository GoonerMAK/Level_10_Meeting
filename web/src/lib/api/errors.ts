export type FieldError = { field: string; message: string };

const UNREACHABLE_MESSAGE = "Can't reach the server. Check that it is running and try again.";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: FieldError[];

  constructor({ status, code, message, fields }: { status: number; code: string; message: string; fields: FieldError[] }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;

const isFieldError = (value: unknown): value is FieldError =>
  isRecord(value) && typeof value.field === "string" && typeof value.message === "string";

export function toApiError(status: number, body: unknown): ApiError {
  const error = isRecord(body) && isRecord(body.error) ? body.error : null;
  const fields = error && Array.isArray(error.fields) ? error.fields.filter(isFieldError) : [];
  return new ApiError({
    status,
    code: error && typeof error.code === "string" ? error.code : "unknown_error",
    message: error && typeof error.message === "string" ? error.message : `The server answered with status ${status}`,
    fields,
  });
}

export const isApiError = (error: unknown, status?: number): error is ApiError =>
  error instanceof ApiError && (status === undefined || error.status === status);

export const errorMessage = (error: unknown): string => (error instanceof ApiError ? error.message : UNREACHABLE_MESSAGE);

type ApiResult<Data> = { data?: Data; error?: unknown; response: Response };

export async function readData<Data>(request: Promise<ApiResult<Data>>): Promise<Data> {
  const { data, error, response } = await request;
  if (!response.ok || data === undefined) {
    throw toApiError(response.status, error);
  }
  return data;
}

export async function ensureOk(request: Promise<ApiResult<unknown>>): Promise<void> {
  const { error, response } = await request;
  if (!response.ok) {
    throw toApiError(response.status, error);
  }
}
