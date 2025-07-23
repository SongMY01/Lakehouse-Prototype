'use client';
import { useEffect, useRef } from "react";
import Image from "next/image";

type Shape =
  | { type: 'rect', x: number, y: number, w: number, h: number }
  | { type: 'circle', x: number, y: number, r: number }
  | { type: 'triangle', points: [ {x: number, y: number}, {x: number, y: number}, {x: number, y: number} ] }
  | { type: 'curve', start: {x: number, y: number}, cp: {x: number, y: number}, end: {x: number, y: number} };

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
  ];

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
};


  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    shapes.forEach(shape => {
      if (shape.type === 'rect') {
        ctx.fillStyle = "red";
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

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
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
        className="border border-gray-400"
      />
    </div>
  );
}
