export function parseRoomPlanJson(contents: string): string {
  try {
    JSON.parse(contents);
    return contents;
  } catch (error) {
    throw new Error(`Invalid RoomPlan JSON: ${error instanceof Error ? error.message : "unknown parse error"}`);
  }
}
