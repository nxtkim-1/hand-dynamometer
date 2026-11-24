// The real dynamometer over USB, read by the browser itself (Web Serial: Chrome / Edge on a computer).
// Firmware facts: 115200 baud, prints "t_ms,raw,net,force_kg", re-zeroes on "T" and replies "# tared".
// Opening the port restarts the Nano, which tares itself on boot, so we wait for its first data line.

import { emptyDeviceInfo, NEGATIVE_WARN_KG, parseCalibrationComment, parseDeviceInfo, parseLine, reverseLine, type DeviceInfo } from "./parse";
import { BAUD } from "./protocol";

export const serialSupported = () => typeof navigator !== "undefined" && "serial" in navigator;

// Which way the load cell sits depends on the frame: SIGN = -1 was right for the v3 barrel, but a frame
// that bends the cell the other way reads negative on a squeeze. Reversing here is the same as flipping
// SIGN in the firmware, without re-uploading it. Remembered in this browser only.
const REVERSE_KEY = "gripcheck.reverseDirection";

export function getStoredReverse(): boolean {
  try {
    return localStorage.getItem(REVERSE_KEY) === "1";
  } catch {
    return false;
  }
}

export function setStoredReverse(on: boolean) {
  try {
    if (on) localStorage.setItem(REVERSE_KEY, "1");
    else localStorage.removeItem(REVERSE_KEY);
  } catch {
    /* private window: the setting lasts until the page closes */
  }
}

type LineListener = (line: string) => void;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class GripDevice {
  private port: SerialPort;
  private reader: ReadableStreamDefaultReader<string> | null = null;
  private listeners = new Set<LineListener>();
  private closed = false;
  /** Set by the firmware's "# calibration=..." boot comment, if we saw it. */
  calibration: "measured" | "estimated" | null = null;
  /** Everything the firmware has said about itself (version, counts per kg, sign); v1.1 and later. */
  info: DeviceInfo = emptyDeviceInfo();
  /** Listeners that get each line before the browser-side reverse (the device's own sign). */
  private rawListeners = new Set<LineListener>();
  /** Called once if the cable is pulled or the port fails. */
  onLost: (() => void) | null = null;
  lastForceKg = 0;
  /** Flip net and force on every data line (see REVERSE_KEY). */
  private reversedFlag = getStoredReverse();
  /** True once a reading has gone clearly below zero since the last zero or direction change. */
  negativeSeen = false;

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

  private handleLine(rawLine: string) {
    const cal = parseCalibrationComment(rawLine);
    if (cal) this.calibration = cal;
    const info = parseDeviceInfo(rawLine);
    if (Object.keys(info).length) this.info = { ...this.info, ...info };
    for (const fn of this.rawListeners) fn(rawLine);
    // every listener (live graph, recording, saved CSV) sees the corrected line
    const line = this.reversedFlag ? reverseLine(rawLine) : rawLine;
    const p = parseLine(line);
    if (p) {
      this.lastForceKg = p.f;
      if (p.f < NEGATIVE_WARN_KG) this.negativeSeen = true;
    }
    for (const fn of this.listeners) fn(line);
  }

  get reversed() {
    return this.reversedFlag;
  }

  set reversed(on: boolean) {
    if (on === this.reversedFlag) return;
    this.reversedFlag = on;
    this.negativeSeen = false;
    this.lastForceKg = -this.lastForceKg;
  }

  /** Listen to every line. Returns a function that stops listening. */
  subscribe(fn: LineListener): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  /** Listen to every line as the device sent it, before the browser-side reverse. */
  subscribeRaw(fn: LineListener): () => void {
    this.rawListeners.add(fn);
    return () => this.rawListeners.delete(fn);
  }

  /** Send a command and wait for the firmware's "# saved ..." or "# error ..." reply. */
  private async command(text: string, okPrefix: string, timeoutMs = 4000): Promise<{ ok: boolean; reply: string | null }> {
    let reply: string | null = null;
    const got = this.waitFor((line) => {
      if (line.startsWith(okPrefix) || line.startsWith("# error")) {
        reply = line;
        return true;
      }
      return false;
    }, timeoutMs);
    await this.send(text);
    const seen = await got;
    const r = reply as string | null;
    return { ok: seen && r !== null && r.startsWith(okPrefix), reply: r };
  }

  /** Ask the firmware to print its settings. False means it is older than v1.1 (no Calibrate support). */
  async requestInfo(): Promise<boolean> {
    const got = this.waitFor((line) => /^#\s*counts_per_kg\s*=/.test(line), 2500);
    await this.send("I");
    return got;
  }

  /** Store a measured counts-per-kg in the device (EEPROM). Needs firmware v1.1. */
  async saveCalibration(countsPerKg: number, yyyymmdd: string) {
    const res = await this.command(`C ${countsPerKg.toFixed(1)} ${yyyymmdd}\n`, "# saved counts_per_kg");
    if (res.ok) await this.waitFor((line) => line.startsWith("# calibration="), 1500);
    return res;
  }

  /** Store the direction in the device, so a squeeze reads positive without the browser-side reverse. */
  async saveSign(sign: 1 | -1) {
    const res = await this.command(`S ${sign}\n`, "# saved sign");
    if (res.ok) {
      this.info = { ...this.info, sign };
      this.negativeSeen = false;
    }
    return res;
  }

  /** Back to the datasheet estimate and the default sign. */
  async resetCalibration() {
    const res = await this.command("R\n", "# saved defaults");
    if (res.ok) await this.waitFor((line) => line.startsWith("# calibration="), 1500);
    return res;
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
    this.negativeSeen = false;
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
