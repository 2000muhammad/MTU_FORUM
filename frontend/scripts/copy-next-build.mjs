import { cp, mkdir, rm } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repositoryDir = resolve(frontendDir, "..");
const sourceDir = join(frontendDir, "out");
const targetDir = join(repositoryDir, "static", "next");

if (targetDir !== resolve(repositoryDir, "static", "next")) {
  throw new Error("Refusing to replace an unexpected build directory.");
}

await rm(targetDir, { recursive: true, force: true });
await mkdir(targetDir, { recursive: true });
await cp(sourceDir, targetDir, { recursive: true });
console.log(`Next.js export copied to ${targetDir}`);
