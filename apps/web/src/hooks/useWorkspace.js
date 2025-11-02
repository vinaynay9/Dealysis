/**
 * useWorkspace Hook
 * 
 * Main workspace state and logic for memo generation workflow.
 * 
 * Manages:
 * - File uploads (reference documents, example memos)
 * - Text/URL references
 * - Multi-step memo generation (8 sections)
 * - Chat interface for refinements
 * - Progress tracking
 * - Auto-save functionality
 * 
 * @param {Function} onMemoSaved - Callback when memo is auto-saved (optional)
 * @returns {Object} Workspace state and handlers
 * 
 * Key functions:
 * - handleFileUpload: Process uploaded files with AI analysis
 * - generateMemo: Generate all 8 sections sequentially
 * - sendChatMessage: Refine memo via AI chat
 * - startOver: Reset workspace to initial state
 */
import { useState, useCallback } from "react";
import useHandleStreamResponse from "@/utils/useHandleStreamResponse";

export function useWorkspace(onMemoSaved) {
  const [referenceFiles, setReferenceFiles] = useState([]);
  const [exampleFiles, setExampleFiles] = useState([]);
  const [referenceSummaries, setReferenceSummaries] = useState([]); // AI-processed summaries
  const [exampleSummaries, setExampleSummaries] = useState([]); // AI-processed summaries
  const [referenceTexts, setReferenceTexts] = useState([]);
  const [referenceUrls, setReferenceUrls] = useState([]);
  const [companyContext, setCompanyContext] = useState("");
  const [rawTextInput, setRawTextInput] = useState("");
  const [rawTextLabel, setRawTextLabel] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [urlLabel, setUrlLabel] = useState("");
  const [activeTab, setActiveTab] = useState("files");
  const [isProcessing, setIsProcessing] = useState(false);
  const [generatedMemo, setGeneratedMemo] = useState("");
  const [streamingMemo, setStreamingMemo] = useState("");
  const [processingStage, setProcessingStage] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatProcessing, setIsChatProcessing] = useState(false);
  const [fileProcessingStatus, setFileProcessingStatus] = useState({}); // Track individual file processing

  // New state for micro-prompt flow
  const [generationProgress, setGenerationProgress] = useState({
    currentSection: "",
    completedSections: [],
    totalSections: 8,
    currentStep: 0,
    error: null,
  });
  const [memoSections, setMemoSections] = useState({});

  const handleFinish = useCallback((message) => {
    setGeneratedMemo(message);
    setStreamingMemo("");
    setIsProcessing(false);
    setShowResults(true);
  }, []);

  const handleChatFinish = useCallback((message) => {
    setGeneratedMemo(message);
    setChatHistory((prev) => [
      ...prev,
      { role: "assistant", content: message },
    ]);
    setIsChatProcessing(false);
  }, []);

  const handleStreamResponse = useHandleStreamResponse({
    onChunk: setStreamingMemo,
    onFinish: handleFinish,
  });

  const handleChatStreamResponse = useHandleStreamResponse({
    onChunk: (chunk) => {
      setGeneratedMemo((prev) => prev + chunk);
    },
    onFinish: handleChatFinish,
  });

  /**
   * Process a single file with AI analysis.
   * 
   * Uploads file to /api/process-documents and tracks processing status.
   * Updates fileProcessingStatus state with progress/errors.
   * 
   * @param {File} file - The file to process
   * @param {string} fileType - "reference" or "example"
   * @returns {Promise<Object>} Analysis result with fileName, analysis, etc.
   * @throws {Error} If processing fails
   */
  const processFileWithAI = async (file, fileType) => {
    const fileId = `${file.name}-${file.size}-${Date.now()}`;

    setFileProcessingStatus((prev) => ({
      ...prev,
      [fileId]: { status: "processing", fileName: file.name },
    }));

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("fileType", fileType);

      const response = await fetch("/api/process-documents", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        const errorMessage = result.error || `Failed to process ${file.name}`;

        setFileProcessingStatus((prev) => ({
          ...prev,
          [fileId]: {
            status: "error",
            fileName: file.name,
            error: errorMessage,
            details: result.details,
          },
        }));

        alert(
          `Error processing ${file.name}:\n\n${errorMessage}\n\nPlease try:\n• Converting to a simpler format (TXT, basic PDF)\n• Checking if the file is corrupted\n• Using a smaller file`,
        );

        throw new Error(errorMessage);
      }

      setFileProcessingStatus((prev) => ({
        ...prev,
        [fileId]: {
          status: "completed",
          fileName: file.name,
          processingType: result.analysisType || "Analysis",
        },
      }));

      // Add to appropriate summaries array (updated field name)
      if (fileType === "reference") {
        setReferenceSummaries((prev) => [...prev, result]);
      } else {
        setExampleSummaries((prev) => [...prev, result]);
      }

      return result;
    } catch (error) {
      console.error(`Error processing ${file.name}:`, error);

      setFileProcessingStatus((prev) => {
        if (prev[fileId]?.status === "error") {
          return prev;
        }
        return {
          ...prev,
          [fileId]: {
            status: "error",
            fileName: file.name,
            error: error.message || `Processing failed for ${file.name}`,
          },
        };
      });

      throw error;
    }
  };

  const handleFileUpload = async (files, type) => {
    const fileArray = Array.from(files).slice(0, 5);

    // Add to file lists immediately for UI feedback
    if (type === "reference") {
      setReferenceFiles((prev) => [...prev, ...fileArray].slice(0, 5));
    } else {
      setExampleFiles((prev) => [...prev, ...fileArray].slice(0, 5));
    }

    // Process each file individually with AI
    for (const file of fileArray) {
      try {
        await processFileWithAI(file, type);
      } catch (error) {
        console.error(`Failed to process ${file.name}:`, error);
        // Continue processing other files even if one fails
      }
    }
  };

  const removeFile = (index, type) => {
    if (type === "reference") {
      const removedFile = referenceFiles[index];
      setReferenceFiles((prev) => prev.filter((_, i) => i !== index));
      // Also remove corresponding summary (updated field name)
      setReferenceSummaries((prev) =>
        prev.filter((summary) => summary.fileName !== removedFile.name),
      );
    } else {
      const removedFile = exampleFiles[index];
      setExampleFiles((prev) => prev.filter((_, i) => i !== index));
      // Also remove corresponding summary (updated field name)
      setExampleSummaries((prev) =>
        prev.filter((summary) => summary.fileName !== removedFile.name),
      );
    }
  };

  const addText = useCallback(() => {
    if (rawTextInput.trim()) {
      const label =
        rawTextLabel.trim() || `Text Content #${referenceTexts.length + 1}`;
      setReferenceTexts((prev) => [
        ...prev,
        { label, content: rawTextInput.trim() },
      ]);
      setRawTextInput("");
      setRawTextLabel("");
    }
  }, [rawTextInput, rawTextLabel, referenceTexts.length]);

  const addUrl = useCallback(() => {
    if (urlInput.trim()) {
      const label =
        urlLabel.trim() || `URL Reference #${referenceUrls.length + 1}`;
      setReferenceUrls((prev) => [...prev, { label, url: urlInput.trim() }]);
      setUrlInput("");
      setUrlLabel("");
    }
  }, [urlInput, urlLabel, referenceUrls.length]);

  const removeText = useCallback((index) => {
    setReferenceTexts((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const removeUrl = useCallback((index) => {
    setReferenceUrls((prev) => prev.filter((_, i) => i !== index));
  }, []);

  /**
   * Generate complete investment memo by creating 8 sections sequentially.
   * 
   * Uses micro-prompt approach: each section generated independently
   * for better quality. Sections generated in fixed order:
   * 1. Executive Summary
   * 2. Company Overview
   * 3. Market Opportunity
   * 4. Product & Technology
   * 5. Competitive Landscape
   * 6. Traction & Financials
   * 7. Team & Leadership
   * 8. Risks & Recommendation
   * 
   * After generation:
   * - Combines sections into final memo
   * - Adds bibliography with source citations
   * - Auto-saves to database
   * - Tracks usage analytics
   * 
   * @returns {Promise<void>}
   * @throws {Error} If generation fails (continues with placeholder sections)
   * 
   * Total time: ~20-25 minutes for all sections
   */
  const generateMemo = async () => {
    if (
      referenceSummaries.length === 0 &&
      referenceTexts.length === 0 &&
      referenceUrls.length === 0
    ) {
      alert(
        "Please upload at least one reference document, add text content, or provide URLs",
      );
      return;
    }

    const startTime = Date.now();
    setIsProcessing(true);
    setMemoSections({});
    setGenerationProgress({
      currentSection: "",
      completedSections: [],
      totalSections: 8,
      currentStep: 0,
      error: null,
    });

    const sectionOrder = [
      "executive_summary",
      "company_overview",
      "market_opportunity",
      "product_technology",
      "competitive_landscape",
      "traction_financials",
      "team_leadership",
      "risks_recommendation",
    ];

    const sectionTitles = {
      executive_summary: "Executive Summary",
      company_overview: "Company Overview",
      market_opportunity: "Market Opportunity",
      product_technology: "Product & Technology",
      competitive_landscape: "Competitive Landscape",
      traction_financials: "Traction & Financials",
      team_leadership: "Team & Leadership",
      risks_recommendation: "Key Risks & Investment Recommendation",
    };

    // Extract company name from context or generated content for tracking
    const extractCompanyName = (text) => {
      if (!text) return null;

      // Look for common patterns
      const patterns = [
        /company[:\s]+([A-Z][a-zA-Z\s&.-]+)/i,
        /startup[:\s]+([A-Z][a-zA-Z\s&.-]+)/i,
        /([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:is|was|will)/,
        /analyzing\s+([A-Z][a-zA-Z\s&.-]+)/i,
      ];

      for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match && match[1] && match[1].length > 2 && match[1].length < 50) {
          return match[1].trim();
        }
      }
      return null;
    };

    let generationSuccessful = false;
    let extractedCompanyName = extractCompanyName(companyContext);

    try {
      // Generate each section individually
      for (let i = 0; i < sectionOrder.length; i++) {
        const sectionKey = sectionOrder[i];
        const sectionTitle = sectionTitles[sectionKey];

        setGenerationProgress((prev) => ({
          ...prev,
          currentSection: sectionTitle,
          currentStep: i + 1,
        }));

        setProcessingStage(
          `Generating ${sectionTitle}... (${i + 1}/${sectionOrder.length})`,
        );

        try {
          const response = await fetch("/api/generate-memo-sections", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              templateAnalysis: exampleSummaries,
              contentAnalyses: referenceSummaries,
              additionalContext: companyContext,
              referenceTexts: referenceTexts,
              referenceUrls: referenceUrls,
              sectionToGenerate: sectionKey,
            }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(
              errorData.error || `Failed to generate ${sectionTitle}`,
            );
          }

          const sectionResult = await response.json();

          // Add completed section
          setMemoSections((prev) => ({
            ...prev,
            [sectionKey]: {
              title: sectionResult.title,
              content: sectionResult.content,
              timestamp: sectionResult.timestamp,
            },
          }));

          setGenerationProgress((prev) => ({
            ...prev,
            completedSections: [...prev.completedSections, sectionKey],
          }));

          // Small delay to show progress
          await new Promise((resolve) => setTimeout(resolve, 500));
        } catch (sectionError) {
          console.error(
            `Error generating section ${sectionKey}:`,
            sectionError,
          );

          setGenerationProgress((prev) => ({
            ...prev,
            error: `Failed to generate ${sectionTitle}: ${sectionError.message}`,
          }));

          // Add placeholder section so memo can still be built
          setMemoSections((prev) => ({
            ...prev,
            [sectionKey]: {
              title: sectionTitle,
              content: `[Error generating this section: ${sectionError.message}]\n\nPlease regenerate this section or edit manually.`,
              timestamp: new Date().toISOString(),
              error: true,
            },
          }));
        }
      }

      // Combine all sections into final memo
      setProcessingStage("Assembling final memo...");

      // Use current sections from state
      setMemoSections((currentSections) => {
        let finalMemo = "";
        sectionOrder.forEach((sectionKey) => {
          const section = currentSections[sectionKey];
          if (section) {
            finalMemo += `# ${section.title}\n\n${section.content}\n\n---\n\n`;
          }
        });

        // Add bibliography section with sources
        finalMemo += `# Sources & Bibliography\n\n`;

        let sourceIndex = 1;

        // Add uploaded files as sources
        if (referenceSummaries.length > 0) {
          referenceSummaries.forEach((summary) => {
            finalMemo += `[${sourceIndex}] ${summary.fileName} - Uploaded document analysis\n\n`;
            sourceIndex++;
          });
        }

        // Add text references as sources
        if (referenceTexts.length > 0) {
          referenceTexts.forEach((text) => {
            finalMemo += `[${sourceIndex}] ${text.label} - Reference material\n\n`;
            sourceIndex++;
          });
        }

        // Add URLs as sources
        if (referenceUrls.length > 0) {
          referenceUrls.forEach((url) => {
            finalMemo += `[${sourceIndex}] ${url.label} - ${url.url}\n\n`;
            sourceIndex++;
          });
        }

        // Remove trailing separator before sources
        finalMemo = finalMemo.replace(
          /---\n\n# Sources & Bibliography/,
          "# Sources & Bibliography",
        );

        // Try to extract company name from generated content if not found in context
        if (!extractedCompanyName) {
          extractedCompanyName = extractCompanyName(finalMemo);
        }

        generationSuccessful = true;
        const endTime = Date.now();
        const processingTimeSeconds = Math.round((endTime - startTime) / 1000);

        // Track usage - don't let this fail the generation
        (async () => {
          try {
            await fetch("/api/track-usage", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                company_name: extractedCompanyName,
                files_uploaded_count: referenceSummaries.length,
                reference_texts_count: referenceTexts.length,
                reference_urls_count: referenceUrls.length,
                company_context: companyContext || null,
                user_notes: null,
                processing_time_seconds: processingTimeSeconds,
                sections_generated: Object.keys(currentSections).length,
                generation_successful: true,
                user_session_id:
                  sessionStorage.getItem("userId") || `session_${Date.now()}`,
              }),
            });
          } catch (trackingError) {
            console.error(
              "Usage tracking failed (non-critical):",
              trackingError,
            );
          }
        })();

        setGeneratedMemo(finalMemo);
        setIsProcessing(false);
        setProcessingStage("");

        // Auto-save the memo to user's account
        (async () => {
          try {
            const memoData = {
              title: extractedCompanyName
                ? `${extractedCompanyName} - Investment Memo`
                : `Investment Memo - ${new Date().toLocaleDateString()}`,
              content: finalMemo,
              sections: currentSections,
              metadata: {
                generated: new Date().toISOString(),
                totalSections: Object.keys(currentSections).length,
                referenceMaterials:
                  referenceSummaries.length +
                  referenceTexts.length +
                  referenceUrls.length,
              },
              company_name: extractedCompanyName,
            };

            const response = await fetch("/api/user-memos", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(memoData),
            });

            if (response.ok) {
              const data = await response.json();
              console.log("Memo auto-saved successfully:", data.memo.id);

              // Trigger sidebar refresh by calling onMemoSaved callback if provided
              if (onMemoSaved) {
                onMemoSaved(data.memo);
              }
            } else {
              console.error("Failed to auto-save memo");
            }
          } catch (autoSaveError) {
            console.error("Auto-save failed (non-critical):", autoSaveError);
          }
        })();

        setShowResults(true);

        return currentSections; // Return the same sections
      });

      generationSuccessful = true;
    } catch (error) {
      console.error("Error in multi-step memo generation:", error);
      setIsProcessing(false);
      setGenerationProgress((prev) => ({
        ...prev,
        error: `Memo generation failed: ${error.message}`,
      }));

      // Track failed generation
      const endTime = Date.now();
      const processingTimeSeconds = Math.round((endTime - startTime) / 1000);

      (async () => {
        try {
          await fetch("/api/track-usage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              company_name: extractedCompanyName,
              files_uploaded_count: referenceSummaries.length,
              reference_texts_count: referenceTexts.length,
              reference_urls_count: referenceUrls.length,
              company_context: companyContext || null,
              user_notes: `Error: ${error.message}`,
              processing_time_seconds: processingTimeSeconds,
              sections_generated: 0,
              generation_successful: false,
              user_session_id:
                sessionStorage.getItem("userId") || `session_${Date.now()}`,
            }),
          });
        } catch (trackingError) {
          console.error("Usage tracking failed (non-critical):", trackingError);
        }
      })();

      alert(`Failed to generate memo: ${error.message}\n\nPlease try again.`);
    }
  };

  const regenerateMemo = async () => {
    if (
      referenceSummaries.length === 0 &&
      referenceTexts.length === 0 &&
      referenceUrls.length === 0
    ) {
      alert("Please add reference materials before regenerating the memo");
      return;
    }

    // Use the same generateMemo logic for regeneration
    await generateMemo();
  };

  const sendChatMessage = async () => {
    if (!chatMessage.trim() || !generatedMemo) return;

    const userMessage = chatMessage;
    setChatMessage("");
    setChatHistory((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsChatProcessing(true);

    try {
      const aiResponse = await fetch(
        "/integrations/chat-gpt/conversationgpt4",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: [
              {
                role: "system",
                content: `You are an expert VC analyst helping edit an investment memo. The user will ask you to make specific changes to sections of the memo. Apply their requested changes and return the updated full memo.`,
              },
              {
                role: "user",
                content: `Current memo:
${generatedMemo}

User request: ${userMessage}

Please apply the requested changes and return the updated full memo.`,
              },
            ],
            stream: true,
          }),
        },
      );

      if (!aiResponse.ok) {
        const errorText = await aiResponse.text();
        throw new Error(
          `ChatGPT API error: ${aiResponse.status} - ${errorText}`,
        );
      }

      setGeneratedMemo("");
      handleChatStreamResponse(aiResponse);
    } catch (error) {
      console.error("Error processing chat:", error);
      setIsChatProcessing(false);
      alert(
        `Failed to process chat request: ${error.message}\n\nPlease try again.`,
      );
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedMemo);
    alert("Memo copied to clipboard!");
  };

  const downloadMemo = () => {
    const blob = new Blob([generatedMemo], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "investment-memo.txt";
    a.click();
  };

  const startOver = () => {
    setReferenceFiles([]);
    setExampleFiles([]);
    setReferenceSummaries([]);
    setExampleSummaries([]);
    setReferenceTexts([]);
    setReferenceUrls([]);
    setRawTextInput("");
    setUrlInput("");
    setCompanyContext("");
    setGeneratedMemo("");
    setStreamingMemo("");
    setShowResults(false);
    setIsProcessing(false);
    setShowChat(false);
    setChatHistory([]);
    setFileProcessingStatus({});
    setMemoSections({});
    setGenerationProgress({
      currentSection: "",
      completedSections: [],
      totalSections: 8,
      currentStep: 0,
      error: null,
    });
  };

  return {
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
    generationProgress, // NEW
    memoSections, // NEW
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
  };
}
