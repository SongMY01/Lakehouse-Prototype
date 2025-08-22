'use client'
import { useEffect, useRef, useState, useMemo, useCallback } from 'react'
import { BadgeCheck, Car, Waypoints, MousePointerClick, Move3D, Ruler, PackageSearch, Camera, Cpu, Square, Circle, Triangle, Save, Upload, Download, Settings, Keyboard, Inspect, Activity } from 'lucide-react'

// === Utilities ===
const log = (...args: any[]) => console.log(...args)
const measureBytes = (obj: unknown): number => {
  try {
    return new TextEncoder().encode(JSON.stringify(obj)).length
  } catch {
    return -1
  }
}

// === test.tsx 스타일: 이벤트 직렬화 & 전송 ===
function serializeEvent(e: Event): Record<string, any> {
  // Robust epoch timestamp derivation
  const rawTs = (e as any).timeStamp
  const isNumber = typeof rawTs === 'number' && Number.isFinite(rawTs)
  const navStart = (performance as any)?.timeOrigin ?? (performance as any)?.timing?.navigationStart
  const epochMs = (() => {
    if (!isNumber) return Date.now()
    // If the browser gives high-res relative ts (typically < 1e12), convert using timeOrigin
    if (rawTs < 1e12) {
      const base = typeof navStart === 'number' ? navStart : Date.now() - rawTs
      return Math.round(base + rawTs)
    }
    // Some browsers already provide epoch ms
    return Math.round(rawTs)
  })()

  const obj: Record<string, any> = {
    type: e.type,
    timeStamp: epochMs,
  }

  // target 정보 최소화 저장
  if (e.target instanceof HTMLElement) {
    obj.target = {
      tag: e.target.tagName,
      id: e.target.id,
      className: e.target.className,
    }
  }

  // enumerable 속성 자동 복사 (함수/객체 제외)
  for (const key in e as any) {
    try {
      const val = (e as any)[key]
      if (typeof val !== 'function' && typeof val !== 'object') {
        // 충돌 방지: 위에서 이미 세팅한 키는 덮어쓰지 않음
        if (!(key in obj)) obj[key] = val
      }
    } catch {}
  }

  return obj
}

function enqueueLog(payload: Record<string, any>) {
  fetch('http://localhost:8000/api/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).catch((err) => {
    console.error('Failed to send event:', err)
  })
}

// === Types ===
type Point = { x: number; y: number }

type Shape =
  | { type: 'rect'; id: string; x: number; y: number; w: number; h: number; label?: string; color?: string }
  | { type: 'circle'; id: string; x: number; y: number; r: number; label?: string; color?: string }
  | { type: 'triangle'; id: string; points: [Point, Point, Point]; label?: string; color?: string }

// === Demo Data ===
const demoShapes: Shape[] = [
  { type: 'rect', id: 's1', x: 50, y: 50, w: 100, h: 100, label: 'Car', color: '#22d3ee' },
  { type: 'circle', id: 's2', x: 200, y: 200, r: 50, label: 'Person', color: '#34d399' },
  {
    type: 'triangle',
    id: 's3',
    points: [
      { x: 300, y: 50 },
      { x: 350, y: 150 },
      { x: 250, y: 150 },
    ],
    label: 'Yield Sign',
    color: '#fbbf24',
  },
  { type: 'rect', id: 's4', x: 100, y: 300, w: 120, h: 80, label: 'Red Light', color: '#a78bfa' },
]

