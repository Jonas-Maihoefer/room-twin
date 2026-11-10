import { parseRoomPlanJson } from "./files";
import { RoomPlanExport } from "./scannerTypes";

export async function readExportJson(files: RoomPlanExport): Promise<string> {
  if (files.source !== "web-mock" || !files.jsonText) throw new Error("The browser mock did not provide structured JSON.");
  return parseRoomPlanJson(files.jsonText);
}
