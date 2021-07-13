module.exports = (api) => {
  const dev = api.mode === "development";

  return {
    plugins: [
      "autoprefixer",
      // disable cssnano in dev as it breaks source maps:
      ...(dev ? [] : ["cssnano"]),
      "postcss-custom-properties",
    ],
  };
};
