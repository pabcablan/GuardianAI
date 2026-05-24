import type { ReactNode } from "react";

interface MarkdownTokenMatch {
  end: number;
  inner: string;
  start: number;
  type: "bold" | "boldItalic" | "italic" | "code";
}

// Find the next supported inline markdown token inside one text slice.
function findNextMarkdownToken(content: string): MarkdownTokenMatch | null {
  const patterns: Array<{
    expression: RegExp;
    type: MarkdownTokenMatch["type"];
  }> = [
    { expression: /`([^`\n]+)`/, type: "code" },
    {
      expression: /\*\*\*([^*\n](?:[\s\S]*?[^*\n])?)\*\*\*/,
      type: "boldItalic",
    },
    { expression: /\*\*([^*\n](?:[\s\S]*?[^*\n])?)\*\*/, type: "bold" },
    { expression: /\*([^*\n](?:[\s\S]*?[^*\n])?)\*/, type: "italic" },
  ];

  let nextMatch: MarkdownTokenMatch | null = null;

  for (const pattern of patterns) {
    const result = pattern.expression.exec(content);
    if (!result || result.index === undefined) {
      continue;
    }

    const candidate: MarkdownTokenMatch = {
      type: pattern.type,
      start: result.index,
      end: result.index + result[0].length,
      inner: result[1] ?? "",
    };

    if (
      nextMatch === null ||
      candidate.start < nextMatch.start ||
      (
        candidate.start === nextMatch.start &&
        candidate.end > nextMatch.end
      )
    ) {
      nextMatch = candidate;
    }
  }

  return nextMatch;
}

// Render inline markdown tokens such as bold, italic, and inline code.
function renderInlineMarkdown(content: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let cursor = 0;
  let key = 0;

  while (cursor < content.length) {
    const match = findNextMarkdownToken(content.slice(cursor));

    if (!match) {
      nodes.push(content.slice(cursor));
      break;
    }

    const absoluteStart = cursor + match.start;
    const absoluteEnd = cursor + match.end;

    if (absoluteStart > cursor) {
      nodes.push(content.slice(cursor, absoluteStart));
    }

    if (match.type === "code") {
      nodes.push(
        <code key={`md-code-${key++}`}>{match.inner}</code>,
      );
    } else if (match.type === "boldItalic") {
      nodes.push(
        <strong key={`md-strong-em-${key++}`}>
          <em>{renderInlineMarkdown(match.inner)}</em>
        </strong>,
      );
    } else if (match.type === "bold") {
      nodes.push(
        <strong key={`md-strong-${key++}`}>
          {renderInlineMarkdown(match.inner)}
        </strong>,
      );
    } else {
      nodes.push(
        <em key={`md-em-${key++}`}>
          {renderInlineMarkdown(match.inner)}
        </em>,
      );
    }

    cursor = absoluteEnd;
  }

  return nodes;
}

// Render one assistant message with lightweight markdown support.
export function renderAssistantMarkdown(content: string): ReactNode {
  const blocks = content.split(/\n{2,}/).filter((block) => block.trim().length);

  return blocks.map((block, blockIndex) => {
    const trimmedBlock = block.trim();
    const headingMatch = /^(#{1,3})\s+(.+)$/.exec(trimmedBlock);
    const separatorMatch = /^(?:---+|\*\*\*+|___+)$/.exec(trimmedBlock);

    if (separatorMatch) {
      return <hr key={`md-block-${blockIndex}`} className="message__separator" />;
    }

    if (headingMatch) {
      const headingLevel = headingMatch[1].length;
      const headingContent = renderInlineMarkdown(headingMatch[2].trim());

      if (headingLevel === 1) {
        return <h1 key={`md-block-${blockIndex}`}>{headingContent}</h1>;
      }

      if (headingLevel === 2) {
        return <h2 key={`md-block-${blockIndex}`}>{headingContent}</h2>;
      }

      return <h3 key={`md-block-${blockIndex}`}>{headingContent}</h3>;
    }

    const lines = trimmedBlock.split("\n");
    const bulletLines = lines.filter((line) => /^[-*]\s+/.test(line.trim()));
    const numberedLines = lines.filter((line) => /^\d+\.\s+/.test(line.trim()));

    if (bulletLines.length === lines.length) {
      return (
        <ul key={`md-block-${blockIndex}`}>
          {lines.map((line, index) => (
            <li key={`md-bullet-${blockIndex}-${index}`}>
              {renderInlineMarkdown(line.trim().replace(/^[-*]\s+/, ""))}
            </li>
          ))}
        </ul>
      );
    }

    if (numberedLines.length === lines.length) {
      return (
        <ol key={`md-block-${blockIndex}`}>
          {lines.map((line, index) => (
            <li key={`md-number-${blockIndex}-${index}`}>
              {renderInlineMarkdown(line.trim().replace(/^\d+\.\s+/, ""))}
            </li>
          ))}
        </ol>
      );
    }

    return (
      <p key={`md-block-${blockIndex}`}>
        {lines.flatMap((line, index) => {
          const lineNodes = renderInlineMarkdown(line);
          if (index === lines.length - 1) {
            return lineNodes;
          }
          return [
            ...lineNodes,
            <br key={`md-break-${blockIndex}-${index}`} />,
          ];
        })}
      </p>
    );
  });
}
