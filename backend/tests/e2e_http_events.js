// backend/tests/e2e_http_events.js
import http from 'k6/http';

// ===== 환경 변수 =====
// RATE: 초당 이벤트 수(EPS)         예) 20000
// DURATION: 테스트 시간             예) 5m
// URL: 이벤트 수신 URL              예) http://stream_writer:8000/events
// HEAVY_RATIO: mouse 비율(나머지 keydown)
// MOUSE_BYTES/KEY_BYTES: 바이트 근사 패딩(전송량 맞추기)
const RATE = Number(__ENV.RATE || 1000);
const DURATION = __ENV.DURATION || '2m';
const URL = __ENV.URL || 'http://stream_writer:8000/events';
const HEAVY_RATIO = Number(__ENV.HEAVY_RATIO || 0.7);
const MOUSE_BYTES = Number(__ENV.MOUSE_BYTES || 450);
const KEY_BYTES = Number(__ENV.KEY_BYTES || 150);

// VU 가이드: 대략 VU ≈ RATE × (평균응답시간 초)
const PRE_VUS = Number(__ENV.PRE_VUS || 2000);
const MAX_VUS = Number(__ENV.MAX_VUS || 8000);

export const options = {
  discardResponseBodies: true,
  scenarios: {
    warmup: {
      executor: 'ramping-arrival-rate',
      startRate: Math.ceil(RATE * 0.1),
      timeUnit: '1s',
      preAllocatedVUs: PRE_VUS,
      maxVUs: MAX_VUS,
      stages: [
        { duration: '20s', target: Math.ceil(RATE * 0.5) },
        { duration: '20s', target: Math.ceil(RATE * 0.8) },
        { duration: '20s', target: RATE },
      ],
      gracefulStop: '10s',
    },
    steady: {
      executor: 'constant-arrival-rate',
      rate: RATE,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: PRE_VUS,
      maxVUs: MAX_VUS,
      startTime: '1m30s',
      gracefulStop: '10s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],    // 실패율 < 1%
    http_req_duration: ['p(95)<1000'], // p95 < 1s (환경에 맞게 조정)
  },
};

function rnd(n) { return Math.floor(Math.random() * n); }

// 실제 프론트 기준 mouse 페이로드 형태
function makeMouse() {
  const now = Date.now();
  const payload = {
    shape: null,
    stream: 'mouse',
    event_type: 'mousemove', // 필요하면 아래 배열에서 랜덤 선택 가능
    // event_type: ['mousemove','click','dblclick','contextmenu','mousedown','mouseup','mouseover','mouseout','mouseenter','mouseleave'][rnd(10)],
    canvasX: Math.random() * 400,
    canvasY: Math.random() * 400,
    clientX: rnd(400),
    clientY: rnd(400),
    pageX: rnd(400),
    pageY: rnd(400),
    screenX: rnd(1920),
    screenY: rnd(1080),
    movementX: Math.random() * 5,
    movementY: Math.random() * 5,
    button: 0,
    buttons: 0,
    ctrlKey: Math.random() < 0.1,
    altKey: Math.random() < 0.1,
    shiftKey: Math.random() < 0.1,
    metaKey: Math.random() < 0.1,
    timestamp: now,
    isTrusted: true,
  };
  // 크기 근사 패딩(전송량 맞추기용)
  const curr = JSON.stringify(payload).length;
  const pad = Math.max(0, MOUSE_BYTES - curr);
  if (pad > 0) payload._pad = 'x'.repeat(pad);
  return payload;
}

// 실제 프론트 기준 keydown 페이로드 형태
function makeKey() {
  const keys = ['A', 'B', 'C', 'Enter', 'Escape'];
  const codes = ['KeyA', 'KeyB', 'KeyC', 'Enter', 'Escape'];
  const now = Date.now();
  const i = rnd(keys.length);
  const payload = {
    stream: 'keydown',
    key: keys[i],
    code: codes[i],
    altKey: Math.random() < 0.1,
    ctrlKey: Math.random() < 0.1,
    shiftKey: Math.random() < 0.1,
    metaKey: Math.random() < 0.1,
    timestamp: now,
    type: 'keydown',
  };
  const curr = JSON.stringify(payload).length;
  const pad = Math.max(0, KEY_BYTES - curr);
  if (pad > 0) payload._pad = 'x'.repeat(pad);
  return payload;
}

export default function () {
  const body = Math.random() < HEAVY_RATIO ? makeMouse() : makeKey();
  http.post(URL, JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
    timeout: '1s',
  });
}
