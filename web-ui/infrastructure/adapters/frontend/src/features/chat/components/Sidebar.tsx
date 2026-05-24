import { useEffect, useMemo, useRef, useState } from "react";

import { AI_MODEL_OPTIONS, AI_MODEL_PRICING } from "../types";
import type { AiModel, ChatSummary } from "../types";

interface SidebarProps {
  chats: ChatSummary[];
  isExpanded: boolean;
  isInteractionLocked: boolean;
  selectedChatId: string;
  selectedModel: AiModel;
  theme: "dark" | "light";
  onChatSelect: (chatId: string) => void;
  onCreateChat: () => void;
  onDeleteChat: (chatId: string) => Promise<boolean>;
  onModelChange: (model: AiModel) => void;
  onOpenSettings: () => void;
  onRenameChat: (chatId: string, title: string) => Promise<boolean>;
  onThemeToggle: () => void;
  onToggleSidebar: () => void;
}

// Render the sidebar with chat navigation, model selection, and settings access.
export function Sidebar({
  chats,
  isExpanded,
  isInteractionLocked,
  selectedChatId,
  selectedModel,
  theme,
  onChatSelect,
  onCreateChat,
  onDeleteChat,
  onModelChange,
  onOpenSettings,
  onRenameChat,
  onThemeToggle,
  onToggleSidebar,
}: SidebarProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeChat, setActiveChat] = useState<ChatSummary | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [isApplyingAction, setIsApplyingAction] = useState(false);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const modelDropdownRef = useRef<HTMLDivElement | null>(null);

  const filteredChats = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    if (!normalizedSearch) {
      return chats;
    }

    return chats.filter((chat) =>
      `${chat.title} ${chat.lastMessagePreview}`
        .toLowerCase()
        .includes(normalizedSearch),
    );
  }, [chats, searchTerm]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        modelDropdownRef.current &&
        !modelDropdownRef.current.contains(event.target as Node)
      ) {
        setIsModelDropdownOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Open the per-chat actions modal for rename and delete operations.
  function openChatActions(chat: ChatSummary): void {
    setActiveChat(chat);
    setDraftTitle(chat.title);
  }

  // Close the per-chat actions modal unless an action is still running.
  function closeChatActions(): void {
    if (isApplyingAction) {
      return;
    }

    setActiveChat(null);
    setDraftTitle("");
  }

  // Rename the active chat and close the modal when the update succeeds.
  async function handleRenameChat(): Promise<void> {
    if (!activeChat) {
      return;
    }

    setIsApplyingAction(true);
    const didRename = await onRenameChat(activeChat.id, draftTitle);
    setIsApplyingAction(false);

    if (didRename) {
      closeChatActions();
    }
  }

  // Delete the active chat and close the modal when the removal succeeds.
  async function handleDeleteChat(): Promise<void> {
    if (!activeChat) {
      return;
    }

    setIsApplyingAction(true);
    const didDelete = await onDeleteChat(activeChat.id);
    setIsApplyingAction(false);

    if (didDelete) {
      closeChatActions();
    }
  }

  const selectedModelPricing = AI_MODEL_PRICING[selectedModel];

  // Render the sidebar with chat navigation, model selection, and settings access.
  return (
    <aside className={`sidebar ${isExpanded ? "" : "sidebar--collapsed"}`.trim()}>
      <div className="sidebar__header">
        <button
          className="icon-button sidebar__panel-button"
          type="button"
          aria-label={
            isExpanded ? "Comprimir panel lateral" : "Expandir panel lateral"
          }
          onClick={onToggleSidebar}
        >
          <img
            className="icon-image"
            src="/icons/sidebar-toggle.svg"
            alt=""
            aria-hidden="true"
          />
        </button>
        <div className="sidebar__brand">
          <img
            className="sidebar__brand-mark"
            src={
              theme === "light"
                ? "/icons/brand-mark-light.svg"
                : "/icons/brand-mark.svg"
            }
            alt="Guardian AI"
          />
          <div className="sidebar__title-wrap">
            <img
              className="sidebar__brand-logo"
              src={
                theme === "light"
                  ? "/icons/guardianai-brand-light.svg"
                  : "/icons/guardianai-brand.svg"
              }
              alt="Guardian AI Anonymization"
            />
          </div>
        </div>
      </div>

      {isExpanded ? (
        <label className="search-box" htmlFor="chat-search">
          <input
            id="chat-search"
            type="search"
            placeholder="Buscar"
            value={searchTerm}
            disabled={isInteractionLocked}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <span className="icon icon--search" aria-hidden="true" />
        </label>
      ) : (
        <button
          className="sidebar__compact-action"
          type="button"
          aria-label="Buscar chats"
          disabled={isInteractionLocked}
        >
          <span className="icon icon--search" aria-hidden="true" />
        </button>
      )}

      <div className="sidebar__section">
        {isExpanded ? (
          <button
            className="sidebar__add-chat"
            type="button"
            disabled={isInteractionLocked}
            onClick={onCreateChat}
          >
            <img
              className="sidebar__add-icon-image"
              src="/icons/add-chat.svg"
              alt=""
              aria-hidden="true"
            />
            Nuevo chat
          </button>
        ) : (
          <button
            className="sidebar__compact-action"
            type="button"
            disabled={isInteractionLocked}
            onClick={onCreateChat}
            aria-label="Nuevo chat"
          >
            <img
              className="icon-image"
              src="/icons/add-chat.svg"
              alt=""
              aria-hidden="true"
            />
          </button>
        )}
      </div>

      {isExpanded ? (
        <div className="sidebar__section">
          <p className="sidebar__section-title">Chats</p>
        </div>
      ) : null}

      {isExpanded ? (
        <div className="chat-list">
          {filteredChats.map((chat) => {
            const isSelected = chat.id === selectedChatId;

            return (
              <div
                key={chat.id}
                className={`chat-list__item ${isSelected ? "chat-list__item--selected" : ""}`}
              >
                <button
                  className="chat-list__select"
                  type="button"
                  disabled={isInteractionLocked}
                  onClick={() => onChatSelect(chat.id)}
                >
                  <span className="chat-list__title">{chat.title}</span>
                </button>
                <button
                  className="chat-list__menu-button"
                  type="button"
                  aria-label={`Abrir opciones de ${chat.title}`}
                  disabled={isInteractionLocked}
                  onClick={() => openChatActions(chat)}
                >
                  <span className="chat-list__menu-dots" aria-hidden="true" />
                </button>
              </div>
            );
          })}

          {!filteredChats.length ? (
            <p className="chat-list__empty">No hay chats que coincidan.</p>
          ) : null}
        </div>
      ) : null}

      <div className="sidebar__footer">
        {isExpanded ? (
          <>
            <div className="sidebar__model-select">
              <span className="sidebar__model-label">Modelo IA</span>

              <div
                ref={modelDropdownRef}
                className={`model-dropdown ${isInteractionLocked ? "is-disabled" : ""}`}
              >
                <button
                  className="model-dropdown__trigger"
                  type="button"
                  disabled={isInteractionLocked}
                  onClick={() => setIsModelDropdownOpen((prev) => !prev)}
                  aria-haspopup="listbox"
                  aria-expanded={isModelDropdownOpen}
                >
                  <span className="model-dropdown__trigger-copy">
                    <span className="model-dropdown__name">{selectedModel}</span>
                    <span className="model-dropdown__price">
                      Entrada: {selectedModelPricing.input} | Salida:{" "}
                      {selectedModelPricing.output}
                    </span>
                  </span>
                  <span className="model-dropdown__chevron" aria-hidden="true">
                    ▾
                  </span>
                </button>

                {isModelDropdownOpen && !isInteractionLocked ? (
                  <ul className="model-dropdown__menu" role="listbox">
                    {AI_MODEL_OPTIONS.map((model) => {
                      const pricing = AI_MODEL_PRICING[model];

                      return (
                        <li
                          key={model}
                          className={`model-dropdown__option ${
                            selectedModel === model ? "is-selected" : ""
                          }`}
                          role="option"
                          aria-selected={selectedModel === model}
                          onClick={() => {
                            onModelChange(model);
                            setIsModelDropdownOpen(false);
                          }}
                        >
                          <span className="model-dropdown__name">{model}</span>
                          <span className="model-dropdown__price">
                            Entrada: {pricing.input} | Salida: {pricing.output}
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </div>
            </div>

            <button
              className="sidebar__settings sidebar__theme-toggle"
              type="button"
              disabled={isInteractionLocked}
              onClick={onThemeToggle}
            >
              <span className="sidebar__theme-icon" aria-hidden="true">
                {theme === "dark" ? "☀" : "☾"}
              </span>
              {theme === "dark" ? "Tema claro" : "Tema oscuro"}
            </button>

            <button
              className="sidebar__settings"
              type="button"
              disabled={isInteractionLocked}
              onClick={onOpenSettings}
            >
              <span className="icon icon--settings" aria-hidden="true" />
              Configuración
            </button>
          </>
        ) : (
          <>
            <button
              className="sidebar__compact-action"
              type="button"
              disabled={isInteractionLocked}
              onClick={onThemeToggle}
              aria-label={
                theme === "dark"
                  ? "Cambiar a tema claro"
                  : "Cambiar a tema oscuro"
              }
            >
              <span className="sidebar__theme-icon" aria-hidden="true">
                {theme === "dark" ? "☀" : "☾"}
              </span>
            </button>
            <button
              className="sidebar__compact-action"
              type="button"
              disabled={isInteractionLocked}
              onClick={onOpenSettings}
              aria-label="Abrir configuración"
            >
              <span className="icon icon--settings" aria-hidden="true" />
            </button>
          </>
        )}
      </div>

      {activeChat ? (
        <div
          className="chat-actions-modal"
          role="presentation"
          onClick={closeChatActions}
        >
          <div
            className="chat-actions-modal__dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="chat-actions-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="chat-actions-modal__header">
              <div>
                <p className="chat-actions-modal__eyebrow">Chat</p>
                <h2 id="chat-actions-title">Opciones</h2>
              </div>
              <button
                className="chat-actions-modal__close"
                type="button"
                aria-label="Cerrar opciones"
                onClick={closeChatActions}
              >
                x
              </button>
            </div>

            <label className="chat-actions-modal__field" htmlFor="chat-title">
              <span>Cambiar nombre</span>
              <input
                id="chat-title"
                type="text"
                maxLength={120}
                value={draftTitle}
                disabled={isApplyingAction}
                onChange={(event) => setDraftTitle(event.target.value)}
              />
            </label>

            <div className="chat-actions-modal__actions">
              <button
                className="chat-actions-modal__button"
                type="button"
                disabled={isApplyingAction}
                onClick={() => {
                  void handleRenameChat();
                }}
              >
                Guardar nombre
              </button>
              <button
                className="chat-actions-modal__button chat-actions-modal__button--danger"
                type="button"
                disabled={isApplyingAction}
                onClick={() => {
                  void handleDeleteChat();
                }}
              >
                Borrar chat
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </aside>
  );
}
