// ─────────────────────────────────────────────────────────────
// Cloudflare Worker — 텔레그램 ↔ GitHub 승인 봇
// 텔레그램에서 [발행]/[폐기] 버튼을 누르거나 "수정 1: ..." 로 답장하면
// GitHub PR을 병합/닫기/코멘트 처리한다.
//
// 필요한 환경변수 (Cloudflare Worker → Settings → Variables and Secrets):
//   TELEGRAM_BOT_TOKEN  (Secret)  텔레그램 봇 토큰
//   TELEGRAM_CHAT_ID    (Text)    내 chat_id — 이 사람만 조작 가능
//   GITHUB_TOKEN        (Secret)  GitHub 파인그레인드 토큰(Contents R/W, Pull requests R/W)
//   GH_OWNER            (Text)    aicatveo3-prog
//   GH_REPO             (Text)    Mocap_blog
//   WEBHOOK_SECRET      (Secret)  아무 긴 랜덤 문자열(웹훅 위조 방지)
// ─────────────────────────────────────────────────────────────

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("ok");

    // 웹훅 위조 방지: 텔레그램이 보낸 비밀 헤더 검증
    if (
      env.WEBHOOK_SECRET &&
      request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET
    ) {
      return new Response("forbidden", { status: 403 });
    }

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("ok");
    }

    try {
      if (update.callback_query) {
        await handleCallback(update.callback_query, env);
      } else if (update.message && update.message.text) {
        await handleMessage(update.message, env);
      }
    } catch (e) {
      // 오류가 나도 200을 돌려줘 텔레그램 재시도를 막고, 나에게만 알림
      try {
        await tg(env, "sendMessage", {
          chat_id: env.TELEGRAM_CHAT_ID,
          text: "⚠️ 처리 중 오류: " + (e && e.message ? e.message : e),
        });
      } catch {}
    }
    return new Response("ok");
  },
};

function authorized(chatId, env) {
  return String(chatId) === String(env.TELEGRAM_CHAT_ID);
}

// 버튼 탭 처리
async function handleCallback(cq, env) {
  const chatId = cq.message && cq.message.chat && cq.message.chat.id;
  if (!authorized(chatId, env)) {
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "권한이 없어요" });
    return;
  }
  const parts = String(cq.data || "").split(":");
  const action = parts[0];
  const num = parseInt(parts[1], 10);
  if (!num) {
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "잘못된 요청" });
    return;
  }

  if (action === "pub") {
    const r = await gh(env, "PUT", `/pulls/${num}/merge`, { merge_method: "squash" });
    if (r.ok) {
      await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "발행했어요 ✅" });
      await tg(env, "sendMessage", { chat_id: chatId, text: `✅ PR #${num} 발행 완료! 몇 분 뒤 사이트에 반영됩니다.` });
    } else {
      const msg = trim(await r.text());
      await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "발행 실패" });
      await tg(env, "sendMessage", { chat_id: chatId, text: `❌ PR #${num} 발행 실패:\n${msg}` });
    }
  } else if (action === "dis") {
    const r = await gh(env, "PATCH", `/pulls/${num}`, { state: "closed" });
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: r.ok ? "폐기했어요 🗑️" : "실패" });
    if (r.ok) await tg(env, "sendMessage", { chat_id: chatId, text: `🗑️ PR #${num} 폐기(닫기) 완료.` });
  } else if (action === "rev") {
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: "수정요청" });
    await tg(env, "sendMessage", {
      chat_id: chatId,
      text: `✏️ PR #${num} 수정요청은 이렇게 답장해 주세요:\n\n수정 ${num}: 더 짧게, 예시 하나 추가`,
    });
  }
}

// 텍스트 메시지 처리
async function handleMessage(msg, env) {
  const chatId = msg.chat && msg.chat.id;
  if (!authorized(chatId, env)) return;
  const text = msg.text.trim();

  // "수정 1: 내용"
  let m = text.match(/^수정\s*#?(\d+)\s*[:：]\s*([\s\S]+)/);
  if (m) {
    const num = parseInt(m[1], 10);
    const body = m[2].trim();
    const r = await gh(env, "POST", `/issues/${num}/comments`, {
      body: `✏️ (텔레그램) 수정요청: ${body}`,
    });
    await tg(env, "sendMessage", {
      chat_id: chatId,
      text: r.ok ? `📝 PR #${num}에 수정요청을 남겼어요.` : "❌ 수정요청 실패",
    });
    return;
  }

  // "발행 1" / "폐기 1"
  m = text.match(/^(발행|폐기)\s*#?(\d+)/);
  if (m) {
    const num = parseInt(m[2], 10);
    if (m[1] === "발행") {
      const r = await gh(env, "PUT", `/pulls/${num}/merge`, { merge_method: "squash" });
      await tg(env, "sendMessage", { chat_id: chatId, text: r.ok ? `✅ PR #${num} 발행 완료!` : "❌ 발행 실패" });
    } else {
      const r = await gh(env, "PATCH", `/pulls/${num}`, { state: "closed" });
      await tg(env, "sendMessage", { chat_id: chatId, text: r.ok ? `🗑️ PR #${num} 폐기 완료.` : "❌ 실패" });
    }
    return;
  }

  // 도움말
  if (text === "/start" || text === "도움말" || text.toLowerCase() === "help") {
    await tg(env, "sendMessage", {
      chat_id: chatId,
      text: "사용법:\n• 알림의 버튼으로 발행/폐기\n• 수정 1: 원하는 내용\n• 발행 1 / 폐기 1",
    });
  }
}

function trim(s) {
  return (s || "").slice(0, 300);
}

async function tg(env, method, payload) {
  return fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function gh(env, method, path, body) {
  return fetch(`https://api.github.com/repos/${env.GH_OWNER}/${env.GH_REPO}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "mocap-blog-telegram-bot",
      "content-type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}
