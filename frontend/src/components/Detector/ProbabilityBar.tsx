import { percent } from './utils';

interface ProbabilityBarProps {
  label: string;
  value: number;
  active: boolean;
  activeClassName: string;
  inactiveClassName: string;
}

export function ProbabilityBar({ label, value, active, activeClassName, inactiveClassName }: ProbabilityBarProps) {
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-600 mb-1 font-medium">
        <span>{label}</span>
        <span className="font-bold">{percent(value)}</span>
      </div>
      <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${active ? activeClassName : inactiveClassName}`}
          style={{ width: percent(value) }}
        />
      </div>
    </div>
  );
}
