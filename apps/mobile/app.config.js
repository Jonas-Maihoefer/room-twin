const defaultConfig = require("./app.json").expo;

module.exports = ({ config }) => ({
  ...defaultConfig,
  ...config,
  ios: {
    ...defaultConfig.ios,
    ...config.ios,
    bundleIdentifier: process.env.IOS_BUNDLE_IDENTIFIER || "com.jonasmaihoefer.roomtwin",
  },
});
