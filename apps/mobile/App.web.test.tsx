import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";
import App from "./App";

jest.mock("react-native-safe-area-context", () => ({
  SafeAreaProvider: ({ children }: { children: React.ReactNode }) => children,
  SafeAreaView: jest.requireActual<typeof import("react-native")>("react-native").View,
}));
jest.mock("./src/roomplan/ScannerSurface", () => jest.requireActual("./src/roomplan/ScannerSurface.web"));
jest.mock("./src/roomplan/readExportJson", () => jest.requireActual("./src/roomplan/readExportJson.web"));
jest.mock("./src/roomplan/shareJson", () => ({ shareOrDownloadJson: jest.fn() }));

describe("browser scanner workflow", () => {
  it("can cancel, simulate failure, retry, and inspect a synthetic JSON export", async () => {
    const screen = render(<App />);
    fireEvent.press(screen.getByRole("button", { name: "Start scan" }));
    fireEvent.press(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByText("Scan canceled.")).toBeTruthy();

    fireEvent.press(screen.getByRole("button", { name: "Start scan" }));
    fireEvent.press(screen.getByRole("button", { name: "Simulate scan failure" }));
    expect(screen.getByText("Simulated mock scan failure. Start a new scan to retry.")).toBeTruthy();

    fireEvent.press(screen.getByRole("button", { name: "Start scan" }));
    fireEvent.press(screen.getByRole("button", { name: "Finish scan" }));
    await waitFor(() => expect(screen.getByText("SYNTHETIC MOCK ROOMPLAN JSON")).toBeTruthy());
    expect(screen.getByText(/"category": "sofa"/)).toBeTruthy();
    expect(screen.getByText(/not authentic Apple output/i)).toBeTruthy();
  });
});
