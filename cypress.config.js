import { defineConfig } from 'cypress';
export default defineConfig({
  viewportWidth: 390,
  viewportHeight: 844,
  video: true,
  screenshotOnRunFailure: true,
  e2e: { supportFile: false, baseUrl: 'http://127.0.0.1:5173', defaultCommandTimeout: 10000 }
});
