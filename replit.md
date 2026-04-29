# ANIMEFLOW

A FastAPI-based anime streaming portal. **Anilibria is the primary data source**;
Shikimori is used only as enrichment for richer descriptions / posters / ratings.

## Stack

- Python 3.11 (kept Python 3.8 source compatible — no walrus, no f-string `=`,
  no `match`, no PEP 604 `X | Y` annotations)
- FastAPI 0.110, Starlette session middleware, Jinja2 templates
- SQLAlchemy 2.0 async + aiosqlite (DB at `animeflow/data/animeflow.db`)
- Vanilla JS + Plyr.io + hls.js for the player
- Tailwind via CDN

## Data sources

### Primary: Anilibria (`anilibria.top` REST API, key-less)

- **Catalogue**: `GET /api/v1/anime/catalog/releases?page=&limit=` — paginated
  list of releases. Used to seed the top 100 titles.
- **Detail**: `GET /api/v1/anime/releases/{id_or_alias}` — full release with
  inline `episodes[]`, each carrying direct HLS URLs (`hls_480`, `hls_720`,
  `hls_1080`).
- **Search**: `GET /api/v1/app/search/releases?query=` — used by the
  resolver to find a release id when only a title is known.
- Mirror failover: every request tries `anilibria.top` first and falls back to
  `api.anilibria.app` automatically (`_anilibria_get` in `parser.py` and
  `video_provider.py`).

### Secondary: Shikimori (best-effort enrichment, never blocks)

- `GET /api/animes?search=` + `GET /api/animes/{id}` to upgrade description,
  rating, fallback poster, fallback genres.

## Episode lifecycle

1. **Parse time** — for every imported release the parser materialises an
   `Episode` row per aired episode and stores the direct HLS URLs in
   `anilibria_hls_hd / sd / fhd` plus the best-quality URL in `video_url`.
   No more "0 серий" placeholders.
2. **Auto-update** — a background task started in `lifespan` polls Anilibria
   every 30 minutes (`AUTO_UPDATE_INTERVAL` in `app/services/parser.py`).
   New episodes are appended as fresh bricks in the grid; admin log gets a
   `[OK] Синхронизировано с Anilibria: {Название} (N эп., +K новых)` line.
3. **Playback** — the front-end calls `GET /api/player/data?episode_id=` to
   get a JSON `{video_url, kind, iframe_url}` payload and swaps the iframe
   src in place, with `history.pushState` updating the URL — no page reload.

## Frontend (anime page)

- Episode grid: `display: grid; grid-template-columns: repeat(auto-fill,
  minmax(50px, 1fr)); gap: 10px` (CSS in `app/static/css/custom.css`).
- Brick clicks are intercepted by `app/static/js/player.js`; the player
  iframe is replaced in place and prev/next buttons + label are updated
  client-side.

## File map

- `animeflow/main.py` — FastAPI app, includes routers, registers lifespan
  that starts the auto-update loop.
- `animeflow/app/models/anime.py` — `Anime` and `Episode` models with
  `anilibria_id`, `anilibria_code`, and Anilibria HLS columns on `Episode`.
- `animeflow/app/services/parser.py` — Anilibria-first importer + 30-min
  auto-update loop + Shikimori enrichment.
- `animeflow/app/services/video_provider.py` — On-demand resolver used only
  when DB has no stored URL.
- `animeflow/app/routes/api.py` — `/api/player` (HTML iframe wrapper),
  `/api/player/data` (JSON for SPA brick switching), `/api/iframe`,
  `/api/search`, `/api/favorites/toggle`, `/api/progress`, `/api/episode/...`.
- `animeflow/app/routes/admin.py` — Admin panel (only user `id == 1`),
  parser run/stop, WS log stream.
- `animeflow/app/templates/anime.html` — Brick grid + AJAX player wrapper.
- `animeflow/app/static/js/player.js` — Brick click handler, history
  pushState, autoplay-next via postMessage, resume toast, favourite toggle.

## Running locally

```
cd animeflow
HOST=0.0.0.0 PORT=5000 python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

The Replit workflow `Start application` runs exactly that.

The first registered user (`user.id == 1`) is the only admin. From the admin
panel (`/admin`) you can trigger an Anilibria import; logs stream via
WebSocket and the auto-update loop kicks in automatically once the first
import completes.

## Important notes

- `database.init_db()` runs `Base.metadata.create_all` only — there are **no
  migrations**. After schema changes, delete `animeflow/data/animeflow.db`
  before restart.
- Forbidden video sources (kodik, alloha, jut.su) are explicitly filtered out
  in `video_provider.py`.
- The old Anilibria v3 API (`api.anilibria.tv/v3`) is dead (returns 410).
  Everything now goes through `anilibria.top/api/v1`.
