import * as FileSystem from "expo-file-system";

export async function readRoomPlanJson(jsonUrl?: string): Promise<string> {
  if (!jsonUrl?.trim()) throw new Error("RoomPlan did not return a JSON file URL.");
  const uri = /^[a-z][a-z\d+.-]*:/i.test(jsonUrl) ? jsonUrl : `file://${jsonUrl}`;
  try {
    const contents = await FileSystem.readAsStringAsync(uri);
    JSON.parse(contents);
    return contents;
  } catch (error) {
    const reason = error instanceof Error ? error.message : "unknown file error";
    throw new Error(`Could not read or parse exported RoomPlan JSON: ${reason}`);
  }
}
