# Subscribe Worker

Cloudflare Worker that persists public email subscriptions to `config/subscribers.json` in the repo, so no GitHub token is exposed in the browser.

## Deploy (one-time)

```bash
npm install -g wrangler
cd worker
wrangler login
wrangler deploy
```

## Set secrets

```bash
# Fine-grained PAT: repo "deal-finder", Contents read+write
wrangler secret put GH_TOKEN

# Any 32+ char random string
wrangler secret put HMAC_SECRET
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/subscribe` | `{"email":"...","name":"..."}` — add subscriber |
| GET | `/unsubscribe?token=...&email=...` | HMAC-verified one-click unsubscribe |

## Wire up the frontend

After deploying, update `SUBSCRIBE_API` in `index.html`:

```js
const SUBSCRIBE_API = 'https://deals-subscribe.<your-account>.workers.dev';
```

Cloudflare assigns the subdomain automatically — copy it from the dashboard after `wrangler deploy`.

## Unsubscribe links in emails

`notify.py` needs to include unsubscribe links. Add this to each subscriber's email:

```
https://deals-subscribe.<your-account>.workers.dev/unsubscribe?token=<hmac>&email=<email>
```

To generate the HMAC server-side in Python:

```python
import hmac, hashlib
token = hmac.new(HMAC_SECRET.encode(), f"unsub:{email}".encode(), hashlib.sha256).hexdigest()
```

Set `HMAC_SECRET` as a GitHub Actions secret and pass it to `notify.py` via env var.
