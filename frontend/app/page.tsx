'use client';
import { useEffect } from "react";
import Image from "next/image";

export default function Home() {
  /**
   * 공통으로 payload를 보내는 함수
   */
  const sendPayload = (payload: Record<string, any>) => {
    fetch("http://localhost:8000/api/event", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then((res) => {
        if (!res.ok) {
          alert("전송 실패!");
        }
      })
      .catch((err) => {
        console.error(err);
        alert("에러 발생!");
      });
  };

  /**
   * 클릭 이벤트 핸들러
   */
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
    alert("백엔드에 클릭 정보가 전송되었습니다!");
  };

  /**
   * 키보드 이벤트 등록
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const payload = {
        event_type: "keydown",
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
      console.log("키보드 이벤트 전송됨:", payload);
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
