"use client";

import { useState, useEffect, useCallback } from "react";
import useUser from "@/utils/useUser";
import { useWorkspace } from "@/hooks/useWorkspace";
import MemosSidebar from "@/components/Workspace/MemosSidebar";
import { Header } from "@/components/Workspace/Header";
import { HeroSection } from "@/components/Workspace/HeroSection";
import { UploadSection } from "@/components/Workspace/UploadSection";
import { ResultsSection } from "@/components/Workspace/ResultsSection";
import { Save } from "lucide-react";

export default function WorkspacePage() {
  const { data: user, loading: userLoading } = useUser();
  const [currentMemo, setCurrentMemo] = useState(null);
  const [workspaceKey, setWorkspaceKey] = useState(0);
  const [sidebarRefresh, setSidebarRefresh] = useState(0);

  // Handle memo saved callback
  const handleMemoSaved = useCallback((savedMemo) => {
    setSidebarRefresh((prev) => prev + 1);
  }, []);

  const {
    referenceFiles,
    exampleFiles,
    referenceSummaries,
    exampleSummaries,
    referenceTexts,
    referenceUrls,
    companyContext,
    setCompanyContext,
    rawTextInput,
    setRawTextInput,
    rawTextLabel,
    setRawTextLabel,
    urlInput,
    setUrlInput,
    urlLabel,
    setUrlLabel,
    activeTab,
    setActiveTab,
    isProcessing,
    generatedMemo,
    setGeneratedMemo,
    streamingMemo,
    processingStage,
    showResults,
    showChat,
    setShowChat,
    chatMessage,
    setChatMessage,
    chatHistory,
    isChatProcessing,
    fileProcessingStatus,
    generationProgress,
    memoSections,
    handleFileUpload,
    removeFile,
    addText,
    addUrl,
    removeText,
    removeUrl,
    generateMemo,
    regenerateMemo,
    sendChatMessage,
    copyToClipboard,
    downloadMemo,
    startOver,
  } = useWorkspace(handleMemoSaved);

  // Redirect to signin if not authenticated
  useEffect(() => {
    if (!userLoading && !user) {
      window.location.href = "/account/signin?callbackUrl=/workspace";
    }
  }, [user, userLoading]);

  const handleMemoSelect = async (memo) => {
    try {
      console.log("Loading memo:", memo.id);
      const response = await fetch(`/api/user-memos/${memo.id}`);
      console.log("Response status:", response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("Response data:", data);

      if (data.success) {
        setCurrentMemo(data.memo);
        setGeneratedMemo(data.memo.content);
        // Clear workspace to show saved memo
        startOver();
      } else {
        console.error("Error loading memo:", data.error);
        alert("Failed to load memo: " + (data.error || "Unknown error"));
      }
    } catch (error) {
      console.error("Error loading memo:", error);
      alert("Failed to load memo: " + error.message);
    }
  };

  const handleNewMemo = () => {
    setCurrentMemo(null);
    startOver();
    setWorkspaceKey((prev) => prev + 1);
  };

  const handleSaveMemo = async () => {
    if (!generatedMemo || !user) return;

    const title = prompt(
      "Enter a title for your memo:",
      currentMemo?.title ||
        `Investment Memo - ${new Date().toLocaleDateString()}`,
    );

    if (!title) return;

    try {
      const memoData = {
        title,
        content: generatedMemo,
        sections: memoSections,
        metadata: {
          generated: new Date().toISOString(),
          totalSections: Object.keys(memoSections).length,
          referenceMaterials:
            referenceSummaries.length +
            referenceTexts.length +
            referenceUrls.length,
        },
        company_name: companyContext
          ? companyContext.split(/\s+/).slice(0, 3).join(" ")
          : null,
      };

      const endpoint = currentMemo
        ? `/api/user-memos/${currentMemo.id}`
        : "/api/user-memos";
      const method = currentMemo ? "PUT" : "POST";

      const response = await fetch(endpoint, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(memoData),
      });

      const data = await response.json();

      if (data.success) {
        if (currentMemo) {
          setCurrentMemo({ ...currentMemo, ...data.memo });
        } else {
          setCurrentMemo(data.memo);
        }
        alert(
          currentMemo
            ? "Memo updated successfully!"
            : "Memo saved successfully!",
        );
      } else {
        throw new Error(data.error || "Failed to save memo");
      }
    } catch (error) {
      console.error("Error saving memo:", error);
      alert("Failed to save memo: " + error.message);
    }
  };

  // Show loading state while checking auth
  if (userLoading) {
    return (
      <div className="min-h-screen bg-[#0A0B0D] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-white">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render anything if not authenticated (will redirect)
  if (!user) {
    return null;
  }

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Instrument+Serif:ital,wght@0,400;1,400&display=swap"
        rel="stylesheet"
      />

      <div className="min-h-screen bg-[#0A0B0D] flex">
        {/* Sidebar */}
        <MemosSidebar
          onMemoSelect={handleMemoSelect}
          onNewMemo={handleNewMemo}
          currentMemoId={currentMemo?.id}
          refreshTrigger={sidebarRefresh}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          <Header />

          <div className="flex-1 overflow-auto">
            <div className="max-w-7xl mx-auto px-6 py-8">
              {/* Save Button - Show when there's a generated memo */}
              {generatedMemo && (
                <div className="mb-6 flex justify-end">
                  <button
                    onClick={handleSaveMemo}
                    className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <Save size={16} />
                    <span>{currentMemo ? "Update Memo" : "Save Memo"}</span>
                  </button>
                </div>
              )}

              {/* Current Memo Info */}
              {currentMemo && (
                <div className="mb-6 p-4 bg-blue-900/20 border border-blue-800 rounded-lg">
                  <h2 className="text-white font-semibold">
                    {currentMemo.title}
                  </h2>
                  {currentMemo.company_name && (
                    <p className="text-blue-400 text-sm">
                      {currentMemo.company_name}
                    </p>
                  )}
                  <p className="text-gray-400 text-sm">
                    Last updated:{" "}
                    {new Date(currentMemo.updated_at).toLocaleString()}
                  </p>
                </div>
              )}

              <HeroSection />

              {!showResults && !currentMemo && (
                <UploadSection
                  key={workspaceKey}
                  referenceFiles={referenceFiles}
                  exampleFiles={exampleFiles}
                  companyContext={companyContext}
                  isProcessing={isProcessing}
                  processingStage={processingStage}
                  onReferenceUpload={(files) =>
                    handleFileUpload(files, "reference")
                  }
                  onExampleUpload={(files) =>
                    handleFileUpload(files, "example")
                  }
                  onRemoveReferenceFile={(index) =>
                    removeFile(index, "reference")
                  }
                  onRemoveExampleFile={(index) => removeFile(index, "example")}
                  onContextChange={setCompanyContext}
                  onGenerate={generateMemo}
                  activeTab={activeTab}
                  onTabChange={setActiveTab}
                  rawTextInput={rawTextInput}
                  onRawTextChange={setRawTextInput}
                  rawTextLabel={rawTextLabel}
                  onRawTextLabelChange={setRawTextLabel}
                  urlInput={urlInput}
                  onUrlChange={setUrlInput}
                  urlLabel={urlLabel}
                  onUrlLabelChange={setUrlLabel}
                  onAddText={addText}
                  onAddUrl={addUrl}
                  referenceTexts={referenceTexts}
                  referenceUrls={referenceUrls}
                  onRemoveText={removeText}
                  onRemoveUrl={removeUrl}
                  fileProcessingStatus={fileProcessingStatus}
                  generationProgress={generationProgress}
                />
              )}

              {(showResults || isProcessing || currentMemo) && (
                <ResultsSection
                  generatedMemo={generatedMemo}
                  streamingMemo={streamingMemo}
                  showResults={showResults || !!currentMemo}
                  showChat={showChat}
                  chatHistory={chatHistory}
                  chatMessage={chatMessage}
                  isChatProcessing={isChatProcessing}
                  isProcessing={isProcessing}
                  onToggleChat={() => setShowChat(!showChat)}
                  onCopyMemo={copyToClipboard}
                  onDownloadMemo={downloadMemo}
                  onFileUpload={(files) => handleFileUpload(files, "reference")}
                  onRegenerate={regenerateMemo}
                  onChatMessageChange={setChatMessage}
                  onSendChatMessage={sendChatMessage}
                  onStartOver={handleNewMemo}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
