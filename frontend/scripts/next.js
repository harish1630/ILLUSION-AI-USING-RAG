const { spawn } = require("node:child_process");
const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const projectDirectory = path.resolve(__dirname, "..");
const nodeModules = path.join(projectDirectory, "node_modules");
const oneDriveRoots = [
  process.env.OneDrive,
  process.env.OneDriveConsumer,
].filter(Boolean);

const projectPath = projectDirectory.toLowerCase();
const isInOneDrive = oneDriveRoots.some((root) => {
  const rootPath = path.resolve(root).toLowerCase();
  return projectPath === rootPath || projectPath.startsWith(rootPath + path.sep);
});

if (process.platform === "win32" && isInOneDrive) {
  const cacheRoot = path.join(
    process.env.LOCALAPPDATA || os.tmpdir(),
    "illusion-ai-next-cache",
  );
  const projectKey = crypto
    .createHash("sha256")
    .update(projectDirectory.toLowerCase())
    .digest("hex")
    .slice(0, 12);
  const cacheDirectory = path.join(cacheRoot, projectKey);
  const distDirectory = path.join(projectDirectory, ".next");

  fs.mkdirSync(cacheDirectory, { recursive: true });

  let alreadyLinked = false;
  try {
    const distStats = fs.lstatSync(distDirectory);
    alreadyLinked =
      distStats.isSymbolicLink() &&
      path.resolve(fs.realpathSync(distDirectory)).toLowerCase() ===
        path.resolve(cacheDirectory).toLowerCase();
    if (!alreadyLinked) {
      fs.rmSync(distDirectory, { recursive: true, force: true });
    }
  } catch (error) {
    if (error.code !== "ENOENT") {
      throw error;
    }
  }

  if (!alreadyLinked) {
    fs.symlinkSync(cacheDirectory, distDirectory, "junction");
  }
}

const env = {
  ...process.env,
  NODE_PATH: [nodeModules, process.env.NODE_PATH].filter(Boolean).join(path.delimiter),
};
const nextCli = require.resolve("next/dist/bin/next", { paths: [nodeModules] });
const nextProcess = spawn(
  process.execPath,
  [nextCli, ...process.argv.slice(2)],
  {
    cwd: projectDirectory,
    env,
    stdio: "inherit",
  },
);

nextProcess.on("error", (error) => {
  console.error(`Failed to start Next.js: ${error.message}`);
  process.exitCode = 1;
});

nextProcess.on("exit", (code, signal) => {
  process.exitCode = signal ? 1 : code ?? 0;
});
