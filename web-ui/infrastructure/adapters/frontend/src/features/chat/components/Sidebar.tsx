import { useMemo, useState } from "react";
import type { ChatSummary } from "../types";

interface SidebarProps {
  chats: ChatSummary[];
  selectedChatId: string;
  isExpanded: boolean;
  onChatSelect: (chatId: string) => void;
  onCreateChat: () => void;
  onToggleSidebar: () => void;
}

export function Sidebar({
  chats,
  selectedChatId,
  isExpanded,
  onChatSelect,
  onCreateChat,
  onToggleSidebar,
}: SidebarProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredChats = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    if (!normalizedSearch) {
      return chats;
    }

    return chats.filter((chat) =>
      `${chat.title} ${chat.lastMessagePreview}`.toLowerCase().includes(normalizedSearch),
    );
  }, [chats, searchTerm]);

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
          <button className="sidebar__add-chat" type="button" onClick={onCreateChat}>
            <img className="sidebar__add-icon-image" src="/icons/add-chat.svg" alt="" aria-hidden="true" />
            Anadir Chat
          </button>
        ) : (
          <button className="sidebar__compact-action" type="button" onClick={onCreateChat} aria-label="Anadir chat">
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
              <button
                key={chat.id}
                className={`chat-list__item ${isSelected ? "chat-list__item--selected" : ""}`}
                type="button"
                onClick={() => onChatSelect(chat.id)}
              >
                <span className="chat-list__title">{chat.title}</span>
              </button>
            );
          })}

          {!filteredChats.length ? (
            <p className="chat-list__empty">No hay chats que coincidan.</p>
          ) : null}
        </div>
      ) : null}
    </aside>
  );
}
