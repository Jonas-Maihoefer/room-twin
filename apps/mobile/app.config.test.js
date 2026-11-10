/* global describe, it, expect */
const appConfig = require("./app.config");

describe("iOS bundle identifier", () => {
  it("always resolves to the project identifier regardless of local EAS environment variables", () => {
    const previous = process.env.IOS_BUNDLE_IDENTIFIER;
    process.env.IOS_BUNDLE_IDENTIFIER = "com.example.unexpected";
    try {
      expect(appConfig({ config: {} }).ios.bundleIdentifier).toBe("com.jonasmaihoefer.roomtwin");
    } finally {
      if (previous === undefined) delete process.env.IOS_BUNDLE_IDENTIFIER;
      else process.env.IOS_BUNDLE_IDENTIFIER = previous;
    }
  });
});
