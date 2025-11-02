import { useState } from "react";
import useHandleStreamResponse from "@/utils/useHandleStreamResponse";

export function useChatAssistant(currentContent, setCurrentContent) {
  const [showChat, setShowChat] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatProcessing, setIsChatProcessing] = useState(false);
  const [streamingResponse, setStreamingResponse] = useState("");

  const handleChatFinish = (message) => {
    setCurrentContent(message);
    setChatHistory((prev) => [
      ...prev,
      { role: "assistant", content: message },
    ]);
    setIsChatProcessing(false);
    setStreamingResponse("");
  };

  const handleStreamResponse = useHandleStreamResponse({
    onChunk: setStreamingResponse,
    onFinish: handleChatFinish,
  });

  const sendChatMessage = async () => {
    if (!chatMessage.trim() || !currentContent) return;

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
                content: `You are an expert VC analyst helping edit an investment memo. The user will ask you to make specific changes to sections of the memo. Apply their requested changes and return the updated full memo in markdown format. Maintain the existing structure and formatting.`,
              },
              {
                role: "user",
                content: `Current memo:
${currentContent}

User request: ${userMessage}

Please apply the requested changes and return the updated full memo.`,
              },
            ],
            stream: true,
          }),
        },
      );

      if (!aiResponse.ok) {
        throw new Error(`AI API error: ${aiResponse.status}`);
      }

      handleStreamResponse(aiResponse);
    } catch (error) {
      console.error("Error processing chat:", error);
      setIsChatProcessing(false);
      alert(`Failed to process chat request: ${error.message}`);
    }
  };

  return {
    showChat,
    setShowChat,
    chatMessage,
    setChatMessage,
    chatHistory,
    isChatProcessing,
    streamingResponse,
    sendChatMessage,
  };
}
