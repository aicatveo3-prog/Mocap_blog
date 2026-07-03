// ─────────────────────────────────────────────────────────────
// Val Town (HTTP val) — 텔레그램 ↔ GitHub 승인 봇
// Cloudflare 대신 Val Town에 붙여넣는 버전. 로직은 동일.
//
// 환경변수 (Val Town → Settings → Environment Variables 에 추가):
//   TELEGRAM_BOT_TOKEN   텔레그램 봇 토큰
//   TELEGRAM_CHAT_ID     내 chat_id (숫자)
//   GITHUB_TOKEN         GitHub 파인그레인드 토큰(Contents R/W, Pull requests R/W)
//   GH_OWNER             aicatveo3-prog
//   GH_REPO              Mocap_blog
//   WEBHOOK_SECRET       아무 긴 랜덤 문자열
// ─────────────────────────────────────────────────────────────

const env = (k: string): string => Deno.env.get(k) || "";

export default async function (request: Request): Promise<Response> {
  if (request.method !== "POST") return new Response("ok");

  // 웹훅 위조 방지
  if (
    env("WEBHOOK_SECRET") &&
    request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env("WEBHOOK_SECRET")
  ) {
    return new Response("forbidden", { status: 403 });
  }

  let update: any;
  try {
    update = await request.json();
  } catch {
    return new Response("ok");
  }

  try {
    if (update.callback_query) {
      await handleCallback(update.callback_query);
    } else if (update.message && update.message.text) {
      await handleMessage(update.message);
    }
  } catch (e: any) {
    try {
      await tg("sendMessage", {
        chat_id: env("TELEGRAM_CHAT_ID"),
        text: "⚠️ 처리 중 오류: " + (e && e.message ? e.message : e),
      });
    } catch {}
  }
  return new Response("ok");
}

function authorized(chatId: any): boolean {
  return String(chatId) === String(env("TELEGRAM_CHAT_ID"));
}

async function handleCallback(cq: any): Promise<void> {
  const chatId = cq.message?.chat?.id;
  if (!authorized(chatId)) {
    await tg("answerCallbackQuery", { callback_query_id: cq.id, text: "권한이 없어요" });
    return;
  }
  const [action, numStr] = String(cq.data || "").split(":");
  const num = parseInt(numStr, 10);
  if (!num) {
    await tg("answerCallbackQuery", { callback_query_id: cq.id, text: "잘못된 요청" });
    return;
  }

  if (action === "pub") {
    const r = await gh("PUT", `/pulls/${num}/merge`, { merge_method: "squash" });
    if (r.ok) {
      await tg("answerCallbackQuery", { callback_query_id: cq.id, text: "발행했어요 ✅" });
      await tg("sendMessage", { chat_id: chatId, text: `✅ PR #${num} 발행 완료! 몇 분 뒤 사이트에 반영됩니다.` });
    } else {
      const msg = trim(await r.text());
      await tg("answerCallbackQuery", { callback_query_id: cq.id, text: "발행 실패" });
      await tg("sendMessage", { chat_id: chatId, text: `❌ PR #${num} 발행 실패:\n${msg}` });
    }
  } else if (action === "dis") {
    const r = await gh("PATCH", `/pulls/${num}`, { state: "closed" });
    await tg("answerCallbackQuery", { callback_query_id: cq.id, text: r.ok ? "폐기했어요 🗑️" : "실패" });
    if (r.ok) await tg("sendMessage", { chat_id: chatId, text: `🗑️ PR #${num} 폐기(닫기) 완료.` });
  } else if (action === "rev") {
    await tg("answerCallbackQuery", { callback_query_id: cq.id, text: "수정요청" });
    await tg("sendMessage", {
      chat_id: chatId,
      text: `✏️ PR #${num} 수정요청은 이렇게 답장해 주세요:\n\n수정 ${num}: 더 짧게, 예시 하나 추가`,
    });
  }
}

async function handleMessage(msg: any): Promise<void> {
  const chatId = msg.chat?.id;
  if (!authorized(chatId)) return;
  const text = String(msg.text).trim();

  let m = text.match(/^수정\s*#?(\d+)\s*[:：]\s*([\s\S]+)/);
  if (m) {
    const num = parseInt(m[1], 10);
    const body = m[2].trim();
    const r = await gh("POST", `/issues/${num}/comments`, { body: `✏️ (텔레그램) 수정요청: ${body}` });
    await tg("sendMessage", { chat_id: chatId, text: r.ok ? `📝 PR #${num}에 수정요청을 남겼어요.` : "❌ 수정요청 실패" });
    return;
  }

  m = text.match(/^(발행|폐기)\s*#?(\d+)/);
  if (m) {
    const num = parseInt(m[2], 10);
    if (m[1] === "발행") {
      const r = await gh("PUT", `/pulls/${num}/merge`, { merge_method: "squash" });
      await tg("sendMessage", { chat_id: chatId, text: r.ok ? `✅ PR #${num} 발행 완료!` : "❌ 발행 실패" });
    } else {
      const r = await gh("PATCH", `/pulls/${num}`, { state: "closed" });
      await tg("sendMessage", { chat_id: chatId, text: r.ok ? `🗑️ PR #${num} 폐기 완료.` : "❌ 실패" });
    }
    return;
  }

  if (text === "/start" || text === "도움말" || text.toLowerCase() === "help") {
    await tg("sendMessage", {
      chat_id: chatId,
      text: "사용법:\n• 알림의 버튼으로 발행/폐기\n• 수정 1: 원하는 내용\n• 발행 1 / 폐기 1",
    });
  }
}

function trim(s: string): string {
  return (s || "").slice(0, 300);
}

async function tg(method: string, payload: any): Promise<Response> {
  return fetch(`https://api.telegram.org/bot${env("TELEGRAM_BOT_TOKEN")}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function gh(method: string, path: string, body?: any): Promise<Response> {
  return fetch(`https://api.github.com/repos/${env("GH_OWNER")}/${env("GH_REPO")}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${env("GITHUB_TOKEN")}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "mocap-blog-telegram-bot",
      "content-type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}
