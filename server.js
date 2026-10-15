#!/usr/bin/env node
/**
 * Smithery wrapper for japan-market-mcp.
 *
 * The MCP server is implemented in Python (src/stdio_main.py, run via uv).
 * Smithery hosts provide Node.js but not uv, so this thin wrapper spawns
 * the Python entry point and pipes stdio through to the Smithery runtime.
 */
'use strict';

const { spawn } = require('child_process');
const path = require('path');

const repoRoot = __dirname;

// Prefer uv (declared in pyproject), fall back to plain python3.
const candidates = [
  ['uv', ['run', '--directory', repoRoot, 'src/stdio_main.py']],
  ['python3', [path.join(repoRoot, 'src', 'stdio_main.py')]],
];

let child = null;
let started = false;

function trySpawn(index) {
  if (index >= candidates.length) {
    console.error('japan-market-mcp: no working Python runner (tried uv, python3)');
    process.exit(1);
  }
  const [cmd, args] = candidates[index];
  child = spawn(cmd, args, { stdio: ['inherit', 'inherit', 'inherit'], env: { ...process.env } });
  child.on('error', (err) => {
    console.error(`japan-market-mcp: ${cmd} failed to start: ${err.message}`);
    trySpawn(index + 1);
  });
  child.on('exit', (code) => {
    process.exit(code == null ? 1 : code);
  });
}

trySpawn(0);