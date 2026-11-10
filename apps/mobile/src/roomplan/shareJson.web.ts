export async function shareOrDownloadJson(json: string): Promise<void> {
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  try {
    const link = document.createElement("a");
    link.href = url;
    link.download = "room-twin-mock-roomplan.json";
    link.click();
  } finally {
    URL.revokeObjectURL(url);
  }
}
