import React, { useEffect, useRef, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import fixture from "./fixtures/mock-roomplan.json";
import { RoomPlanExport, ScannerSurfaceProps } from "./scannerTypes";

export function isScannerAvailable() { return true; }

export default function ScannerSurface({ active, sessionId, finishTrigger, onStatus, onExported }: ScannerSurfaceProps) {
  const [capturedSession, setCapturedSession] = useState<number | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const session = useRef(sessionId);

  useEffect(() => {
    session.current = sessionId;
    if (!active) return;
    timer.current = setTimeout(() => {
      if (session.current === sessionId) setCapturedSession(sessionId);
    }, 700);
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [active, sessionId]);

  useEffect(() => {
    if (!active || finishTrigger === undefined) return;
    timer.current = setTimeout(() => {
      if (session.current !== sessionId) return;
      onExported({ jsonText: JSON.stringify(fixture, null, 2), source: "web-mock" } satisfies RoomPlanExport, sessionId);
      onStatus("OK", undefined, sessionId);
    }, 350);
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [active, finishTrigger, onExported, onStatus, sessionId]);

  if (!active) return null;
  const mockState = finishTrigger !== undefined
    ? "Exporting synthetic RoomPlan JSON…"
    : capturedSession === sessionId
      ? "Room surfaces and objects captured (synthetic)."
      : "Mock scan active. Finish, cancel, or simulate an error.";
  return <View style={styles.mock}>
    <Text style={styles.heading}>Browser mock scanner</Text>
    <Text style={styles.body}>{mockState}</Text>
    <Text style={styles.body}>No camera or LiDAR is accessed. Output is visibly marked as synthetic.</Text>
    <Pressable accessibilityRole="button" style={styles.failure} onPress={() => onStatus("Error", "Simulated mock scan failure. Start a new scan to retry.", sessionId)}>
      <Text style={styles.failureText}>Simulate scan failure</Text>
    </Pressable>
  </View>;
}

const styles = StyleSheet.create({
  mock: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12, padding: 36, borderWidth: 1, borderColor: "#53634f", borderRadius: 16 },
  heading: { color: "#b8f16b", fontSize: 22, fontWeight: "700" },
  body: { color: "#e1e8dc", textAlign: "center", lineHeight: 22 },
  failure: { padding: 12, borderWidth: 1, borderColor: "#a86b62", borderRadius: 10 },
  failureText: { color: "#ffc4b8", fontWeight: "700" },
});
