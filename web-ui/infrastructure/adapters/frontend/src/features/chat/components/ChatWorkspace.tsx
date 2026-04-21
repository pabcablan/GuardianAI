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
    selectChat,
    createChat,
    sendMessage,
  } = useChatWorkspace();
  const [draft, setDraft] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  function handleFileSelect(file: File | null) {
    if (!file) {
      return;
    }

    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      return;
    }

    setPendingFile(file);
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
          pendingFile={pendingFile}
          onDraftChange={setDraft}
          onFileSelect={handleFileSelect}
          onClearFile={() => setPendingFile(null)}
          onSubmit={() => {
            void sendMessage(draft, pendingFile);
            setDraft("");
            setPendingFile(null);
          }}
        />
      </section>
    </main>
  );
}
