'use client';
const log = (...args: any[]) => {
  console.log(...args);
};
import { useEffect, useRef } from "react";

import Image from "next/image";

const measureBytes = (obj: unknown): number => {
  try {
    return new TextEncoder().encode(JSON.stringify(obj)).length;
  } catch {
    return -1;
  }
};

type Shape =
  | { type: 'rect', x: number, y: number, w: number, h: number }
  | { type: 'circle', x: number, y: number, r: number }
  | { type: 'triangle', points: [ {x: number, y: number}, {x: number, y: number}, {x: number, y: number} ] }


export default function Home() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const shapes: Shape[] = [
    { type: 'rect', x: 50, y: 50, w: 100, h: 100 },
    { type: 'circle', x: 200, y: 200, r: 50 },
    {
      type: 'triangle',
      points: [
        { x: 300, y: 50 },
        { x: 350, y: 150 },
        { x: 250, y: 150 }
      ]
    },
    { type: 'rect', x: 100, y: 300, w: 120, h: 80 } // 주황색 사각형
  ];

  const sendPayload = async (payload: any) => {
    const sizeBytes = measureBytes(payload);
    log('DEBUG', '[size]', sizeBytes, 'bytes');
    try {
      await fetch("http://localhost:8000/api/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      console.error("Event send failed:", err);
    }
  };

const handleMouseEvent = (e: React.MouseEvent) => {
  const canvas = canvasRef.current;
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  let hitShape: Shape | null = null;

  for (const shape of shapes) {
    if (shape.type === 'rect') {
      if (x >= shape.x && x <= shape.x + shape.w && y >= shape.y && y <= shape.y + shape.h) {
        hitShape = shape;
        break;
      }
    } else if (shape.type === 'circle') {
      const dx = x - shape.x;
      const dy = y - shape.y;
      if (Math.sqrt(dx * dx + dy * dy) <= shape.r) {
        hitShape = shape;
        break;
      }
    } else if (shape.type === 'triangle') {
      const [p1, p2, p3] = shape.points;
      const area = (a: any, b: any, c: any) =>
        Math.abs((a.x*(b.y-c.y) + b.x*(c.y-a.y) + c.x*(a.y-b.y)) / 2);
      const A = area(p1, p2, p3);
      const A1 = area({x,y}, p2, p3);
      const A2 = area(p1, {x,y}, p3);
      const A3 = area(p1, p2, {x,y});
      if (Math.abs(A - (A1+A2+A3)) < 0.5) {
        hitShape = shape;
        break;
      }
    }
  }

  if (!hitShape) return;

  console.log(`🖱️ [${e.type}]`, { x, y, shape: hitShape }, e);
  const payload = {
    canvasId: "main-annotation-canvas",
    stream: "mouse",
    event_type: e.type,
    canvasX: x,
    canvasY: y,
    clientX: e.clientX,
    clientY: e.clientY,
    pageX: e.pageX,
    pageY: e.pageY,
    screenX: e.screenX,
    screenY: e.screenY,
    movementX: e.movementX,
    movementY: e.movementY,
    button: e.button,
    buttons: e.buttons,
    ctrlKey: e.ctrlKey,
    altKey: e.altKey,
    shiftKey: e.shiftKey,
    metaKey: e.metaKey,
    timestamp: Date.now(),
    isTrusted: e.isTrusted,
    shape: hitShape ?? null
  };
  sendPayload(payload);
};


  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    shapes.forEach(shape => {
      if (shape.type === 'rect') {
        if (shape.x === 100 && shape.y === 300) {
          ctx.fillStyle = "yellow"; // 주황색 사각형
        } else {
          ctx.fillStyle = "red";
        }
        ctx.fillRect(shape.x, shape.y, shape.w, shape.h);
      } else if (shape.type === 'circle') {
        ctx.fillStyle = "blue";
        ctx.beginPath();
        ctx.arc(shape.x, shape.y, shape.r, 0, Math.PI*2);
        ctx.fill();
      } else if (shape.type === 'triangle') {
        const [p1,p2,p3] = shape.points;
        ctx.fillStyle = "green";
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.lineTo(p3.x, p3.y);
        ctx.closePath();
        ctx.fill();
      }
    });
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const payload = {
        stream: "keydown",
        key: e.key,
        code: e.code,
        altKey: e.altKey,
        ctrlKey: e.ctrlKey,
        shiftKey: e.shiftKey,
        metaKey: e.metaKey,
        timestamp: Date.now(),
        type: e.type,
      };

      sendPayload(payload);
      log('DEBUG', "키보드 이벤트 전송:", payload);
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-6 bg-gray-100 py-10">
      <h1 className="text-2xl font-bold text-gray-700">🎨 캔버스 도형 인터랙션 예제</h1>
      <p className="text-gray-600 text-sm">
        캔버스를 클릭하거나 마우스를 올려 도형과의 상호작용을 확인해보세요.
      </p>
      <canvas
        ref={canvasRef}
        width={400}
        height={400}
        onClick={handleMouseEvent}
        onMouseDown={handleMouseEvent}
        onMouseUp={handleMouseEvent}
        onDoubleClick={handleMouseEvent}
        onMouseMove={handleMouseEvent}
        onMouseOver={handleMouseEvent}
        onMouseOut={handleMouseEvent}
        onMouseEnter={handleMouseEvent}
        onMouseLeave={handleMouseEvent}
        onContextMenu={(e) => {
          e.preventDefault();
          handleMouseEvent(e);
        }}
        className="border-2 border-gray-500 shadow-md bg-white"
      />
    </div>
  );
}
