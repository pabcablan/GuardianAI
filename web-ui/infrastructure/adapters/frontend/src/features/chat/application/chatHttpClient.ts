export class ChatHttpClient {
  constructor(private readonly apiBaseUrl: string) {}

  async getJson<T>(path: string): Promise<T> {
    const response = await fetch(`${this.apiBaseUrl}${path}`);
    await this.ensureSuccess(response);
    return (await response.json()) as T;
  }

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

  async delete(path: string): Promise<void> {
    const response = await fetch(`${this.apiBaseUrl}${path}`, {
      method: "DELETE",
    });
    await this.ensureSuccess(response);
  }

  async getBlob(path: string): Promise<Blob> {
    const response = await fetch(`${this.apiBaseUrl}${path}`);
    await this.ensureSuccess(response);
    return await response.blob();
  }

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
