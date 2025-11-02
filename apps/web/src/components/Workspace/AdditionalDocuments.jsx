import { Plus } from "lucide-react";

export function AdditionalDocuments({
  onFileUpload,
  onRegenerate,
  isProcessing,
}) {
  return (
    <div className="bg-[#1A1B23] rounded-2xl p-6 border border-[#374151]">
      <h3
        className="text-lg font-semibold text-white mb-4"
        style={{ fontFamily: "Inter, sans-serif" }}
      >
        Add More Documents
      </h3>
      <div
        className="border-2 border-dashed border-[#4B5563] rounded-xl p-4 text-center hover:border-[#6366F1] transition-colors cursor-pointer"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          onFileUpload(e.dataTransfer.files);
        }}
        onClick={() => document.getElementById("additional-upload").click()}
      >
        <Plus size={24} className="text-[#6366F1] mx-auto mb-2" />
        <p
          className="text-sm text-[#9CA3AF]"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          Add more documents
        </p>
      </div>
      <input
        id="additional-upload"
        type="file"
        multiple
        accept=".pdf,.docx,.txt"
        className="hidden"
        onChange={(e) => onFileUpload(e.target.files)}
      />

      <button
        onClick={onRegenerate}
        disabled={isProcessing}
        className="w-full mt-4 px-4 py-2 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white font-medium rounded-lg hover:from-[#5B61F0] hover:to-[#7C3AED] transition-colors disabled:opacity-50"
        style={{ fontFamily: "Inter, sans-serif" }}
      >
        Regenerate Memo
      </button>
    </div>
  );
}
