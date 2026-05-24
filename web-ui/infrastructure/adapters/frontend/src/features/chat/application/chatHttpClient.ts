export class ChatHttpClient {
  constructor(private readonly apiBaseUrl: string) {}

  // Fetch one JSON payload with GET and type it at the call site.
  async getJson<T>(path: string): Promise<T> {
    const response = await fetch(`${this.apiBaseUrl}${path}`);
    await this.ensureSuccess(response);
    return (await response.json()) as T;
  }

  // Send one JSON body with POST and parse the JSON response.
  async postJson<T>(
    path: string,
    payload: unknown,
  ): Promise<T> {
    const response = await fetch(`${this.apiBaseUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    await this.ensureSuccess(response);
    return (await response.json()) as T;
  }

  // Send JSON with POST when the caller needs the raw Response, usually for streams.
  async postJsonForResponse(path: string, payload: unknown): Promise<Response> {
    const response = await fetch(`${this.apiBaseUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    await this.ensureSuccess(response);
    return response;
  }

  // Send multipart form data and keep the raw Response for streamed processing.
  async postFormForResponse(
    path: string,
    formData: FormData,
  ): Promise<Response> {
    const response = await fetch(`${this.apiBaseUrl}${path}`, {
      method: "POST",
      body: formData,
    });
    await this.ensureSuccess(response);
    return response;
  }

  // Send a partial JSON update with PATCH when no response body is needed.
  async patchJson(path: string, payload: unknown): Promise<void> {
    const response = await fetch(`${this.apiBaseUrl}${path}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    await this.ensureSuccess(response);
  }

  // Delete one backend resource and only fail if the HTTP status is not successful.
  async delete(path: string): Promise<void> {
    const response = await fetch(`${this.apiBaseUrl}${path}`, {
      method: "DELETE",
    });
    await this.ensureSuccess(response);
  }

  // Download one binary payload, used for files such as anonymized PDF previews.
  async getBlob(path: string): Promise<Blob> {
    const response = await fetch(`${this.apiBaseUrl}${path}`);
    await this.ensureSuccess(response);
    return await response.blob();
  }

  // Normalize failed HTTP responses into one frontend Error with the best detail available.
  private async ensureSuccess(response: Response): Promise<void> {
    if (response.ok) {
      return;
    }

    const fallbackMessage = `La petición falló con estado ${response.status}.`;
    let detailMessage = fallbackMessage;

    try {
      const payload = (await response.json()) as { detail?: string };
      detailMessage = payload.detail ?? fallbackMessage;
    } catch {
      detailMessage = fallbackMessage;
    }

    throw new Error(detailMessage);
  }
}
