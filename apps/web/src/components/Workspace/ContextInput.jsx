export function ContextInput({ value, onChange }) {
  return (
    <div className="bg-[#1A1B23] rounded-2xl p-6 border border-[#374151] mb-8">
      <h3
        className="text-lg font-semibold text-white mb-4"
        style={{ fontFamily: "Inter, sans-serif" }}
      >
        Additional Context (Optional)
      </h3>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Company name, sector, stage, or any specific details to guide the memo..."
        className="w-full p-4 border border-[#374151] rounded-xl bg-[#374151] text-white placeholder-[#9CA3AF] resize-none focus:outline-none focus:ring-2 focus:ring-[#6366F1]"
        rows="3"
        style={{ fontFamily: "Inter, sans-serif" }}
      />
    </div>
  );
}
