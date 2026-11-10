import * as FileSystem from "expo-file-system/legacy";
import { parseRoomPlanJson } from "./files";
import { RoomPlanExport } from "./scannerTypes";

export async function readExportJson(files: RoomPlanExport): Promise<string> {
  if (!files.jsonUrl?.trim()) throw new Error("RoomPlan did not return a JSON file URL.");
  const uri = /^[a-z][a-z\d+.-]*:/i.test(files.jsonUrl) ? files.jsonUrl : `file://${files.jsonUrl}`;
  try {
    return parseRoomPlanJson(await FileSystem.readAsStringAsync(uri));
  } catch (error) {
    const reason = error instanceof Error ? error.message : "unknown file error";
    throw new Error(`Could not read or parse exported RoomPlan JSON: ${reason}`);
  }
}
