import React, { useCallback, useEffect, useRef } from "react";
import { StyleSheet, Text, View } from "react-native";
import { RoomPlanExport, ScannerSurfaceProps } from "./scannerTypes";

type RoomPlanLibrary = {
  RoomPlanView: React.ComponentType<any>;
  ExportType?: { Parametric?: unknown };
  useRoomPlanView: (options: Record<string, unknown>) => {
    viewProps: Record<string, unknown>;
    controls: { start: () => void; cancel: () => void; finishScan: () => void };
  };
};

function loadNativeLibrary(): RoomPlanLibrary | null {
  try {
    // Resolve lazily so Expo Go or a malformed native build can render an actionable unavailable state.
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    return require("expo-roomplan") as RoomPlanLibrary;
  } catch {
    return null;
  }
}

const nativeLibrary = loadNativeLibrary();

export function isScannerAvailable() { return Boolean(nativeLibrary?.RoomPlanView); }

export default function ScannerSurface(props: ScannerSurfaceProps) {
  if (!nativeLibrary) {
    return props.active ? <View style={styles.unavailable}>
      <Text style={styles.unavailableText}>Native RoomPlan is unavailable. Install the Room Twin iOS development build on a supported device.</Text>
    </View> : null;
  }
  return <NativeScannerSurface {...props} library={nativeLibrary} />;
}

function NativeScannerSurface({ active, sessionId, finishTrigger, onStatus, onExported, library }: ScannerSurfaceProps & { library: RoomPlanLibrary }) {
  const session = useRef(sessionId);
  const callbacks = useRef({ onStatus, onExported });
  useEffect(() => { callbacks.current = { onStatus, onExported }; }, [onStatus, onExported]);
  const onNativeStatus = useCallback((event: { nativeEvent?: { status?: string; errorMessage?: string } }) => {
    const { status, errorMessage } = event.nativeEvent ?? {};
    const mapped = status === "OK" || status === "Canceled" || status === "Error" ? status : "Error";
    callbacks.current.onStatus(mapped, errorMessage || (mapped === "Error" ? `Unexpected RoomPlan status: ${status ?? "missing"}` : undefined), session.current);
  }, []);
  const onNativeExport = useCallback((event: { nativeEvent?: { scanUrl?: string; jsonUrl?: string } }) => {
    callbacks.current.onExported({ ...(event.nativeEvent ?? {}), source: "apple-roomplan" } satisfies RoomPlanExport, session.current);
  }, []);
  const { viewProps, controls: roomPlanControls } = library.useRoomPlanView({
    scanName: "RoomTwinScan",
    exportType: library.ExportType?.Parametric,
    sendFileLoc: true,
    exportOnFinish: true,
    autoCloseOnTerminalStatus: true,
    onStatus: onNativeStatus,
    onExported: onNativeExport,
  });
  const { start, cancel, finishScan } = roomPlanControls;

  useEffect(() => {
    if (active) {
      session.current = sessionId;
      start();
    } else {
      // Keep the native view mounted until the controller passes running=false to RoomPlanView.
      // This stops capture explicitly and permits a clean subsequent session.
      cancel();
    }
  }, [active, sessionId, start, cancel]);

  useEffect(() => {
    if (active && finishTrigger !== undefined) finishScan();
  }, [active, finishTrigger, finishScan]);

  return <View pointerEvents={active ? "auto" : "none"} style={active ? styles.active : styles.hidden}>
    <library.RoomPlanView style={StyleSheet.absoluteFill} {...viewProps} />
  </View>;
}

const styles = StyleSheet.create({
  active: { ...StyleSheet.absoluteFill, zIndex: 10 },
  hidden: { display: "none" },
  unavailable: { ...StyleSheet.absoluteFill, zIndex: 10, backgroundColor: "#101511", justifyContent: "center", padding: 28 },
  unavailableText: { color: "#f5f4ec", textAlign: "center", fontSize: 16, lineHeight: 24 },
});
