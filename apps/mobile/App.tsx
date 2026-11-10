import React, { useCallback, useMemo, useState } from "react";
import { ActivityIndicator, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";
import * as FileSystem from "expo-file-system";
import * as Sharing from "expo-sharing";
import { loadRoomPlanPackage, RoomPlanExport, RoomPlanStatus, useRoomPlanCallbacks } from "./src/roomplan/bridge";
import { readRoomPlanJson } from "./src/roomplan/files";

type Phase = "idle" | "scanning" | "exporting" | "reading" | "ready" | "error" | "canceled";

export default function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [message, setMessage] = useState("Ready to scan. Use a physical RoomPlan-compatible LiDAR iPhone or iPad.");
  const [json, setJson] = useState<string | null>(null);
  const [scanUrl, setScanUrl] = useState<string | null>(null);
  const [finishTrigger, setFinishTrigger] = useState<number | undefined>();
  const [showScanner, setShowScanner] = useState(false);
  const pkg = useMemo(() => loadRoomPlanPackage(), []);
  const nativeAvailable = Boolean(pkg?.RoomPlanView);

  const onStatus = useCallback((status: RoomPlanStatus, error?: string) => {
    if (status === "OK") {
      setPhase("exporting");
      setMessage("Scan finished. Waiting for the RoomPlan JSON export…");
    } else if (status === "Canceled") {
      setPhase("canceled");
      setShowScanner(false);
      setMessage("Scan canceled. No files were sent to the backend.");
    } else {
      setPhase("error");
      setShowScanner(false);
      setMessage(error || "RoomPlan could not start. Check camera permission and device compatibility.");
    }
  }, []);

  const onExported = useCallback(async (files: RoomPlanExport) => {
    setShowScanner(false);
    setPhase("reading");
    if (files.scanUrl) setScanUrl(files.scanUrl);
    try {
      const content = await readRoomPlanJson(files.jsonUrl);
      setJson(content);
      setPhase("ready");
      setMessage("RoomPlan JSON loaded on device. The Room Twin API conversion and upload contract remain separate.");
    } catch (error) {
      setPhase("error");
      setMessage(error instanceof Error ? error.message : "RoomPlan export failed.");
    }
  }, []);

  const callbacks = useRoomPlanCallbacks({ onStatus, onExported });
  const start = () => {
    setJson(null);
    setScanUrl(null);
    setMessage("Starting RoomPlan. Grant camera access if prompted.");
    setPhase("scanning");
    setShowScanner(true);
  };
  const cancel = () => {
    setShowScanner(false);
    setPhase("canceled");
    setMessage("Scan canceled.");
  };
  const shareJson = async () => {
    if (!json) return;
    try {
      if (!FileSystem.documentDirectory) throw new Error("App document storage is unavailable.");
      const target = `${FileSystem.documentDirectory}room-twin-roomplan.json`;
      await FileSystem.writeAsStringAsync(target, json);
      await Sharing.shareAsync(target, { mimeType: "application/json", dialogTitle: "Share RoomPlan JSON" });
    } catch (error) {
      setMessage(error instanceof Error ? `Could not share the JSON file: ${error.message}` : "Could not share the JSON file.");
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.eyebrow}>ROOM TWIN · FOUNDATION</Text>
        <Text style={styles.title}>Room scan</Text>
        <Text style={styles.copy}>Capture structured room data with Apple RoomPlan. This screen checks the native export path before any product workflow is built.</Text>
        <Text style={styles.apiTarget}>Configured API: {process.env.EXPO_PUBLIC_API_BASE_URL || "not set"} · uploads are not implemented yet</Text>
        <View style={styles.card}>
          <Text style={styles.label}>SCAN STATUS</Text>
          {phase === "reading" || phase === "exporting" ? <ActivityIndicator color="#b8f16b" /> : null}
          <Text accessibilityLiveRegion="polite" style={styles.message}>{message}</Text>
          {!nativeAvailable ? <Text style={styles.note}>Native RoomPlan module is unavailable in this runtime. Install the EAS development build; Expo Go cannot load this native module.</Text> : null}
          {showScanner ? <View style={styles.actions}>
            <Pressable style={styles.secondaryButton} onPress={cancel}><Text style={styles.buttonText}>Cancel</Text></Pressable>
            <Pressable style={styles.button} onPress={() => { setPhase("exporting"); setMessage("Finishing scan and waiting for Apple’s preview and JSON export…"); setFinishTrigger(Date.now()); }}><Text style={styles.buttonText}>Finish scan</Text></Pressable>
          </View> : <Pressable disabled={!nativeAvailable} style={[styles.button, !nativeAvailable && styles.disabled]} onPress={start}><Text style={styles.buttonText}>Start scan</Text></Pressable>}
        </View>
        {json ? <View style={styles.card}>
          <Text style={styles.label}>EXPORTED APPLE ROOMPLAN JSON</Text>
          <Text style={styles.note}>{json.length.toLocaleString()} characters loaded. Source JSON is shown as-is and is not the Room Twin API payload.</Text>
          {scanUrl ? <Text style={styles.path} numberOfLines={2}>USDZ: {scanUrl}</Text> : null}
          <Pressable style={styles.secondaryButton} onPress={shareJson}><Text style={styles.buttonText}>Share JSON file</Text></Pressable>
          <Text style={styles.preview} selectable numberOfLines={18}>{JSON.stringify(JSON.parse(json), null, 2)}</Text>
        </View> : null}
      </ScrollView>
      {showScanner && pkg?.RoomPlanView ? <View style={styles.scanOverlay}>
        {React.createElement(pkg.RoomPlanView as React.ComponentType<any>, {
          style: StyleSheet.absoluteFillObject,
          scanName: "RoomTwinScan",
          exportType: pkg.ExportType?.Parametric,
          sendFileLoc: true,
          exportOnFinish: true,
          running: true,
          finishTrigger,
          ...callbacks,
        })}
        <SafeAreaView style={styles.overlayActions}>
          <Pressable style={styles.secondaryButton} onPress={cancel}><Text style={styles.buttonText}>Cancel</Text></Pressable>
          <Pressable style={styles.button} onPress={() => { setPhase("exporting"); setMessage("Finishing scan and waiting for Apple’s preview and JSON export…"); setFinishTrigger(Date.now()); }}><Text style={styles.buttonText}>Finish scan</Text></Pressable>
        </SafeAreaView>
      </View> : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#101511" },
  content: { padding: 24, gap: 18 },
  eyebrow: { color: "#b8f16b", fontSize: 12, letterSpacing: 2, fontWeight: "700", marginTop: 20 },
  title: { color: "#f5f4ec", fontSize: 34, fontWeight: "700" },
  copy: { color: "#b3b9b0", fontSize: 16, lineHeight: 23 },
  apiTarget: { color: "#8c9a8e", fontSize: 12 },
  card: { backgroundColor: "#1c241e", borderRadius: 18, padding: 18, gap: 14 },
  label: { color: "#b8f16b", fontWeight: "700", fontSize: 11, letterSpacing: 1.4 },
  message: { color: "#f5f4ec", fontSize: 16, lineHeight: 23 },
  note: { color: "#aab2a9", fontSize: 13, lineHeight: 19 },
  path: { color: "#8c9a8e", fontSize: 11 },
  button: { backgroundColor: "#b8f16b", padding: 15, borderRadius: 12, alignItems: "center", minWidth: 130 },
  disabled: { opacity: 0.4 },
  secondaryButton: { borderColor: "#62705f", borderWidth: 1, padding: 14, borderRadius: 12, alignItems: "center" },
  buttonText: { color: "#101511", fontWeight: "700" },
  actions: { flexDirection: "row", gap: 12, justifyContent: "space-between" },
  scanOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: "#101511" },
  overlayActions: { position: "absolute", top: 16, left: 20, right: 20, flexDirection: "row", justifyContent: "space-between" },
  preview: { color: "#cfdbc9", backgroundColor: "#111713", padding: 12, borderRadius: 10, fontFamily: "monospace", fontSize: 11 },
});
