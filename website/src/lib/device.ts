// The real dynamometer over USB, read by the browser itself (Web Serial: Chrome / Edge on a computer).
// Firmware facts: 115200 baud, prints "t_ms,raw,net,force_kg", re-zeroes on "T" and replies "# tared".
// Opening the port restarts the Nano, which tares itself on boot, so we wait for its first data line.

import { parseCalibrationComment, parseLine } from "./parse";
import { BAUD } from "./protocol";

export const serialSupported = () => typeof navigator !== "undefined" && "serial" in navigator;

type LineListener = (line: string) => void;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class GripDevice {
  private port: SerialPort;
  private reader: ReadableStreamDefaultReader<string> | null = null;
  private listeners = new Set<LineListener>();
  private closed = false;
  /** Set by the firmware's "# calibration=..." boot comment, if we saw it. */
  calibration: "measured" | "estimated" | null = null;
  /** Called once if the cable is pulled or the port fails. */
  onLost: (() => void) | null = null;
  lastForceKg = 0;

  private constructor(port: SerialPort) {
    this.port = port;
  }

  /** Ask the user to pick the port, open it, and wait until data arrive. */
  static async connect(onStatus?: (text: string) => void): Promise<GripDevice> {
    const port = await navigator.serial.requestPort();
    await port.open({ baudRate: BAUD });
    const device = new GripDevice(port);
    device.startReading();
    onStatus?.("Starting the device (it restarts when connected)...");
    const ok = await device.waitFor((line) => parseLine(line) !== null, 6000);
    if (!ok) {
      await device.close();
      throw new Error(
        "No data from the device. Check that the GripCheck firmware is uploaded, and close the Arduino Serial Monitor (only one program can use the port).",
      );
    }
    navigator.serial.addEventListener("disconnect", device.handleDisconnect);
    return device;
  }

  private handleDisconnect = (e: Event) => {
    if (e.target === this.port) this.lost();
  };

  private lost() {
    if (this.closed) return;
    this.closed = true;
    this.onLost?.();
  }

  private async startReading() {
    const decoder = new TextDecoderStream();
    this.port.readable!.pipeTo(decoder.writable as WritableStream<Uint8Array>).catch(() => {});
    this.reader = decoder.readable.getReader();
    let buffer = "";
    try {
      for (;;) {
        const { value, done } = await this.reader.read();
        if (done) break;
        buffer += value;
        let cut: number;
        while ((cut = buffer.indexOf("\n")) >= 0) {
          const line = buffer.slice(0, cut).trim();
          buffer = buffer.slice(cut + 1);
          this.handleLine(line);
        }
      }
    } catch {
      this.lost();
    }
  }

  private handleLine(line: string) {
    const cal = parseCalibrationComment(line);
    if (cal) this.calibration = cal;
    const p = parseLine(line);
    if (p) this.lastForceKg = p.f;
    for (const fn of this.listeners) fn(line);
  }

  /** Listen to every line. Returns a function that stops listening. */
  subscribe(fn: LineListener): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  /** Resolve true when a line matches, false after the timeout. */
  waitFor(match: (line: string) => boolean, timeoutMs: number): Promise<boolean> {
    return new Promise((resolve) => {
      const stop = this.subscribe((line) => {
        if (match(line)) {
          stop();
          clearTimeout(timer);
          resolve(true);
        }
      });
      const timer = setTimeout(() => {
        stop();
        resolve(false);
      }, timeoutMs);
    });
  }

  async send(text: string) {
    const writer = this.port.writable!.getWriter();
    try {
      await writer.write(new TextEncoder().encode(text));
    } finally {
      writer.releaseLock();
    }
  }

  /** Zero the scale. Nothing may touch the handle. The firmware averages 20 samples (~2 s at 10 Hz). */
  async tare() {
    await this.send("T");
    const confirmed = await this.waitFor((line) => line.startsWith("# tared"), 5000);
    if (!confirmed) await sleep(500); // older firmware without the reply: the fixed wait has passed
  }

  /** Collect raw lines for a number of seconds. onLine sees each line as it arrives (for the live graph). */
  async record(seconds: number, onLine: LineListener, isCancelled: () => boolean): Promise<string[]> {
    const lines: string[] = [];
    const stop = this.subscribe((line) => {
      lines.push(line);
      onLine(line);
    });
    const started = performance.now();
    try {
      while (performance.now() - started < seconds * 1000) {
        if (this.closed) throw new Error("The device was unplugged.");
        if (isCancelled()) break;
        await sleep(50);
      }
    } finally {
      stop();
    }
    return lines;
  }

  get connected() {
    return !this.closed;
  }

  async close() {
    this.closed = true;
    navigator.serial?.removeEventListener("disconnect", this.handleDisconnect);
    try {
      await this.reader?.cancel();
    } catch {
      /* already closed */
    }
    try {
      await this.port.close();
    } catch {
      /* already closed */
    }
  }
}
