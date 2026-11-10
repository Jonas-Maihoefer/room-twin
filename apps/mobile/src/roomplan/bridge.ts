import { useMemo } from "react";

/** App-facing boundary for the version-specific expo-roomplan surface. */
export type RoomPlanStatus = "OK" | "Canceled" | "Error" | "Unavailable";
export type RoomPlanExport = { scanUrl?: string; jsonUrl?: string };
export type RoomPlanCallbacks = {
  onStatus: (status: RoomPlanStatus, message?: string) => void;
  onExported: (files: RoomPlanExport) => void;
};

type RoomPlanPackage = {
  RoomPlanView?: unknown;
  ExportType?: { Parametric?: unknown };
};

/** Lazy loading lets the app explain that Expo Go lacks this native module. */
export function loadRoomPlanPackage(): RoomPlanPackage | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    return require("expo-roomplan") as RoomPlanPackage;
  } catch {
    return null;
  }
}

export function useRoomPlanCallbacks(callbacks: RoomPlanCallbacks) {
  return useMemo(
    () => ({
      onStatus: (event: { nativeEvent?: { status?: string; errorMessage?: string } }) => {
        const status = event.nativeEvent?.status;
        if (status === "OK" || status === "Canceled" || status === "Error") {
          callbacks.onStatus(status, event.nativeEvent?.errorMessage);
        } else if (status) {
          callbacks.onStatus("Error", `Unexpected RoomPlan status: ${status}`);
        }
      },
      onExported: (event: { nativeEvent?: RoomPlanExport }) => {
        callbacks.onExported(event.nativeEvent ?? {});
      },
    }),
    [callbacks],
  );
}
