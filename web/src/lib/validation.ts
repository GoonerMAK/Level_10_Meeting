import { z } from "zod";

export const titleSchema = z
  .string()
  .trim()
  .min(1, "Title is required")
  .max(200, "Title must be 200 characters or fewer");

export const noteSchema = z
  .string()
  .trim()
  .min(1, "A note is required to solve an Issue")
  .max(2000, "Note must be 2000 characters or fewer");

export const scoreValueSchema = z
  .string()
  .trim()
  .regex(/^-?\d{1,11}(\.\d{1,4})?$/, "Enter a number with up to 4 decimals");

export const NO_PRIORITY = "none";
export const PRIORITIES = ["5", "4", "3", "2", "1"] as const;
export const priorityChoiceSchema = z.enum([NO_PRIORITY, ...PRIORITIES]);
export type PriorityChoice = z.infer<typeof priorityChoiceSchema>;

export const toPriority = (choice: PriorityChoice): number | null => (choice === NO_PRIORITY ? null : Number(choice));

export const toPriorityChoice = (priority: number | null): PriorityChoice =>
  priorityChoiceSchema.catch(NO_PRIORITY).parse(priority === null ? NO_PRIORITY : String(priority));
