export function ChatAssistant({
  showChat,
  chatHistory,
  isChatProcessing,
  chatMessage,
  setChatMessage,
  sendChatMessage,
}) {
  if (!showChat) return null;

  return (
    <aside className="w-80 bg-white border-l border-gray-200 h-screen fixed right-0 top-16 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="font-semibold text-gray-800">AI Editing Assistant</h2>
        <p className="text-sm text-gray-600 mt-1">
          Ask me to edit specific sections or content
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatHistory.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xs p-3 rounded-lg ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              <p className="text-sm">{message.content}</p>
            </div>
          </div>
        ))}

        {isChatProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-100 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"
                  style={{ animationDelay: "0.2s" }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"
                  style={{ animationDelay: "0.4s" }}
                ></div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && sendChatMessage()}
            placeholder="Edit the executive summary..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isChatProcessing}
          />
          <button
            onClick={sendChatMessage}
            disabled={!chatMessage.trim() || isChatProcessing}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>

        <div className="mt-3 text-xs text-gray-500">
          <p>
            <strong>Examples:</strong>
          </p>
          <ul className="space-y-1 mt-1">
            <li>• "Add more detail about market size"</li>
            <li>• "Emphasize team risks in the final section"</li>
            <li>• "Summarize competitive landscape in bullet points"</li>
          </ul>
        </div>
      </div>
    </aside>
  );
}
