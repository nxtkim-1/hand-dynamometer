// One device connection for the whole site, so moving between pages does not drop the USB link.

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { getStoredReverse, GripDevice, serialSupported, setStoredReverse } from "../lib/device";

type Status = "unsupported" | "idle" | "connecting" | "connected" | "error";

interface DeviceState {
  device: GripDevice | null;
  status: Status;
  message: string;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  /** Readings are sign-flipped in the browser (the cell sits the other way round in this frame). */
  reversed: boolean;
  setReversed: (on: boolean) => void;
}

const Ctx = createContext<DeviceState | null>(null);

export function DeviceProvider({ children }: { children: ReactNode }) {
  const [device, setDevice] = useState<GripDevice | null>(null);
  const [status, setStatus] = useState<Status>(serialSupported() ? "idle" : "unsupported");
  const [message, setMessage] = useState("");
  const deviceRef = useRef<GripDevice | null>(null);
  const [reversed, setReversedState] = useState(getStoredReverse);

  const setReversed = useCallback((on: boolean) => {
    setStoredReverse(on);
    setReversedState(on);
    if (deviceRef.current) deviceRef.current.reversed = on;
  }, []);

  const connect = useCallback(async () => {
    setStatus("connecting");
    setMessage("Choose the dynamometer in the browser's list (usually “USB-SERIAL CH340” or “Arduino”).");
    try {
      const d = await GripDevice.connect(setMessage);
      d.onLost = () => {
        deviceRef.current = null;
        setDevice(null);
        setStatus("error");
        setMessage("The device was disconnected. Check the USB cable and connect again.");
      };
      deviceRef.current = d;
      setDevice(d);
      setStatus("connected");
      setMessage("Connected. Your squeezes will be measured, not simulated.");
    } catch (err) {
      const e = err as Error;
      if (e.name === "NotFoundError") {
        setStatus("idle"); // the user closed the port picker
        setMessage("");
      } else {
        setStatus("error");
        setMessage(
          e.name === "NetworkError" || e.name === "InvalidStateError"
            ? "The port is busy. Close the Arduino Serial Monitor (or any other program using it) and try again."
            : e.message,
        );
      }
    }
  }, []);

  const disconnect = useCallback(async () => {
    const d = deviceRef.current;
    deviceRef.current = null;
    setDevice(null);
    setStatus("idle");
    setMessage("");
    await d?.close();
  }, []);

  useEffect(() => () => void deviceRef.current?.close(), []);

  return <Ctx.Provider value={{ device, status, message, connect, disconnect, reversed, setReversed }}>{children}</Ctx.Provider>;
}

export function useDevice(): DeviceState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useDevice must be used inside DeviceProvider");
  return v;
}

/** Latest force from the connected device, refreshed a few times per second (for idle meters). */
export function useLiveForce(device: GripDevice | null): number | null {
  const [kg, setKg] = useState<number | null>(null);
  useEffect(() => {
    if (!device) {
      setKg(null);
      return;
    }
    const id = setInterval(() => setKg(device.lastForceKg), 150);
    return () => clearInterval(id);
  }, [device]);
  return kg;
}

/** True while the device has recently read clearly below zero (reversed direction or a bad zero). */
export function useNegativeReading(device: GripDevice | null): boolean {
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    if (!device) {
      setSeen(false);
      return;
    }
    const id = setInterval(() => setSeen(device.negativeSeen), 300);
    return () => clearInterval(id);
  }, [device]);
  return seen;
}