// === Component ===
export default function AutomotiveLabeler() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [shapes, setShapes] = useState<Shape[]>(demoShapes)
  const [hoverId, setHoverId] = useState<string | null>(null)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [cursor, setCursor] = useState<'default' | 'crosshair' | 'grabbing'>('crosshair')
  const [lastEvent, setLastEvent] = useState<any>(null)
  const [payloadSize, setPayloadSize] = useState<number>(0)
  const [mousePos, setMousePos] = useState<Point>({ x: 0, y: 0 })

  const classes = useMemo(
    () => [
      { key: 'vehicle', name: 'Vehicle', color: '#22d3ee', icon: Car },
      { key: 'pedestrian', name: 'Pedestrian', color: '#34d399', icon: Waypoints },
      { key: 'traffic_sign', name: 'Traffic Sign', color: '#fbbf24', icon: Triangle },
      { key: 'traffic_light', name: 'Traffic Light', color: '#a78bfa', icon: Activity },
    ],
    []
  )

  // === Drawing Helpers ===
  const drawGrid = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    ctx.save()
    ctx.clearRect(0, 0, width, height)

    // dark base
    ctx.fillStyle = '#0b1220'
    ctx.fillRect(0, 0, width, height)

    // grid lines
    ctx.beginPath()
    const minor = 10
    const major = 50
    for (let x = 0; x <= width; x += minor) {
      ctx.moveTo(x + 0.5, 0)
      ctx.lineTo(x + 0.5, height)
    }
    for (let y = 0; y <= height; y += minor) {
      ctx.moveTo(0, y + 0.5)
      ctx.lineTo(width, y + 0.5)
    }
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)'
    ctx.lineWidth = 1
    ctx.stroke()

    // major grid emphasized
    ctx.beginPath()
    for (let x = 0; x <= width; x += major) {
      ctx.moveTo(x + 0.5, 0)
      ctx.lineTo(x + 0.5, height)
    }
    for (let y = 0; y <= height; y += major) {
      ctx.moveTo(0, y + 0.5)
      ctx.lineTo(width, y + 0.5)
    }
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.25)'
    ctx.lineWidth = 1
    ctx.stroke()

    ctx.restore()
  }

  const drawShapes = (ctx: CanvasRenderingContext2D) => {
    shapes.forEach((shape) => {
      const isHover = hoverId === shape.id
      const isActive = activeId === shape.id
      const base = shape.color ?? '#60a5fa'

      ctx.save()
      // Fill
      ctx.fillStyle = base + (isHover ? 'AA' : '66')
      ctx.strokeStyle = isActive ? '#f97316' : base
      ctx.lineWidth = isActive ? 3 : 2

      if (shape.type === 'rect') {
        ctx.fillRect(shape.x, shape.y, shape.w, shape.h)
        ctx.strokeRect(shape.x, shape.y, shape.w, shape.h)
      } else if (shape.type === 'circle') {
        ctx.beginPath()
        ctx.arc(shape.x, shape.y, shape.r, 0, Math.PI * 2)
        ctx.fill()
        ctx.stroke()
      } else if (shape.type === 'triangle') {
        const [p1, p2, p3] = shape.points
        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.lineTo(p3.x, p3.y)
        ctx.closePath()
        ctx.fill()
        ctx.stroke()
      }

      // Label pill
      if (shape.label) {
        const label = shape.label
        ctx.font = '12px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto'
        const textWidth = ctx.measureText(label).width
        const padX = 6
        const padY = 3
        let lx = 0,
          ly = 0
        if (shape.type === 'rect') {
          lx = shape.x
          ly = shape.y - 8
        } else if (shape.type === 'circle') {
          lx = shape.x - shape.r
          ly = shape.y - shape.r - 8
        } else {
          const top = [...shape.points].sort((a, b) => a.y - b.y)[0]
          lx = top.x
          ly = top.y - 8
        }
        // bg
        ctx.fillStyle = 'rgba(15,23,42,0.9)'
        ctx.strokeStyle = base
        ctx.lineWidth = 1
        ctx.beginPath()
        //@ts-ignore roundRect 지원 브라우저
        ctx.roundRect(lx - padX, ly - 12 - padY, textWidth + padX * 2, 18, 6)
        ctx.fill()
        ctx.stroke()
        // text
        ctx.fillStyle = '#e2e8f0'
        ctx.fillText(label, lx, ly)
      }
      ctx.restore()
    })
  }

  // === Hit Testing ===
  const hitTest = useCallback(
    (x: number, y: number): Shape | null => {
      for (const shape of [...shapes].reverse()) {
        if (shape.type === 'rect') {
          if (x >= shape.x && x <= shape.x + shape.w && y >= shape.y && y <= shape.y + shape.h) return shape
        } else if (shape.type === 'circle') {
          const dx = x - shape.x
          const dy = y - shape.y
          if (Math.sqrt(dx * dx + dy * dy) <= shape.r) return shape
        } else {
          const [p1, p2, p3] = shape.points
          const area = (a: Point, b: Point, c: Point) => Math.abs((a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y)) / 2)
          const A = area(p1, p2, p3)
          const A1 = area({ x, y }, p2, p3)
          const A2 = area(p1, { x, y }, p3)
          const A3 = area(p1, p2, { x, y })
          if (Math.abs(A - (A1 + A2 + A3)) < 0.5) return shape
        }
      }
      return null
    },
    [shapes]
  )

  // === Mouse Handling (로컬 UI 상태만 업데이트) ===
  const handleMouseEvent = (e: React.MouseEvent) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    setMousePos({ x: Math.round(x), y: Math.round(y) })

    const hit = hitTest(x, y)
    setHoverId(hit?.id ?? null)
    if (e.type === 'mousedown' && hit) setActiveId(hit.id)
    if (e.type === 'mouseup') setActiveId((prev) => (prev && !hit ? null : prev))
    // ✅ 네트워킹은 전역 이벤트 로거가 담당(serializeEvent + enqueueLog)
  }

  // === Draw Loop ===
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    drawGrid(ctx, canvas.width, canvas.height)
    drawShapes(ctx)
  }, [shapes, hoverId, activeId])

  // === test.tsx 스타일: 전역 이벤트 로거 ===
  useEffect(() => {
    const allEventTypes = Object.keys(window)
      .filter((k) => k.startsWith('on'))
      .map((k) => k.slice(2))

    const handler = (e: Event) => {
      const payload = serializeEvent(e)

      // 캔버스 상호작용이면 캔버스 상대 좌표 & 히트 정보 보강 (선택적 확장)
      const target = e.target as HTMLElement | null
      if (target && target === canvasRef.current) {
        const rect = canvasRef.current!.getBoundingClientRect()
        const mx = (e as any).clientX - rect.left
        const my = (e as any).clientY - rect.top
        const hit = hitTest(mx, my)
        ;(payload as any)._canvas = {
          canvasX: Math.round(mx),
          canvasY: Math.round(my),
          shape: hit
            ? { id: hit.id, type: hit.type, label: hit.label ?? null, color: hit.color ?? null }
            : null,
        }
      }

      // Send policy (mouse/pointer only gated by canvas hit; others sent globally)
      const isCanvasEvent = target && target === canvasRef.current
      const t = String(payload.type || '')
      const isMousePointer = t.startsWith('mouse') || t.startsWith('pointer')
      const hitShape = (payload as any)._canvas?.shape ?? null

      if (isMousePointer) {
        // For mouse/pointer events, send only when on canvas AND a shape is hit
        if (isCanvasEvent && hitShape) {
          setLastEvent(payload)
          setPayloadSize(measureBytes(payload))
          enqueueLog(payload)
        }
      } else {
        // All other events (keyboard, focus, visibility, etc.)
        setLastEvent(payload)
        setPayloadSize(measureBytes(payload))
        enqueueLog(payload)
      }
    }

    // 가능한 모든 이벤트 타입 등록
    allEventTypes.forEach((type) => {
      try {
        window.addEventListener(type as any, handler, { passive: true })
      } catch {}
    })

    return () => {
      allEventTypes.forEach((type) => {
        try {
          window.removeEventListener(type as any, handler as any)
        } catch {}
      })
    }
  }, [hitTest])

  // === UI ===
  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-200">
      {/* Top Bar */}
      <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <img src="/strad_logo.svg" width={50} height={50} className="h-5 w-5 object-contain" />
            <span className="text-sm uppercase tracking-widest text-slate-400">Stradvision</span>
            <span className="text-sm font-semibold text-slate-100">Labelit</span>
            <BadgeCheck className="ml-2 h-4 w-4 text-emerald-400" />
          </div>
          <div className="flex items-center gap-2">
            <button className="inline-flex items-center gap-1 rounded-xl border border-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-900">
              <Camera className="h-4 w-4" /> Dataset: <b className="ml-1 text-slate-100">demo-seq-001</b>
            </button>
            <button className="rounded-xl border border-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-900">
              <Settings className="mr-1 inline h-4 w-4" /> Settings
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl grid-cols-[220px_minmax(0,1fr)_300px] gap-4 px-4 py-4">
        {/* Left Sidebar: Classes */}
        <aside className="rounded-2xl border border-slate-800 bg-slate-900/50 p-3">
          <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wider text-slate-400">
            <PackageSearch className="h-4 w-4" /> Classes
          </div>
          <div className="space-y-2">
            {classes.map((c) => (
              <button
                key={c.key}
                className="group flex w-full items-center justify-between gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 hover:border-slate-700"
              >
                <span className="flex items-center gap-2">
                  <c.icon className="h-4 w-4" /> {c.name}
                </span>
                <span className="h-3 w-3 rounded" style={{ background: c.color }} aria-hidden />
              </button>
            ))}
          </div>

          <div className="mt-4 h-px bg-slate-800" />

          <div className="mt-4 space-y-2 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <Keyboard className="h-3.5 w-3.5" /> H: Toggle help, Del: Remove
            </div>
            <div className="flex items-center gap-2">
              <Move3D className="h-3.5 w-3.5" /> Drag to move, Double-click to select
            </div>
            <div className="flex items-center gap-2">
              <Ruler className="h-3.5 w-3.5" /> Grid 10/50px snapping
            </div>
          </div>
        </aside>

        {/* Center: Canvas + Toolbar */}
        <main className="flex flex-col gap-3">
          {/* Tool Bar */}
          <div className="flex items-center gap-2 rounded-2xl border border-slate-800 bg-slate-900/60 p-2">
            <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:border-slate-700">
              <MousePointerClick className="mr-2 inline h-4 w-4" />
              Select
            </button>
            <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:border-slate-700">
              <Square className="mr-2 inline h-4 w-4" />
              Box
            </button>
            <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:border-slate-700">
              <Circle className="mr-2 inline h-4 w-4" />
              Circle
            </button>
            <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:border-slate-700">
              <Triangle className="mr-2 inline h-4 w-4" />
              Polygon
            </button>
            <div className="ml-auto flex items-center gap-2">
              <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:border-slate-700">
                <Save className="mr-2 inline h-4 w-4" />
                Save
              </button>
              <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:border-slate-700">
                <Upload className="mr-2 inline h-4 w-4" />
                Import
              </button>
              <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:border-slate-700">
                <Download className="mr-2 inline h-4 w-4" />
                Export
              </button>
            </div>
          </div>

          {/* Canvas Stage */}
          <div className="relative rounded-2xl border border-slate-800 bg-slate-900/50 p-3">
            <div className="absolute inset-x-3 top-3 z-10 flex items-center justify-between text-xs text-slate-400">
              <span className="flex items-center gap-2">
                <Inspect className="h-4 w-4" /> scene_0001.png{' '}
                <span className="rounded bg-slate-800/80 px-2 py-0.5 text-[10px]">400×400</span>
              </span>
              <span className="rounded-xl border border-slate-800 bg-slate-900 px-2 py-1">
                Cursor: <b className="ml-1 text-slate-200">{mousePos.x}</b>,{' '}
                <b className="text-slate-200">{mousePos.y}</b>
              </span>
            </div>

            <canvas
              ref={canvasRef}
              width={400}
              height={400}
              onClick={handleMouseEvent}
              onMouseDown={(e) => {
                setCursor('grabbing')
                handleMouseEvent(e)
              }}
              onMouseUp={(e) => {
                setCursor('crosshair')
                handleMouseEvent(e)
              }}
              onDoubleClick={handleMouseEvent}
              onMouseMove={handleMouseEvent}
              onMouseOver={handleMouseEvent}
              onMouseOut={handleMouseEvent}
              onMouseEnter={handleMouseEvent}
              onMouseLeave={handleMouseEvent}
              onContextMenu={(e) => {
                e.preventDefault()
                handleMouseEvent(e)
              }}
              className={`mx-auto block cursor-${cursor} rounded-xl bg-slate-950 shadow-inner`}
            />

            {/* Status Strip */}
            <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-2">
                Active: <b className="ml-1 text-slate-100">{activeId ?? '—'}</b>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-2">
                Hover: <b className="ml-1 text-slate-100">{hoverId ?? '—'}</b>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-2">
                Payload: <b className="ml-1 text-slate-100">{payloadSize}</b> bytes
              </div>
            </div>
          </div>
        </main>

        {/* Right Sidebar: Event Stream */}
        <aside className="flex max-h-[560px] flex-col gap-2 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-3">
          <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wider text-slate-400">
            <PackageSearch className="h-4 w-4" /> Event Stream
          </div>
          <div className="scrollbar-thin scrollbar-thumb-slate-700/50 scrollbar-track-transparent min-h-0 flex-1 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-2">
            {lastEvent ? (
              <pre className="whitespace-pre-wrap break-words text-[11px] leading-relaxed text-slate-300">{JSON.stringify(lastEvent, null, 2)}</pre>
            ) : (
              <div className="text-xs text-slate-500">No events yet. Interact with the canvas to see payloads here.</div>
            )}
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 hover:border-slate-700">
              <Save className="mr-1 inline h-3.5 w-3.5" /> Save
            </button>
            <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 hover:border-slate-700">
              <Upload className="mr-1 inline h-3.5 w-3.5" /> Import
            </button>
            <button className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 hover:border-slate-700">
              <Download className="mr-1 inline h-3.5 w-3.5" /> Export
            </button>
          </div>
        </aside>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-2 text-[11px] text-slate-400">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <Car className="h-3.5 w-3.5" /> Automotive Labeling Theme
            </span>
            <span className="flex items-center gap-1">
              <Waypoints className="h-3.5 w-3.5" /> Crosshair + Grid
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1">
              <Cpu className="h-3.5 w-3.5" /> v0.1
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
