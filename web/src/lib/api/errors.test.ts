import { describe, expect, it } from "vitest";

import { ApiError, errorMessage, readData, toApiError } from "./errors";

describe("toApiError", () => {
  it("reads the server's error envelope with its field errors", () => {
    const error = toApiError(422, {
      error: {
        code: "invalid_input",
        message: "Some fields are invalid",
        fields: [{ field: "title", message: "Title is required" }, { field: 3 }],
      },
    });

    expect(error).toMatchObject({ status: 422, code: "invalid_input", message: "Some fields are invalid" });
    expect(error.fields).toEqual([{ field: "title", message: "Title is required" }]);
  });

  it("falls back to a readable message when the body is not the envelope", () => {
    const error = toApiError(502, "<html>Bad gateway</html>");

    expect(error).toMatchObject({ status: 502, code: "unknown_error", fields: [] });
    expect(error.message).toBe("The server answered with status 502");
  });
});

describe("readData", () => {
  it("throws the parsed error for a failed response", async () => {
    const response = new Response(null, { status: 404 });
    const request = Promise.resolve({ error: { error: { code: "not_found", message: "Team not found" } }, response });

    await expect(readData(request)).rejects.toMatchObject({ status: 404, message: "Team not found" });
  });
});

describe("errorMessage", () => {
  it("uses the server's message for API errors and a connection hint otherwise", () => {
    const apiError = new ApiError({ status: 403, code: "forbidden", message: "Observers cannot change anything", fields: [] });

    expect(errorMessage(apiError)).toBe("Observers cannot change anything");
    expect(errorMessage(new TypeError("Failed to fetch"))).toMatch(/Can't reach the server/);
  });
});
