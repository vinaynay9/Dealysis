import { RotateCcw } from "lucide-react";

export function ActionsPanel({ onStartOver }) {
  return (
    <div className="bg-[#1A1B23] rounded-2xl p-6 border border-[#374151]">
      <h3
        className="text-lg font-semibold text-white mb-4"
        style={{ fontFamily: "Inter, sans-serif" }}
      >
        Actions
      </h3>
      <div className="space-y-3">
        <button
          onClick={onStartOver}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 border border-[#4B5563] text-[#D4D4D8] rounded-lg hover:bg-[#374151] transition-colors"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          <RotateCcw size={16} />
          <span>Start Over</span>
        </button>
      </div>
    </div>
  );
}
