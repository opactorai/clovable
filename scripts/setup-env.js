#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const net = require('net');

const rootDir = path.join(__dirname, '..');
const envFile = path.join(rootDir, '.env');
const webEnvFile = path.join(rootDir, 'apps', 'web', '.env.local');

// Default ports
const DEFAULT_API_PORT = 8080;
const DEFAULT_WEB_PORT = 3000;

// Check if port is available using lsof or netstat
function isPortAvailable(port) {
  return new Promise((resolve) => {
    const { exec } = require('child_process');
    const platform = require('os').platform();
    
    // Try using lsof on Unix-like systems (Mac, Linux)
    if (platform === 'darwin' || platform === 'linux') {
      exec(`lsof -i :${port} -P -n | grep LISTEN`, (error, stdout) => {
        if (error || !stdout) {
          // No process listening on this port
          resolve(true);
        } else {
          // Port is in use
          console.log(`    Port ${port} is in use by: ${stdout.trim().split(/\s+/)[0]}`);
          resolve(false);
        }
      });
    } else if (platform === 'win32') {
      // Use netstat on Windows
      exec(`netstat -ano | findstr :${port}`, (error, stdout) => {
        if (error || !stdout) {
          resolve(true);
        } else {
          resolve(false);
        }
      });
    } else {
      // Fallback to original method
      const server = net.createServer();
      server.once('error', () => resolve(false));
      server.once('listening', () => {
        server.close();
        resolve(true);
      });
      server.listen(port);
    }
  });
}

// Find available port starting from default
async function findAvailablePort(startPort) {
  let port = startPort;
  while (!(await isPortAvailable(port))) {
    port++;
  }
  return port;
}

async function setupEnvironment() {
  console.log('Setting up environment...');
  
  try {
    // Ensure data directory exists
    const dataDir = path.join(rootDir, 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
      console.log('  Created data directory');
    }
    
    // Check if .env already exists and read existing ports
    let apiPort = DEFAULT_API_PORT;
    let webPort = DEFAULT_WEB_PORT;
    let existingEnv = {};
    
    if (fs.existsSync(envFile)) {
      const envContent = fs.readFileSync(envFile, 'utf8');
      envContent.split('\n').forEach(line => {
        if (line && !line.startsWith('#')) {
          const [key, value] = line.split('=');
          if (key && value) {
            existingEnv[key.trim()] = value.trim();
          }
        }
      });
      
      // Use existing ports if available
      if (existingEnv.API_PORT) {
        apiPort = parseInt(existingEnv.API_PORT, 10);
        console.log(`  Using existing API port from .env: ${apiPort}`);
      }
      if (existingEnv.WEB_PORT) {
        webPort = parseInt(existingEnv.WEB_PORT, 10);
        console.log(`  Using existing Web port from .env: ${webPort}`);
      }
    }
    
    // Check if existing ports are available, find new ones if not
    if (!await isPortAvailable(apiPort)) {
      const newApiPort = await findAvailablePort(apiPort);
      console.log(`  API port ${apiPort} is busy, using ${newApiPort}`);
      apiPort = newApiPort;
    } else if (!existingEnv.API_PORT) {
      console.log(`  API port: ${apiPort}`);
    }
    
    if (!await isPortAvailable(webPort)) {
      const newWebPort = await findAvailablePort(webPort);
      console.log(`  Web port ${webPort} is busy, using ${newWebPort}`);
      webPort = newWebPort;
    } else if (!existingEnv.WEB_PORT) {
      console.log(`  Web port: ${webPort}`);
    }
    
    // Only create/update .env if it doesn't exist or ports have changed
    if (!fs.existsSync(envFile) || 
        parseInt(existingEnv.API_PORT) !== apiPort || 
        parseInt(existingEnv.WEB_PORT) !== webPort) {
      const envContent = `# Auto-generated environment configuration
API_PORT=${apiPort}
WEB_PORT=${webPort}
DATABASE_URL=sqlite:///${path.join(rootDir, 'data', 'cc.db')}
`;
      
      fs.writeFileSync(envFile, envContent);
      console.log(`  Updated .env`);
    } else {
      console.log(`  .env already configured with correct ports`);
    }
    
    // Always update web .env.local file to sync with current API port
    const webEnvContent = `# Auto-generated environment configuration
NEXT_PUBLIC_API_BASE=http://localhost:${apiPort}
NEXT_PUBLIC_WS_BASE=ws://localhost:${apiPort}
`;
    
    fs.writeFileSync(webEnvFile, webEnvContent);
    console.log(`  Updated apps/web/.env.local with API port: ${apiPort}`);
    
    console.log('  Environment setup complete!');
    
    if (apiPort !== DEFAULT_API_PORT || webPort !== DEFAULT_WEB_PORT) {
      console.log('\n  Note: Using non-default ports');
      console.log(`     API: http://localhost:${apiPort}`);
      console.log(`     Web: http://localhost:${webPort}`);
    }
    
    // Return ports for use in other scripts
    return { apiPort, webPort };
  } catch (error) {
    console.error('\nFailed to setup environment');
    console.error('Error:', error.message);
    console.error('\nHow to fix:');
    console.error('   1. Check file permissions');
    console.error('   2. Ensure you have write access to the project directory');
    console.error('   3. Try running with elevated permissions if needed');
    process.exit(1);
  }
}

// If run directly
if (require.main === module) {
  setupEnvironment().catch(console.error);
}

module.exports = { setupEnvironment, findAvailablePort };