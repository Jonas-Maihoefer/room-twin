import React, { useCallback, useMemo, useRef, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import ScannerSurface, { isScannerAvailable } from "./src/roomplan/ScannerSurface";
import { readExportJson } from "./src/roomplan/readExportJson";
import { shareOrDownloadJson } from "./src/roomplan/shareJson";
import { RoomPlanExport, RoomPlanStatus } from "./src/roomplan/scannerTypes";

type Phase = "idle" | "scanning" | "exporting" | "reading" | "ready" | "error" | "canceled";

export default function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const phaseRef = useRef<Phase>("idle");
  const [message, setMessage] = useState("Ready to scan. On iOS, use a compatible LiDAR iPhone or iPad; on web, use the synthetic scanner.");
  const [json, setJson] = useState<string | null>(null);
  const [scanUrl, setScanUrl] = useState<string | null>(null);
  const [source, setSource] = useState<RoomPlanExport["source"] | null>(null);
  const [finishTrigger, setFinishTrigger] = useState<number | undefined>();
  const [showScanner, setShowScanner] = useState(false);
  const [sessionId, setSessionId] = useState(0);
  const activeSession = useRef(0);
  const scannerAvailable = useMemo(() => isScannerAvailable(), []);

  const setCurrentPhase = useCallback((next: Phase) => {
    phaseRef.current = next;
    setPhase(next);
  }, []);

  const onStatus = useCallback((status: RoomPlanStatus, error?: string, eventSession = activeSession.current) => {
    if (eventSession !== activeSession.current) return;
    if (phaseRef.current === "reading" || phaseRef.current === "ready") return;
    if (status === "OK") {
      // The export callback can precede a delayed terminal status; it must not regress reading or ready.
      setCurrentPhase("exporting");
      setMessage("Scan finished. Waiting for the structured JSON export…");
    } else if (status === "Canceled") {
      setShowScanner(false);
      setCurrentPhase("canceled");
      setMessage("Scan canceled. No files were sent to the backend.");
    } else {
      setShowScanner(false);
      setCurrentPhase("error");
      setMessage(error || "RoomPlan could not start. Check camera permission and device compatibility.");
    }
  }, [setCurrentPhase]);

  const onExported = useCallback(async (files: RoomPlanExport, eventSession = activeSession.current) => {
    if (eventSession !== activeSession.current || phaseRef.current === "canceled" || phaseRef.current === "error") return;
    setCurrentPhase("reading");
    setMessage("Validating exported JSON…");
    setSource(files.source);
    setScanUrl(files.scanUrl ?? null);
    try {
      const content = await readExportJson(files);
      if (eventSession !== activeSession.current) return;
      setJson(content);
      setCurrentPhase("ready");
      setShowScanner(false);
      setMessage(files.source === "web-mock"
        ? "Synthetic scan JSON is ready for inspection. It is not Apple RoomPlan output."
        : "RoomPlan JSON loaded on device. API conversion and upload remain separate.");
    } catch (error) {
      if (eventSession !== activeSession.current) return;
      setCurrentPhase("error");
      setShowScanner(false);
      setMessage(error instanceof Error ? error.message : "RoomPlan export failed.");
    }
  }, [setCurrentPhase]);

  const start = () => {
    const nextSession = activeSession.current + 1;
    activeSession.current = nextSession;
    setSessionId(nextSession);
    setJson(null);
    setScanUrl(null);
    setSource(null);
    setFinishTrigger(undefined);
    setMessage("Starting scanner. On iOS, grant camera access if prompted.");
    setCurrentPhase("scanning");
    setShowScanner(true);
  };
  const cancel = () => {
    const canceledSession = activeSession.current + 1;
    activeSession.current = canceledSession;
    setSessionId(canceledSession);
    setShowScanner(false);
    setCurrentPhase("canceled");
    setMessage("Scan canceled.");
  };
  const finish = () => {
    setCurrentPhase("exporting");
    setMessage("Finishing scan and preparing the JSON export…");
    setFinishTrigger(Date.now());
  };
  const shareJson = async () => {
    if (!json) return;
    try {
      await shareOrDownloadJson(json);
      setMessage(source === "web-mock" ? "Mock JSON download started." : "JSON share sheet opened.");
    } catch (error) {
      setMessage(error instanceof Error ? `Could not share the JSON file: ${error.message}` : "Could not share the JSON file.");
    }
  };

  return (
    <SafeAreaProvider>
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.eyebrow}>ROOM TWIN · DEVELOPMENT</Text>
        <Text style={styles.title}>Room scan</Text>
        <Text style={styles.copy}>Develop the shared scan workflow in a Windows browser with synthetic data. Native iOS uses Apple RoomPlan through an isolated adapter.</Text>
        <Text style={styles.apiTarget}>Configured API: {process.env.EXPO_PUBLIC_API_BASE_URL || "not set"} · uploads are not implemented</Text>
        <View style={styles.card}>
          <Text style={styles.label}>SCAN STATUS</Text>
          {phase === "reading" || phase === "exporting" ? <ActivityIndicator color="#b8f16b" /> : null}
          <Text accessibilityLiveRegion="polite" style={styles.message}>{message}</Text>
          {!scannerAvailable ? <Text style={styles.note}>Native RoomPlan is unavailable in this runtime. Install the signed iOS development client on a supported device.</Text> : null}
          {showScanner ? <View style={styles.actions}>
            <Pressable accessibilityRole="button" style={styles.secondaryButton} onPress={cancel}><Text style={styles.buttonText}>Cancel</Text></Pressable>
            <Pressable accessibilityRole="button" style={styles.button} onPress={finish}><Text style={styles.buttonText}>Finish scan</Text></Pressable>
          </View> : <Pressable accessibilityRole="button" disabled={!scannerAvailable} style={[styles.button, !scannerAvailable && styles.disabled]} onPress={start}><Text style={styles.buttonText}>Start scan</Text></Pressable>}
        </View>
        {json ? <View style={styles.card}>
          <Text style={styles.label}>{source === "web-mock" ? "SYNTHETIC MOCK ROOMPLAN JSON" : "APPLE ROOMPLAN JSON"}</Text>
          <Text style={styles.note}>{json.length.toLocaleString()} characters loaded. {source === "web-mock" ? "This fixture is not authentic Apple output." : "Source data is shown as-is."}</Text>
          {scanUrl ? <Text style={styles.path} numberOfLines={2}>USDZ: {scanUrl}</Text> : null}
          <Pressable accessibilityRole="button" style={styles.secondaryButton} onPress={shareJson}><Text style={styles.buttonText}>{source === "web-mock" ? "Download JSON" : "Share JSON file"}</Text></Pressable>
          <Text style={styles.preview} selectable>{JSON.stringify(JSON.parse(json), null, 2)}</Text>
        </View> : null}
      </ScrollView>
      <ScannerSurface active={showScanner} sessionId={sessionId} finishTrigger={finishTrigger} onStatus={onStatus} onExported={onExported} />
    </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#101511" },
  content: { padding: 24, gap: 18, maxWidth: 900, width: "100%", alignSelf: "center" },
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
  preview: { color: "#cfdbc9", backgroundColor: "#111713", padding: 12, borderRadius: 10, fontFamily: "monospace", fontSize: 11 },
});
