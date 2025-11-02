import { Settings } from "lucide-react";

export function OutlineToggle({ showOutline, setShowOutline }) {
  if (showOutline) return null;

  return (
    <button
      onClick={() => setShowOutline(true)}
      className="fixed left-4 top-24 bg-white border border-gray-300 rounded-md p-2 shadow-sm hover:shadow-md"
    >
      <Settings size={16} />
    </button>
  );
}
