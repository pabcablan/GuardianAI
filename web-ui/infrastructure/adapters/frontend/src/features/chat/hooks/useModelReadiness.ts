import { useEffect, useState } from "react";

import type { ChatApplicationService } from "../application/chatApplicationService";
import type { ModelReadinessStatus } from "../types";
import {
  INITIAL_MODEL_READINESS_STATUS,
  MODEL_READINESS_POLL_INTERVAL_MS,
} from "./chatWorkspaceUtils";

export function useModelReadiness(
  service: ChatApplicationService,
): ModelReadinessStatus {
  const [modelReadiness, setModelReadiness] = useState<ModelReadinessStatus>(
    INITIAL_MODEL_READINESS_STATUS,
  );

  useEffect(() => {
    let isActive = true;
    let timeoutId: number | null = null;

    async function refreshModelReadiness(): Promise<void> {
      try {
        const readiness = await service.getModelReadiness();
        if (!isActive) {
          return;
        }

        setModelReadiness(readiness);

        if (!readiness.ready) {
          timeoutId = window.setTimeout(
            refreshModelReadiness,
            MODEL_READINESS_POLL_INTERVAL_MS,
          );
        }
      } catch {
        if (!isActive) {
          return;
        }

        setModelReadiness({
          ready: false,
          message: "Esperando a que arranque el proveedor de modelos...",
        });
        timeoutId = window.setTimeout(
          refreshModelReadiness,
          MODEL_READINESS_POLL_INTERVAL_MS,
        );
      }
    }

    void refreshModelReadiness();

    return () => {
      isActive = false;
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [service]);

  return modelReadiness;
}
