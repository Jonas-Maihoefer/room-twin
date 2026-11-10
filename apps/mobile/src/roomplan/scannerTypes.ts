export type RoomPlanStatus = "OK" | "Canceled" | "Error" | "Unavailable";
export type RoomPlanExport = { scanUrl?: string; jsonUrl?: string; jsonText?: string; source: "apple-roomplan" | "web-mock" };

export type ScannerSurfaceProps = {
  active: boolean;
  sessionId: number;
  finishTrigger?: number;
  onStatus: (status: RoomPlanStatus, message?: string, sessionId?: number) => void;
  onExported: (files: RoomPlanExport, sessionId?: number) => void;
};
