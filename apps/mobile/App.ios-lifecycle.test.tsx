import React from "react";
import { act, fireEvent, render, waitFor } from "@testing-library/react-native";
import App from "./App";

let mockNativeSessions: {
  sessionId: number;
  active: boolean;
  finishTrigger?: number;
  onStatus: (status: "OK" | "Canceled" | "Error", message?: string, sessionId?: number) => void;
  onExported: (files: { jsonUrl?: string; source: "apple-roomplan" }, sessionId?: number) => void;
}[];
const mockReadExportJson = jest.fn();

jest.mock("react-native-safe-area-context", () => ({
  SafeAreaProvider: ({ children }: { children: React.ReactNode }) => children,
  SafeAreaView: jest.requireActual<typeof import("react-native")>("react-native").View,
}));
jest.mock("./src/roomplan/ScannerSurface", () => {
  const React = jest.requireActual<typeof import("react")>("react");
  const { Pressable, Text } = jest.requireActual<typeof import("react-native")>("react-native");
  return {
    __esModule: true,
    default: (props: (typeof mockNativeSessions)[number]) => {
      mockNativeSessions.push(props);
      return React.createElement(React.Fragment, null,
        React.createElement(Pressable, { accessibilityRole: "button", onPress: () => props.onStatus("OK", undefined, props.sessionId) }, React.createElement(Text, null, "Mock status OK")),
        React.createElement(Pressable, { accessibilityRole: "button", onPress: () => props.onExported({ jsonUrl: "file://scan.json", source: "apple-roomplan" }, props.sessionId) }, React.createElement(Text, null, "Mock export")),
      );
    },
    isScannerAvailable: () => true,
  };
});
jest.mock("./src/roomplan/readExportJson", () => ({ readExportJson: (...args: unknown[]) => mockReadExportJson(...args) }));
jest.mock("./src/roomplan/shareJson", () => ({ shareOrDownloadJson: jest.fn() }));

describe("iOS scan lifecycle controller", () => {
  beforeEach(() => {
    mockNativeSessions = [];
    mockReadExportJson.mockResolvedValue('{"rooms":[]}');
  });

  it("cancels and restarts with a new session; delayed status and export from the canceled session are ignored", async () => {
    const screen = render(<App />);
    fireEvent.press(screen.getByRole("button", { name: "Start scan" }));
    const oldSession = mockNativeSessions[mockNativeSessions.length - 1];
    fireEvent.press(screen.getByRole("button", { name: "Cancel" }));
    fireEvent.press(screen.getByRole("button", { name: "Start scan" }));
    const currentSession = mockNativeSessions[mockNativeSessions.length - 1];

    expect(currentSession.sessionId).not.toBe(oldSession.sessionId);
    expect(mockNativeSessions.some((session) => !session.active)).toBe(true);
    act(() => {
      oldSession.onStatus("Error", "late error", oldSession.sessionId);
      void oldSession.onExported({ jsonUrl: "file://old.json", source: "apple-roomplan" }, oldSession.sessionId);
    });
    expect(screen.getByText("Starting scanner. On iOS, grant camera access if prompted.")).toBeTruthy();

    await act(async () => {
      await currentSession.onExported({ jsonUrl: "file://current.json", source: "apple-roomplan" }, currentSession.sessionId);
      currentSession.onStatus("OK", undefined, currentSession.sessionId);
    });
    await waitFor(() => expect(screen.getByText("APPLE ROOMPLAN JSON")).toBeTruthy());
  });

  it("shows native overlay controls and reports a terminal OK with no export", () => {
    jest.useFakeTimers();
    try {
      const screen = render(<App />);
      fireEvent.press(screen.getByRole("button", { name: "Start scan" }));
      expect(screen.getByRole("button", { name: "Finish scan" })).toBeTruthy();
      fireEvent.press(screen.getByRole("button", { name: "Finish scan" }));
      expect(mockNativeSessions[mockNativeSessions.length - 1].active).toBe(true);
      expect(mockNativeSessions[mockNativeSessions.length - 1].finishTrigger).toBe(1);
      fireEvent.press(screen.getByRole("button", { name: "Mock status OK" }));
      act(() => jest.advanceTimersByTime(30000));
      expect(screen.getByText("RoomPlan finished without returning an export. Start a new scan and try again.")).toBeTruthy();
    } finally {
      jest.useRealTimers();
    }
  });

  it("accepts export after status OK and ignores a later terminal status", async () => {
    jest.useFakeTimers();
    try {
      const screen = render(<App />);
      fireEvent.press(screen.getByRole("button", { name: "Start scan" }));
      const session = mockNativeSessions[mockNativeSessions.length - 1];
      act(() => session.onStatus("OK", undefined, session.sessionId));
      expect(screen.getByText("Scan finished. Waiting for the structured JSON export…")).toBeTruthy();
      await act(async () => { await session.onExported({ jsonUrl: "file://scan.json", source: "apple-roomplan" }, session.sessionId); });
      act(() => session.onStatus("OK", undefined, session.sessionId));
      act(() => jest.advanceTimersByTime(30000));
      expect(screen.getByText("APPLE ROOMPLAN JSON")).toBeTruthy();
    } finally {
      jest.useRealTimers();
    }
  });

  it("surfaces a missing or unreadable export as a failure", async () => {
    mockReadExportJson.mockRejectedValue(new Error("RoomPlan did not return a JSON file URL."));
    const screen = render(<App />);
    fireEvent.press(screen.getByRole("button", { name: "Start scan" }));
    const session = mockNativeSessions[mockNativeSessions.length - 1];
    await act(async () => { await session.onExported({ source: "apple-roomplan" }, session.sessionId); });
    await waitFor(() => expect(screen.getByText("RoomPlan did not return a JSON file URL.")).toBeTruthy());
  });
});
