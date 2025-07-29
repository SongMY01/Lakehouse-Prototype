'use client';
import { useEffect } from "react";
import Image from "next/image";

const logLevel = process.env.NEXT_PUBLIC_LOG_LEVEL || 'INFO';
console.info(`📄 .env에서 읽은 LOG_LEVEL: ${logLevel}`);

const log = (level: string, ...args: any[]) => {
  const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR'];
  const currentIdx = levels.indexOf(logLevel);
  const msgIdx = levels.indexOf(level);

  const consoleMap: Record<string, (...args: any[]) => void> = {
    debug: console.debug,
    info: console.info,
    warning: console.warn,
    error: console.error,
  };

  if (msgIdx >= currentIdx) {
    consoleMap[level.toLowerCase()](...args);
  }
};

export default function Home() {
  const sendPayload = (payload: Record<string, any>) => {
    fetch("http://localhost:8000/api/events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then((res) => {
        if (!res.ok) {
          log('ERROR', "전송 실패!");
          alert("전송 실패!");
        }
      })
      .catch((err) => {
        log('ERROR', "에러 발생:", err);
        alert("에러 발생!");
      });
  };

  const handleClick = (e: React.MouseEvent) => {
    const elemAtPoint = document.elementFromPoint(e.clientX, e.clientY) as HTMLElement | null;

    const payload = {
      event_type: "click",
      altKey: e.altKey,
      ctrlKey: e.ctrlKey,
      metaKey: e.metaKey,
      shiftKey: e.shiftKey,
      button: e.button,
      buttons: e.buttons,
      clientX: e.clientX,
      clientY: e.clientY,
      pageX: e.pageX,
      pageY: e.pageY,
      screenX: e.screenX,
      screenY: e.screenY,
      relatedTarget: elemAtPoint ? elemAtPoint.outerHTML : null,
      timestamp: Date.now(),
      type: e.type,
    };

    sendPayload(payload);
    log('INFO', "백엔드에 클릭 정보 전송:", payload);
    alert("백엔드에 클릭 정보가 전송되었습니다!");
  };

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
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        <button onClick={handleClick} className="cursor-pointer">
          <Image
            className="dark:invert"
            src="/next.svg"
            alt="Next.js logo"
            width={180}
            height={38}
            priority
          />
        </button>
      </main>
    </div>
  );
}