import type {
  DocumentProcessingStatus,
  ModelReadinessStatus,
  ResponseProcessingStatus,
} from "../types";

interface ConversationProgressStackProps {
  documentProcessingStatus: DocumentProcessingStatus | null;
  modelReadiness: ModelReadinessStatus;
  responseProcessingStatus: ResponseProcessingStatus | null;
}

export function ConversationProgressStack({
  documentProcessingStatus,
  modelReadiness,
  responseProcessingStatus,
}: ConversationProgressStackProps) {
  return (
    <>
      {!modelReadiness.ready ? (
        <section
          className="model-readiness-card"
          aria-live="polite"
          aria-atomic="true"
        >
          <p className="model-readiness-card__eyebrow">Inicializando modelos</p>
          <h2 className="model-readiness-card__title">
            GuardianAI se está preparando
          </h2>
          <p className="model-readiness-card__copy">{modelReadiness.message}</p>
          <div className="model-readiness-card__bar" role="progressbar">
            <span />
          </div>
        </section>
      ) : null}

      {documentProcessingStatus || responseProcessingStatus ? (
        <div className="conversation__progress-stack">
          {documentProcessingStatus ? (
            <section
              className="processing-card"
              aria-live="polite"
              aria-atomic="true"
            >
              <div className="processing-card__header">
                <div>
                  <p className="processing-card__eyebrow">
                    Procesando documento
                  </p>
                  <h2 className="processing-card__title">
                    {documentProcessingStatus.filename}
                  </h2>
                </div>
                <span className="processing-card__stage">
                  {documentProcessingStatus.stage}
                </span>
              </div>
              <p className="processing-card__message">
                {documentProcessingStatus.message}
              </p>
              <div className="processing-card__loader" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <div
                className={`processing-card__bar ${documentProcessingStatus.progress === null ? "processing-card__bar--indeterminate" : ""}`.trim()}
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={
                  documentProcessingStatus.progress === null
                    ? undefined
                    : Math.round(documentProcessingStatus.progress * 100)
                }
              >
                <span
                  className="processing-card__bar-fill"
                  style={
                    documentProcessingStatus.progress === null
                      ? undefined
                      : {
                          width: `${Math.max(8, documentProcessingStatus.progress * 100)}%`,
                        }
                  }
                />
              </div>
            </section>
          ) : null}

          {responseProcessingStatus ? (
            <section
              className="processing-card"
              aria-live="polite"
              aria-atomic="true"
            >
              <div className="processing-card__header">
                <div>
                  <p className="processing-card__eyebrow">
                    Protegiendo contenido
                  </p>
                  <h2 className="processing-card__title">
                    {responseProcessingStatus.title}
                  </h2>
                </div>
                <span className="processing-card__stage">
                  {responseProcessingStatus.stage}
                </span>
              </div>
              <p className="processing-card__message">
                {responseProcessingStatus.message}
              </p>
              <div className="processing-card__loader" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <div
                className="processing-card__bar processing-card__bar--indeterminate"
                role="progressbar"
              >
                <span className="processing-card__bar-fill" />
              </div>
            </section>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
