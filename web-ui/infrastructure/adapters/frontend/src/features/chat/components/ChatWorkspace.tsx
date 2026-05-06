import { useState } from "react";
import type {
  AnonymizationMode,
  AnonymizationOption,
  AnonymizationSettings,
  AiModel,
} from "../types";
import { DEFAULT_AI_MODEL } from "../types";
import { AnonymizationSettingsPanel } from "./AnonymizationSettingsPanel";
import { useChatWorkspace } from "../hooks/useChatWorkspace";
import { Sidebar } from "./Sidebar";
import { ConversationPanel } from "./ConversationPanel";

const DEFAULT_ANONYMIZATION_SETTINGS: AnonymizationSettings = {
  personNames: "anonymize",
  identityDocuments: "anonymize",
  emails: "anonymize",
  addresses: "anonymize",
  phones: "anonymize",
  organizations: "anonymize",
  relevantCodes: "anonymize",
};

export function ChatWorkspace() {
  const {
    chats,
    selectedChat,
    selectedChatId,
    errorMessage,
    isLoadingChats,
    isResponding,
    documentProcessingStatus,
    responseProcessingStatus,
    modelReadiness,
    isInteractionLocked,
    selectChat,
    createChat,
    renameChat,
    deleteChat,
    sendMessage,
    approveAnonymizedMessage,
  } = useChatWorkspace();
  const [draft, setDraft] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [shouldPreviewAnonymizedText, setShouldPreviewAnonymizedText] =
    useState(true);
  const [selectedModel, setSelectedModel] = useState<AiModel>(
    DEFAULT_AI_MODEL,
  );
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [anonymizationSettings, setAnonymizationSettings] = useState(
    DEFAULT_ANONYMIZATION_SETTINGS,
  );

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
    const didSend = await sendMessage(
      draft,
      pendingFile,
      shouldPreviewAnonymizedText,
      selectedModel,
    );
    if (!didSend) {
      return;
    }

    setDraft("");
    setPendingFile(null);
  }

  function updateAnonymizationSetting(
    option: AnonymizationOption,
    mode: AnonymizationMode,
  ) {
    setAnonymizationSettings((currentSettings) => ({
      ...currentSettings,
      [option]: mode,
    }));
  }

  return (
    <main className="chat-shell">
      <section className={`chat-frame ${isSidebarOpen ? "" : "chat-frame--sidebar-hidden"}`.trim()}>
        <Sidebar
          chats={chats}
          selectedChatId={selectedChatId}
          isExpanded={isSidebarOpen}
          isInteractionLocked={isInteractionLocked}
          selectedModel={selectedModel}
          onChatSelect={selectChat}
          onCreateChat={createChat}
          onRenameChat={renameChat}
          onDeleteChat={deleteChat}
          onModelChange={setSelectedModel}
          onToggleSidebar={() => setIsSidebarOpen((current) => !current)}
          onOpenSettings={() => setIsSettingsOpen(true)}
        />
        <ConversationPanel
          chat={selectedChat}
          draft={draft}
          errorMessage={errorMessage}
          isLoadingChats={isLoadingChats}
          isResponding={isResponding}
          isInteractionLocked={isInteractionLocked}
          modelReadiness={modelReadiness}
          documentProcessingStatus={documentProcessingStatus}
          responseProcessingStatus={responseProcessingStatus}
          pendingFile={pendingFile}
          shouldPreviewAnonymizedText={shouldPreviewAnonymizedText}
          onDraftChange={setDraft}
          onPreviewAnonymizedTextChange={setShouldPreviewAnonymizedText}
          onFileSelect={handleFileSelect}
          onClearFile={() => setPendingFile(null)}
          onApproveAnonymizedMessage={(message) => {
            void approveAnonymizedMessage(message, selectedModel);
          }}
          onSubmit={() => {
            void handleSubmit();
          }}
        />
        {isSettingsOpen ? (
          <AnonymizationSettingsPanel
            settings={anonymizationSettings}
            onChange={updateAnonymizationSetting}
            onClose={() => setIsSettingsOpen(false)}
          />
        ) : null}
      </section>
    </main>
  );
}
