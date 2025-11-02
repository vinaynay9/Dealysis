import { Brain } from "lucide-react";

export function Header() {
  return (
    <header className="bg-[#1A1B23] border-b border-[#374151] px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <img
            src="https://ucarecdn.com/a197b497-5194-4168-87d3-5bc3a0bdc81a/-/format/auto/"
            alt="Dealysis Logo"
            className="w-8 h-8"
            onError={(e) => {
              e.target.style.display = "none";
              e.target.nextSibling.style.display = "flex";
            }}
          />
          <div
            className="w-8 h-8 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-lg flex items-center justify-center"
            style={{ display: "none" }}
          >
            <Brain size={18} className="text-white" />
          </div>
          <h1
            className="text-xl font-semibold text-white"
            style={{ fontFamily: "Inter, sans-serif" }}
          >
            Dealysis
          </h1>
        </div>
        <p
          className="text-sm text-[#9CA3AF]"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          AI-Powered VC Deal Memo Generator
        </p>
      </div>
    </header>
  );
}
