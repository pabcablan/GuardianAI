import { useState } from "react";
import { useChatWorkspace } from "../hooks/useChatWorkspace";
import { Sidebar } from "./Sidebar";
import { ConversationPanel } from "./ConversationPanel";

export function ChatWorkspace() {
  const {
    chats,
    selectedChat,
    selectedChatId,
    errorMessage,
    isLoadingChats,
    isResponding,
    documentProcessingStatus,
    isInteractionLocked,
    selectChat,
    createChat,
    sendMessage,
  } = useChatWorkspace();
  const [draft, setDraft] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  function handleFileSelect(file: File | null) {
    if (isInteractionLocked) {
      return;
    }

    if (!file) {
      return;
    }

    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      return;
    }

    setPendingFile(file);
  }

  async function handleSubmit() {
    const didSend = await sendMessage(draft, pendingFile);
    if (!didSend) {
      return;
    }

    setDraft("");
    setPendingFile(null);
  }

  return (
    <main className="chat-shell">
      <section className={`chat-frame ${isSidebarOpen ? "" : "chat-frame--sidebar-hidden"}`.trim()}>
        <Sidebar
          chats={chats}
          selectedChatId={selectedChatId}
          isExpanded={isSidebarOpen}
          onChatSelect={selectChat}
          onCreateChat={createChat}
          onToggleSidebar={() => setIsSidebarOpen((current) => !current)}
        />
        <ConversationPanel
          chat={selectedChat}
          draft={draft}
          errorMessage={errorMessage}
          isLoadingChats={isLoadingChats}
          isResponding={isResponding}
          isInteractionLocked={isInteractionLocked}
          documentProcessingStatus={documentProcessingStatus}
          pendingFile={pendingFile}
          onDraftChange={setDraft}
          onFileSelect={handleFileSelect}
          onClearFile={() => setPendingFile(null)}
          onSubmit={() => {
            void handleSubmit();
          }}
        />
      </section>
    </main>
  );
}
