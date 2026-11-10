import * as FileSystem from "expo-file-system/legacy";
import { readExportJson } from "./readExportJson.ios";

jest.mock("expo-file-system/legacy", () => ({ readAsStringAsync: jest.fn() }));

describe("native RoomPlan file export validation", () => {
  const files = { source: "apple-roomplan" as const };

  it("reports a missing JSON URL", async () => {
    await expect(readExportJson(files)).rejects.toThrow("did not return a JSON file URL");
  });

  it("reports read failures and invalid JSON", async () => {
    jest.mocked(FileSystem.readAsStringAsync).mockRejectedValue(new Error("file unavailable"));
    await expect(readExportJson({ ...files, jsonUrl: "file:///capture.json" })).rejects.toThrow("Could not read or parse");

    jest.mocked(FileSystem.readAsStringAsync).mockResolvedValue("not-json");
    await expect(readExportJson({ ...files, jsonUrl: "file:///capture.json" })).rejects.toThrow("Could not read or parse");
  });
});
