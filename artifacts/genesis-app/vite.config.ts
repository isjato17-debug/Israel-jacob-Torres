import path from 'path';
import { defineConfig } from 'vite';

const rawPort = process.env.PORT;

if (!rawPort) {
  throw new Error(
    'PORT environment variable is required but was not provided.',
  );
}

const port = Number(rawPort);

if (Number.isNaN(port) || port <= 0) {
  throw new Error(`Invalid PORT value: "${rawPort}"`);
}

const basePath = process.env.BASE_PATH;

if (!basePath) {
  throw new Error(
    'BASE_PATH environment variable is required but was not provided.',
  );
}

export default defineConfig({
  base: basePath,
  plugins: [{
    name: 'genesis-next-development-routes',
    configureServer(server) {
      server.middlewares.use((request, _response, next) => {
        const url = request.url ?? '';
        if (['/next', '/next/draft', '/next/draft/'].includes(url.split('?')[0])) {
          const query = url.indexOf('?');
          request.url = `/next/index.html${query >= 0 ? url.slice(query) : ''}`;
        }
        next();
      });
    },
  }],
  root: path.resolve(import.meta.dirname, '../../genesis-business-os/frontend'),
  esbuild: { jsx: 'automatic' },
  build: {
    outDir: path.resolve(import.meta.dirname, 'dist/public'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(import.meta.dirname, '../../genesis-business-os/frontend/index.html'),
        next: path.resolve(import.meta.dirname, '../../genesis-business-os/frontend/next/index.html'),
      },
    },
  },
  server: {
    port,
    strictPort: true,
    host: '0.0.0.0',
    allowedHosts: true,
    fs: {
      strict: true,
      allow: [path.resolve(import.meta.dirname, '../..')],
    },
  },
  preview: {
    port,
    host: '0.0.0.0',
    allowedHosts: true,
  },
});
