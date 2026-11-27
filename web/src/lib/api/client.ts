import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

export const api = createClient<paths>({ baseUrl: "" });

export type Schemas = components["schemas"];
export type Me = Schemas["Me"];
export type UserChoice = Schemas["UserChoice"];
export type UserRole = Schemas["UserRole"];
export type TeamSummary = Schemas["TeamSummary"];
export type TeamDetail = Schemas["TeamDetail"];
export type MeetingState = Schemas["MeetingState"];
