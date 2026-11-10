import React from "react";
import { render } from "@testing-library/react-native";
import ScannerSurface from "./ScannerSurface.ios";

const mockStart = jest.fn();
const mockCancel = jest.fn();
const mockFinishScan = jest.fn();
let mockHookOptions: Record<string, unknown>;

jest.mock("expo-roomplan", () => ({
  RoomPlanView: () => null,
  ExportType: { Parametric: "PARAMETRIC" },
  useRoomPlanView: (options: Record<string, unknown>) => {
    mockHookOptions = options;
    return {
      viewProps: {},
      controls: { start: mockStart, cancel: mockCancel, finishScan: mockFinishScan },
    };
  },
}));

describe("iOS scanner adapter", () => {
  beforeEach(() => {
    mockStart.mockClear();
    mockCancel.mockClear();
    mockFinishScan.mockClear();
  });

  it("wires start, cancel, finish and stamps events with the owning session ID", () => {
    const onStatus = jest.fn();
    const onExported = jest.fn();
    const screen = render(<ScannerSurface active sessionId={41} onStatus={onStatus} onExported={onExported} />);
    expect(mockStart).toHaveBeenCalledTimes(1);

    const statusHandler = mockHookOptions.onStatus as (event: { nativeEvent: { status: string } }) => void;
    const exportHandler = mockHookOptions.onExported as (event: { nativeEvent: { jsonUrl: string } }) => void;
    statusHandler({ nativeEvent: { status: "OK" } });
    exportHandler({ nativeEvent: { jsonUrl: "file://scan.json" } });
    expect(onStatus).toHaveBeenCalledWith("OK", undefined, 41);
    expect(onExported).toHaveBeenCalledWith({ jsonUrl: "file://scan.json", source: "apple-roomplan" }, 41);

    screen.rerender(<ScannerSurface active={false} sessionId={41} onStatus={onStatus} onExported={onExported} />);
    expect(mockCancel).toHaveBeenCalledTimes(1);
    screen.rerender(<ScannerSurface active sessionId={42} onStatus={onStatus} onExported={onExported} />);
    expect(mockStart).toHaveBeenCalledTimes(2);
    expect(mockHookOptions.onStatus).not.toBe(statusHandler);
    screen.rerender(<ScannerSurface active sessionId={42} finishTrigger={7} onStatus={onStatus} onExported={onExported} />);
    expect(mockFinishScan).toHaveBeenCalledTimes(1);
  });
});
