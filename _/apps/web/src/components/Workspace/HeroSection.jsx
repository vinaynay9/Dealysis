import { Upload, Brain, FileText } from "lucide-react";

export function HeroSection() {
  return (
    <section className="mb-12">
      <div className="bg-[#1A1B23] rounded-3xl p-8 md:p-12 border border-[#374151]">
        <div className="text-center mb-8">
          <h2
            className="text-3xl md:text-5xl text-white mb-4"
            style={{ fontFamily: "Instrument Serif, serif" }}
          >
            Transform Due Diligence into <em>Professional</em> Investment Memos
          </h2>
          <p
            className="text-lg text-[#D4D4D8] max-w-3xl mx-auto"
            style={{ fontFamily: "Inter, sans-serif" }}
          >
            Upload your pitch decks, notes, and transcripts. Get a structured,
            editable investment memo in minutes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="text-center">
            <div className="w-12 h-12 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Upload size={24} className="text-white" />
            </div>
            <h3
              className="font-semibold text-white mb-2"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              Upload Documents
            </h3>
            <p
              className="text-sm text-[#9CA3AF]"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              Drag & drop pitch decks, transcripts, notes (PDF, DOCX, TXT)
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Brain size={24} className="text-white" />
            </div>
            <h3
              className="font-semibold text-white mb-2"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              AI Analysis
            </h3>
            <p
              className="text-sm text-[#9CA3AF]"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              Extract insights, analyze market, team, traction & risks
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileText size={24} className="text-white" />
            </div>
            <h3
              className="font-semibold text-white mb-2"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              Get Your Memo
            </h3>
            <p
              className="text-sm text-[#9CA3AF]"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              Receive structured, editable memo ready for IC presentation
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
