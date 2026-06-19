/**
 * Brasfield Deals – Subscribe Worker
 *
 * Handles public subscribe / unsubscribe requests without exposing a GitHub
 * token to the browser.  Deploy to Cloudflare Workers.
 *
 * Required Worker secrets (set via `wrangler secret put` or the dashboard):
 *   GH_TOKEN   – GitHub fine-grained PAT with Contents read+write on deal-finder
 *
 * Environment variables (set in wrangler.toml or dashboard):
 *   GH_OWNER   jambione
 *   GH_REPO    deal-finder
 *   HMAC_SECRET  any random 32+ char string (used to sign unsubscribe tokens)
 *
 * Endpoints:
 *   POST /subscribe      { email, name? }  → adds subscriber
 *   GET  /unsubscribe?token=<hmac-token>   → deactivates subscriber
 */

const ALLOWED_ORIGINS = [
  'https://deals.jbrasfield.com',
  'http://localhost:3456',   // local preview
];

function corsHeaders(request) {
  const origin = request.headers.get('Origin') || '';
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// HMAC-SHA256 using the Web Crypto API available in Workers
async function hmac(secret, message) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(message));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, '0')).join('');
}

async function makeUnsubToken(email, secret) {
  return hmac(secret, `unsub:${email}`);
}

// Read config/subscribers.json from the repo via Contents API
async function readSubscribers(env) {
  const url = `https://api.github.com/repos/${env.GH_OWNER}/${env.GH_REPO}/contents/config/subscribers.json`;
  const resp = await fetch(url, {
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'deals-subscribe-worker',
    },
  });
  if (!resp.ok) throw new Error(`GitHub read ${resp.status}`);
  const data = await resp.json();
  const content = JSON.parse(atob(data.content.replace(/\n/g, '')));
  return { content, sha: data.sha };
}

// Write config/subscribers.json back to the repo
async function writeSubscribers(env, content, sha) {
  const url = `https://api.github.com/repos/${env.GH_OWNER}/${env.GH_REPO}/contents/config/subscribers.json`;
  const body = JSON.stringify({
    message: 'chore: update subscribers [skip ci]',
    content: btoa(JSON.stringify(content, null, 2) + '\n'),
    sha,
  });
  const resp = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'deals-subscribe-worker',
    },
    body,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`GitHub write ${resp.status}: ${text}`);
  }
}

// POST /subscribe
async function handleSubscribe(request, env) {
  let body;
  try { body = await request.json(); } catch { return json({ error: 'Invalid JSON' }, 400); }

  const email = (body.email || '').trim().toLowerCase();
  const name  = (body.name  || '').trim();
  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json({ error: 'Invalid email address' }, 400);
  }

  const { content, sha } = await readSubscribers(env);
  const subs = content.subscribers || [];
  const existing = subs.find(s => s.email.toLowerCase() === email);

  if (existing) {
    if (existing.active) {
      return json({ message: `${email} is already subscribed.` }, 200);
    }
    existing.active = true;
    if (name) existing.name = name;
  } else {
    subs.push({ email, name: name || '', active: true });
  }
  content.subscribers = subs;

  await writeSubscribers(env, content, sha);

  const token = await makeUnsubToken(email, env.HMAC_SECRET);
  const unsubUrl = `https://deals-subscribe.jbrasfield.workers.dev/unsubscribe?token=${token}&email=${encodeURIComponent(email)}`;

  return json({
    message: `You're subscribed! You'll receive the top 5 deals by email. Unsubscribe anytime: ${unsubUrl}`,
  }, 201);
}

// GET /unsubscribe?token=...&email=...
async function handleUnsubscribe(request, env) {
  const url = new URL(request.url);
  const email = (url.searchParams.get('email') || '').trim().toLowerCase();
  const token = url.searchParams.get('token') || '';

  if (!email || !token) return html('<h2>Missing parameters.</h2>', 400);

  const expected = await makeUnsubToken(email, env.HMAC_SECRET);
  if (expected !== token) return html('<h2>Invalid unsubscribe link.</h2>', 400);

  const { content, sha } = await readSubscribers(env);
  const sub = (content.subscribers || []).find(s => s.email.toLowerCase() === email);
  if (!sub || !sub.active) {
    return html('<h2>Already unsubscribed.</h2>', 200);
  }
  sub.active = false;
  await writeSubscribers(env, content, sha);

  return html(`
    <html><body style="font-family:sans-serif;max-width:480px;margin:60px auto;text-align:center">
      <h2 style="color:#1B2438">Unsubscribed</h2>
      <p>${email} has been removed from Brasfield Deals emails.</p>
      <a href="https://deals.jbrasfield.com">Back to deals</a>
    </body></html>
  `, 200);
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function html(body, status = 200) {
  return new Response(body, { status, headers: { 'Content-Type': 'text/html' } });
}

export default {
  async fetch(request, env) {
    const cors = corsHeaders(request);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors });
    }

    const url = new URL(request.url);
    let response;

    try {
      if (request.method === 'POST' && url.pathname === '/subscribe') {
        response = await handleSubscribe(request, env);
      } else if (request.method === 'GET' && url.pathname === '/unsubscribe') {
        response = await handleUnsubscribe(request, env);
      } else {
        response = json({ error: 'Not found' }, 404);
      }
    } catch (e) {
      console.error(e);
      response = json({ error: `Worker error: ${e.message}` }, 500);
    }

    // Attach CORS headers to every response
    const headers = new Headers(response.headers);
    for (const [k, v] of Object.entries(cors)) headers.set(k, v);
    return new Response(response.body, { status: response.status, headers });
  },
};
