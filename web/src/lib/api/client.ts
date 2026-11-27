import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

export const api = createClient<paths>({ baseUrl: "" });

export type Schemas = components["schemas"];
export type Me = Schemas["Me"];
export type UserChoice = Schemas["UserChoice"];
export type UserRole = Schemas["UserRole"];
export type TeamSummary = Schemas["TeamSummary"];
export type TeamDetail = Schemas["TeamDetail"];
export type TodoOwner = Schemas["TodoOwner"];
export type MeetingState = Schemas["MeetingState"];
export type Scorecard = Schemas["Scorecard"];
export type MeasurableRow = Schemas["MeasurableRow"];
export type ScoreCell = Schemas["ScoreCell"];
export type Goal = Schemas["Goal"];
export type Issue = Schemas["IssueOut"];
export type Todo = Schemas["TodoOut"];
export type Completion = Schemas["Completion"];
export type Rock = Schemas["RockOut"];
