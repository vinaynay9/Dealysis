"use client";
import { useState } from "react";
import { useMemoEditor } from "@/hooks/useMemoEditor";
import { useChatAssistant } from "@/hooks/useChatAssistant";
import { useBibliography } from "@/hooks/useBibliography";
import { useExport } from "@/hooks/useExport";
import { EditorHeader } from "@/components/MemoEditor/EditorHeader";
import { OutlineSidebar } from "@/components/MemoEditor/OutlineSidebar";
import { ChatAssistant } from "@/components/MemoEditor/ChatAssistant";
import { MemoPreview } from "@/components/MemoEditor/MemoPreview";
import { MemoEditor } from "@/components/MemoEditor/MemoEditor";
import { MediaButtons } from "@/components/MemoEditor/MediaButtons";
import { LoadingState } from "@/components/MemoEditor/LoadingState";
import { OutlineToggle } from "@/components/MemoEditor/OutlineToggle";
import { MediaUploadModal } from "@/components/MemoEditor/MediaUploadModal";
import { CitationModal } from "@/components/MemoEditor/CitationModal";

export default function MemoEditorPage() {
  const {
    memoData,
    currentContent,
    setCurrentContent,
    activeTab,
    setActiveTab,
    pageWidth,
    setPageWidth,
    showOutline,
    setShowOutline,
    sections,
    uploadedMedia,
    getPageWidthClass,
    scrollToSection,
    handleMediaUpload,
  } = useMemoEditor();

  const {
    showChat,
    setShowChat,
    chatMessage,
    setChatMessage,
    chatHistory,
    isChatProcessing,
    streamingResponse,
    sendChatMessage,
  } = useChatAssistant(currentContent, setCurrentContent);

  const {
    bibliography,
    showCitationModal,
    setShowCitationModal,
    insertCitation,
    addBibliographySection,
  } = useBibliography(memoData, currentContent, setCurrentContent);

  const {
    showExportDropdown,
    setShowExportDropdown,
    exportToPDF,
    exportToWord,
    copyShareLink,
  } = useExport(currentContent);

  const [showMediaModal, setShowMediaModal] = useState(false);
  const [currentSectionId, setCurrentSectionId] = useState(null);

  const openMediaModal = (sectionId) => {
    setCurrentSectionId(sectionId);
    setShowMediaModal(true);
  };

  if (!memoData) {
    return <LoadingState />;
  }

  return (
    <div
      className="min-h-screen bg-gray-50"
      style={{ fontFamily: "Inter, sans-serif" }}
    >
      <EditorHeader
        memoData={memoData}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        pageWidth={pageWidth}
        setPageWidth={setPageWidth}
        showExportDropdown={showExportDropdown}
        setShowExportDropdown={setShowExportDropdown}
        exportToPDF={exportToPDF}
        exportToWord={exportToWord}
        copyShareLink={copyShareLink}
        setShowCitationModal={setShowCitationModal}
        addBibliographySection={addBibliographySection}
        showChat={showChat}
        setShowChat={setShowChat}
      />

      {/* Click outside to close dropdown */}
      {showExportDropdown && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => setShowExportDropdown(false)}
        ></div>
      )}

      <div className="flex">
        <OutlineSidebar
          showOutline={showOutline}
          setShowOutline={setShowOutline}
          sections={sections}
          scrollToSection={scrollToSection}
          uploadedMedia={uploadedMedia}
        />

        {/* Main Content */}
        <main className={`flex-1 ${showChat ? "mr-80" : ""}`}>
          <div className={`mx-auto ${getPageWidthClass()} py-8 px-6`}>
            {activeTab === "preview" ? (
              <MemoPreview content={streamingResponse || currentContent} />
            ) : (
              <MemoEditor
                content={currentContent}
                setContent={setCurrentContent}
              />
            )}

            {/* Add Media Buttons for sections */}
            {activeTab === "preview" && (
              <MediaButtons openMediaModal={openMediaModal} />
            )}
          </div>
        </main>

        <ChatAssistant
          showChat={showChat}
          chatHistory={chatHistory}
          isChatProcessing={isChatProcessing}
          chatMessage={chatMessage}
          setChatMessage={setChatMessage}
          sendChatMessage={sendChatMessage}
        />
      </div>

      <OutlineToggle
        showOutline={showOutline}
        setShowOutline={setShowOutline}
      />

      {/* Media Upload Modal */}
      <MediaUploadModal
        isOpen={showMediaModal}
        onClose={() => setShowMediaModal(false)}
        onUpload={handleMediaUpload}
        sectionId={currentSectionId}
      />

      {/* Citation Modal */}
      <CitationModal
        isOpen={showCitationModal}
        onClose={() => setShowCitationModal(false)}
        bibliography={bibliography}
        onInsertCitation={insertCitation}
      />
    </div>
  );
}
