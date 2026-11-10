const defaultConfig = require("./app.json").expo;

module.exports = ({ config }) => ({
  ...defaultConfig,
  ...config,
  ios: {
    ...defaultConfig.ios,
    ...config.ios,
    bundleIdentifier: "com.jonasmaihoefer.roomtwin",
  },
});
