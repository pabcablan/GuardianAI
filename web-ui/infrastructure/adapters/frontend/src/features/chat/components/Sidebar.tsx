import { useMemo, useState } from "react";
import type { ChatSummary } from "../types";

interface SidebarProps {
  chats: ChatSummary[];
  selectedChatId: string;
  isExpanded: boolean;
  onChatSelect: (chatId: string) => void;
  onCreateChat: () => void;
  onRenameChat: (chatId: string, title: string) => Promise<boolean>;
  onDeleteChat: (chatId: string) => Promise<boolean>;
  onToggleSidebar: () => void;
  onOpenSettings: () => void;
}

export function Sidebar({
  chats,
  selectedChatId,
  isExpanded,
  onChatSelect,
  onCreateChat,
  onRenameChat,
  onDeleteChat,
  onToggleSidebar,
  onOpenSettings,
}: SidebarProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeChat, setActiveChat] = useState<ChatSummary | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [isApplyingAction, setIsApplyingAction] = useState(false);

  const filteredChats = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    if (!normalizedSearch) {
      return chats;
    }

    return chats.filter((chat) =>
      `${chat.title} ${chat.lastMessagePreview}`.toLowerCase().includes(normalizedSearch),
    );
  }, [chats, searchTerm]);

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

  return (
    <aside className={`sidebar ${isExpanded ? "" : "sidebar--collapsed"}`.trim()}>
      <div className="sidebar__header">
        <div className="sidebar__brand">
          <button
            className="icon-button"
            type="button"
            aria-label={isExpanded ? "Comprimir panel lateral" : "Expandir panel lateral"}
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
            placeholder="Search"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <span className="icon icon--search" aria-hidden="true" />
        </label>
      ) : (
        <button className="sidebar__compact-action" type="button" aria-label="Buscar chats">
          <span className="icon icon--search" aria-hidden="true" />
        </button>
      )}

      <div className="sidebar__section">
        {isExpanded ? (
          <button
            className="sidebar__add-chat"
            type="button"
            onClick={onCreateChat}
          >
            <img className="sidebar__add-icon-image" src="/icons/add-chat.svg" alt="" aria-hidden="true" />
            Anadir Chat
          </button>
        ) : (
          <button
            className="sidebar__compact-action"
            type="button"
            onClick={onCreateChat}
            aria-label="Anadir chat"
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
                  onClick={() => onChatSelect(chat.id)}
                >
                  <span className="chat-list__title">{chat.title}</span>
                </button>
                <button
                  className="chat-list__menu-button"
                  type="button"
                  aria-label={`Abrir opciones de ${chat.title}`}
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
          <button
            className="sidebar__settings"
            type="button"
            onClick={onOpenSettings}
          >
            <span className="icon icon--settings" aria-hidden="true" />
            Configuracion
          </button>
        ) : (
          <button
            className="sidebar__compact-action"
            type="button"
            onClick={onOpenSettings}
            aria-label="Abrir configuracion"
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
