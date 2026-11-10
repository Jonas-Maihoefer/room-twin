import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";

export async function shareOrDownloadJson(json: string): Promise<void> {
  if (!FileSystem.documentDirectory) throw new Error("App document storage is unavailable.");
  const target = `${FileSystem.documentDirectory}room-twin-roomplan.json`;
  await FileSystem.writeAsStringAsync(target, json);
  await Sharing.shareAsync(target, { mimeType: "application/json", dialogTitle: "Share RoomPlan JSON" });
}
