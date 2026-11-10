import { parseRoomPlanJson } from "./files";

describe("readRoomPlanJson", () => {
  it("preserves valid JSON", () => {
    const source = '{"walls":[{"dimensions":[2,3,0.1]}]}';
    expect(parseRoomPlanJson(source)).toBe(source);
  });

  it("reports invalid JSON", () => {
    expect(() => parseRoomPlanJson("not json")).toThrow("Invalid RoomPlan JSON");
  });
});
