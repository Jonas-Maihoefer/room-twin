import * as FileSystem from "expo-file-system";
import { readRoomPlanJson } from "./files";

jest.mock("expo-file-system", () => ({ readAsStringAsync: jest.fn() }));

describe("readRoomPlanJson", () => {
  it("reads and preserves valid Apple JSON", async () => {
    const source = '{"walls":[{"dimensions":[2,3,0.1]}]}';
    jest.mocked(FileSystem.readAsStringAsync).mockResolvedValue(source);
    await expect(readRoomPlanJson("file:///capture.json")).resolves.toBe(source);
    expect(FileSystem.readAsStringAsync).toHaveBeenCalledWith("file:///capture.json");
  });

  it("reports a missing export URL", async () => {
    await expect(readRoomPlanJson(undefined)).rejects.toThrow("did not return a JSON file URL");
  });

  it("reports file read and invalid JSON failures", async () => {
    jest.mocked(FileSystem.readAsStringAsync).mockResolvedValue("not json");
    await expect(readRoomPlanJson("/capture.json")).rejects.toThrow("Could not read or parse");
  });
});
