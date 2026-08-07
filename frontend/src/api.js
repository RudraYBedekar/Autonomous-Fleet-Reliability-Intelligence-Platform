/** API helpers — relative paths work on EC2 (Nginx) and locally (Vite proxy). */

export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`;
  return p;
}

export function wsTelemetryUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/telemetry`;
}
