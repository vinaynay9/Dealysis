import { MemoDisplay } from "./MemoDisplay";
import { AdditionalDocuments } from "./AdditionalDocuments";
import { ChatInterface } from "./ChatInterface";
import { ActionsPanel } from "./ActionsPanel";

export function ResultsSection({
  generatedMemo,
  streamingMemo,
  showResults,
  showChat,
  chatHistory,
  chatMessage,
  isChatProcessing,
  isProcessing,
  onToggleChat,
  onCopyMemo,
  onDownloadMemo,
  onFileUpload,
  onRegenerate,
  onChatMessageChange,
  onSendChatMessage,
  onStartOver,
}) {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2">
        <MemoDisplay
          generatedMemo={generatedMemo}
          streamingMemo={streamingMemo}
          showResults={showResults}
          showChat={showChat}
          onToggleChat={onToggleChat}
          onCopy={onCopyMemo}
          onDownload={onDownloadMemo}
        />
      </div>

      <div className="space-y-6">
        {showResults && (
          <>
            <AdditionalDocuments
              onFileUpload={onFileUpload}
              onRegenerate={onRegenerate}
              isProcessing={isProcessing}
            />

            {showChat && (
              <ChatInterface
                chatHistory={chatHistory}
                chatMessage={chatMessage}
                onMessageChange={onChatMessageChange}
                onSendMessage={onSendChatMessage}
                isChatProcessing={isChatProcessing}
              />
            )}

            <ActionsPanel onStartOver={onStartOver} />
          </>
        )}
      </div>
    </section>
  );
}
