'use client'
import { useEffect } from 'react'

// === 이벤트 직렬화 유틸 ===
function serializeEvent(e: Event): Record<string, any> {
  const obj: Record<string, any> = {
    type: e.type,
    timeStamp: e.timeStamp,
  }

  // target 정보 (태그/ID/ClassName 정도만 저장)
  if (e.target instanceof HTMLElement) {
    obj.target = {
      tag: e.target.tagName,
      id: e.target.id,
      className: e.target.className,
    }
  }

  // enumerable 속성 자동 복사
  for (const key in e) {
    try {
      const val = (e as any)[key]
      if (typeof val !== 'function' && typeof val !== 'object') {
        obj[key] = val
      }
    } catch {
      // 일부 속성 접근 불가 → 무시
    }
  }

  return obj
}

// === 서버 전송 ===
function enqueueLog(payload: Record<string, any>) {
  fetch("http://localhost:8000/api/events", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  }).catch(err => {
    console.error("Failed to send event:", err)
  })
}

export default function Page() {
  useEffect(() => {
    // 브라우저에서 지원하는 이벤트 타입 자동 탐색
    const allEventTypes = Object.keys(window)
      .filter(k => k.startsWith('on'))
      .map(k => k.slice(2)) // 'onclick' → 'click'

    const handler = (e: Event) => {
      const payload = serializeEvent(e)
      enqueueLog(payload)
    }

    // 전체 이벤트 리스너 등록
    allEventTypes.forEach(type => {
      try {
        window.addEventListener(type, handler, { passive: true })
      } catch {
        // 일부 이벤트는 addEventListener 불가 → 무시
      }
    })

    return () => {
      allEventTypes.forEach(type => {
        try {
          window.removeEventListener(type, handler)
        } catch {}
      })
    }
  }, [])

  return (
    <main>
      <h1>범용 자동 이벤트 로깅</h1>
      <p>이 페이지에서 발생하는 거의 모든 DOM 이벤트가 자동으로 기록됩니다.</p>
    </main>
  )
}
