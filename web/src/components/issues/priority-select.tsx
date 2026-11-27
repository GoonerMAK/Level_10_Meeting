import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { NO_PRIORITY, PRIORITIES, priorityChoiceSchema, type PriorityChoice } from "@/lib/validation";

const PRIORITY_LABELS: Record<PriorityChoice, string> = {
  [NO_PRIORITY]: "No priority",
  "5": "5 · highest",
  "4": "4",
  "3": "3",
  "2": "2",
  "1": "1 · lowest",
};

const CHOICES: PriorityChoice[] = [...PRIORITIES, NO_PRIORITY];

type PrioritySelectProps = {
  id?: string;
  value: PriorityChoice;
  onChange: (value: PriorityChoice) => void;
  disabled?: boolean;
  invalid?: boolean;
};

export function PrioritySelect({ id, value, onChange, disabled, invalid }: PrioritySelectProps) {
  return (
    <Select
      value={value}
      onValueChange={(next) => onChange(priorityChoiceSchema.parse(next))}
      disabled={disabled}
    >
      <SelectTrigger id={id} aria-invalid={invalid} className="w-40">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {CHOICES.map((choice) => (
          <SelectItem key={choice} value={choice}>
            {PRIORITY_LABELS[choice]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
