import { User, Bot, Send } from "lucide-react";

export function ChatInterface({
  chatHistory,
  chatMessage,
  onMessageChange,
  onSendMessage,
  isChatProcessing,
}) {
  return (
    <div className="bg-[#1A1B23] rounded-2xl p-6 border border-[#374151]">
      <h3
        className="text-lg font-semibold text-white mb-4"
        style={{ fontFamily: "Inter, sans-serif" }}
      >
        AI Chat Editor
      </h3>

      <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
        {chatHistory.map((message, index) => (
          <div
            key={index}
            className={`flex items-start space-x-2 ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`flex items-start space-x-2 max-w-xs ${message.role === "user" ? "flex-row-reverse space-x-reverse" : ""}`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center ${message.role === "user" ? "bg-[#6366F1]" : "bg-[#8B5CF6]"}`}
              >
                {message.role === "user" ? (
                  <User size={12} className="text-white" />
                ) : (
                  <Bot size={12} className="text-white" />
                )}
              </div>
              <div
                className={`p-3 rounded-lg ${message.role === "user" ? "bg-[#6366F1] text-white" : "bg-[#374151] text-[#D4D4D8]"}`}
              >
                <p
                  className="text-sm"
                  style={{ fontFamily: "Inter, sans-serif" }}
                >
                  {message.content}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex space-x-2">
        <input
          type="text"
          value={chatMessage}
          onChange={(e) => onMessageChange(e.target.value)}
          onKeyPress={(e) =>
            e.key === "Enter" && !isChatProcessing && onSendMessage()
          }
          placeholder="Ask AI to edit the memo..."
          className="flex-1 px-3 py-2 bg-[#374151] border border-[#4B5563] rounded-lg text-white placeholder-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-[#6366F1]"
          style={{ fontFamily: "Inter, sans-serif" }}
          disabled={isChatProcessing}
        />
        <button
          onClick={onSendMessage}
          disabled={!chatMessage.trim() || isChatProcessing}
          className="px-3 py-2 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white rounded-lg hover:from-[#5B61F0] hover:to-[#7C3AED] transition-colors disabled:opacity-50"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
