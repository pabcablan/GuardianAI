import { useEffect, useMemo, useRef, useState } from "react";
import type { AiModel, ChatSummary } from "../types";
import { AI_MODEL_OPTIONS, AI_MODEL_PRICING } from "../types";

interface SidebarProps {
  chats: ChatSummary[];
  selectedChatId: string;
  isExpanded: boolean;
  isInteractionLocked: boolean;
  selectedModel: AiModel;
  onChatSelect: (chatId: string) => void;
  onCreateChat: () => void;
  onRenameChat: (chatId: string, title: string) => Promise<boolean>;
  onDeleteChat: (chatId: string) => Promise<boolean>;
  onModelChange: (model: AiModel) => void;
  onToggleSidebar: () => void;
  onOpenSettings: () => void;
}

export function Sidebar({
  chats,
  selectedChatId,
  isExpanded,
  isInteractionLocked,
  selectedModel,
  onChatSelect,
  onCreateChat,
  onRenameChat,
  onDeleteChat,
  onModelChange,
  onToggleSidebar,
  onOpenSettings,
}: SidebarProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeChat, setActiveChat] = useState<ChatSummary | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [isApplyingAction, setIsApplyingAction] = useState(false);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const filteredChats = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    if (!normalizedSearch) {
      return chats;
    }

    return chats.filter((chat) =>
      `${chat.title} ${chat.lastMessagePreview}`.toLowerCase().includes(normalizedSearch),
    );
  }, [chats, searchTerm]);

  const modelDropdownRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        modelDropdownRef.current &&
        !modelDropdownRef.current.contains(event.target as Node)
      ) {
        setIsModelDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  function openChatActions(chat: ChatSummary): void {
    setActiveChat(chat);
    setDraftTitle(chat.title);
  }

  function closeChatActions(): void {
    if (isApplyingAction) {
      return;
    }

    setActiveChat(null);
    setDraftTitle("");
  }

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

  return (
    <aside className={`sidebar ${isExpanded ? "" : "sidebar--collapsed"}`.trim()}>
      <div className="sidebar__header">
        <div className="sidebar__brand">
          <button
            className="icon-button"
            type="button"
            aria-label={isExpanded ? "Comprimir panel lateral" : "Expandir panel lateral"}
            disabled={isInteractionLocked}
            onClick={onToggleSidebar}
          >
            <img className="icon-image" src="/icons/brand-mark.svg" alt="" aria-hidden="true" />
          </button>
          <div className="sidebar__title-wrap">
            <h1>Guardian AI</h1>
          </div>
        </div>
        <button
          className="icon-button sidebar__panel-button"
          type="button"
          aria-label="Comprimir panel lateral"
          aria-hidden={!isExpanded}
          tabIndex={isExpanded ? 0 : -1}
          disabled={isInteractionLocked}
          onClick={onToggleSidebar}
        >
          <img className="icon-image" src="/icons/sidebar-toggle.svg" alt="" aria-hidden="true" />
        </button>
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
            <img className="sidebar__add-icon-image" src="/icons/add-chat.svg" alt="" aria-hidden="true" />
            Añadir Chat
          </button>
        ) : (
          <button
            className="sidebar__compact-action"
            type="button"
            disabled={isInteractionLocked}
            onClick={onCreateChat}
            aria-label="Añadir chat"
          >
            <img className="icon-image" src="/icons/add-chat.svg" alt="" aria-hidden="true" />
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

              <div ref={modelDropdownRef} className={`model-dropdown ${isInteractionLocked ? "is-disabled" : ""}`}>
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
                    ⌄
                  </span>
                </button>

                {isModelDropdownOpen && !isInteractionLocked && (
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
                )}
              </div>
            </div>

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
          <button
            className="sidebar__compact-action"
            type="button"
            disabled={isInteractionLocked}
            onClick={onOpenSettings}
            aria-label="Abrir configuración"
          >
            <span className="icon icon--settings" aria-hidden="true" />
          </button>
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
