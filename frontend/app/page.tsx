'use client';
import Image from "next/image";

export default function Home() {
  const sendPayload = (e: React.MouseEvent, relatedTarget?: HTMLElement | null) => {
    const payload = {
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
      relatedTarget: relatedTarget ? relatedTarget.outerHTML : null,
      timestamp: Date.now(),
      type: e.type,
    };

    fetch("http://localhost:8000/api/click", {
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

  const handleClick = (e: React.MouseEvent) => {
    // 클릭한 좌표에서 가장 안쪽의 요소를 찾음
    const elemAtPoint = document.elementFromPoint(e.clientX, e.clientY) as HTMLElement | null;
    sendPayload(e, elemAtPoint);
    alert("백엔드에 클릭 정보가 전송되었습니다!");
  };

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
