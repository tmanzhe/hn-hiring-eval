import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cloud Run runs the container, not `next start` on a full node_modules tree.
  // Standalone emits just the server and the files it actually imports.
  output: "standalone",
};

export default nextConfig;
