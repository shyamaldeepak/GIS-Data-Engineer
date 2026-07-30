import type { ServerMessage } from "../types";

type Handler = (message: ServerMessage) => void;

/** Owns a single WebSocket connection with exponential-backoff reconnect. */
export class LiveSocket {
  private ws: WebSocket | null = null;
  private attempt = 0;
  private stopped = false;

  constructor(
    private readonly url: string,
    private readonly onMessage: Handler,
    private readonly onStatusChange: (status: "connecting" | "connected" | "disconnected") => void,
  ) {}

  connect(): void {
    this.stopped = false;
    this.open();
  }

  private open(): void {
    this.onStatusChange("connecting");
    const ws = new WebSocket(this.url);
    this.ws = ws;

    ws.onopen = () => {
      this.attempt = 0;
      this.onStatusChange("connected");
    };

    ws.onmessage = (event) => {
      try {
        this.onMessage(JSON.parse(event.data) as ServerMessage);
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      this.onStatusChange("disconnected");
      if (this.stopped) return;
      const delay = Math.min(1000 * 2 ** this.attempt, 15000);
      this.attempt += 1;
      setTimeout(() => this.open(), delay);
    };

    ws.onerror = () => ws.close();
  }

  close(): void {
    this.stopped = true;
    this.ws?.close();
  }
}
