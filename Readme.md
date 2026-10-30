# web-framework

One small shop service, served by **FastAPI**, **Litestar** or **BlackSheep**, and a benchmark that measures each framework under exactly the same load and compares them. The shop does real work on every request — a SQLite database, calls to (fake, deterministic) external APIs, prices and totals, streams — so the comparison reflects a realistic service, not an empty "hello world".

**[Using web-framework](#using-web-framework)** — run a framework, benchmark it, read the reports.
**[Working on web-framework](#working-on-web-framework)** — how it is built and how to extend it.

```text
  make run_<framework>                      make benchmark                     make benchmark_report
  ┌─ Granian, 1 worker ──────────────┐      ┌─ shop_benchmark ────────────┐    ┌─ comparison ────────────┐
  │  FastAPI │ Litestar │ BlackSheep │ ◄─── │ preflight ► oha load ► probe│ ─► │ latest run of each      │
  │          └────────┬─────────────┘│      └──────────────┬──────────────┘    │ framework ► final .md   │
  │   shop: same use cases, SQLite,  │                     ▼                   │ and .json               │
  │   fake inventory/pricing/market  │      reports/benchmark/<framework>/      └─────────────────────────┘
  └──────────────────────────────────┘      <time>.json and .md
```

---

## Using web-framework

### Install

Requirements: Python 3.14, [uv](https://docs.astral.sh/uv/) and [oha](https://github.com/hatoo/oha), the load generator.

```bash
uv sync --group dev
brew install oha
```

### The shop

Every framework serves the same endpoints, with the same answers byte for byte:

| Endpoint | Kind | Work done for each request |
|---|---|---|
| `GET /v1/products/{sku}` | JSON | Product from the database, stock and tax from two APIs called in parallel, price with tax |
| `POST /v1/orders` | JSON | Validates the order, reads its products, quote from the pricing API, totals with discount and tax, stores the order |
| `GET /v1/products/{sku}/events` | stream (SSE) | Price and stock updates paced by a market feed, then an `end` event |
| `POST /v1/orders/track` | stream (SSE) | The order's stages: received, validated, priced, reserved (inventory API), confirmed (stored) |
| `GET /v1/products/{sku}/image` | binary | The product's image, read from the database |
| `POST /v1/files` | binary | Stores the uploaded bytes and answers their SHA-256 (32 bytes) |
| `GET /v1/products/{sku}/label` | text | A shelf label rendered from the product, its stock and price |
| `POST /v1/notes` | text | Normalises the text, counts lines and words, stores it, answers a summary |
| `GET /v1/about` | JSON | Which framework, version, server and Python answer (used by the benchmark) |
| `GET /actuator/health`, `/health/readiness`, `/info` | JSON | Health and version |

An unknown SKU answers `404 {"detail": "No product '…'"}`. With `WEB_DOCS=true`, the API documentation is at `/docs`.

**Everything is deterministic.** At each start the database is rebuilt and seeded from a fixed seed (500 products `SKU-00001` to `SKU-00500`, 64 KiB images). The fake APIs answer from a formula and wait a fixed time set in the configuration. Orders, files and notes are stored under a key computed from their content, so the database does not grow during a benchmark.

### Benchmark the frameworks

One framework at a time, in two terminals:

```bash
make run_litestar        # terminal 1: the shop, served by Litestar
```

```bash
make benchmark           # terminal 2: about 10 minutes with the default control panel
```

Stop the shop (Ctrl-C), then do the same with `make run_fastapi` and `make run_blacksheep`. When every framework has run:

```bash
make benchmark_report
```

`make run_<framework>` starts every framework with the same Granian settings: one worker, one runtime thread, uvloop, no access log, `WARNING` logs, on `127.0.0.1:8765` (`PORT=…` to change it, and `BASE_URL=…` for the benchmark).

What `make benchmark` does:

1. Asks `/v1/about` which framework is running: the report is named after it, so you cannot mislabel a run.
2. **Preflight**: calls every endpoint once and checks its status, media type and body. Nothing is measured if one answers wrongly.
3. For each load profile and each endpoint: a warm-up, then the measured run with oha, while the server's CPU and memory are sampled.
4. Writes `reports/benchmark/<framework>/<start time>.json` and `.md`.

Useful variables: `DURATION=5` and `WARMUP=1` (seconds, every profile), `CONNECTIONS=128`, `ENDPOINTS=get_json,post_stream`, `PROFILES=throughput`, `OUTPUT_DIR=…`, `DRY_RUN=1` (print the plan only). `make benchmark_quick` is a 3-second run of everything, to check the setup.

### The control panel

`src/shop_benchmark/control_panel.json` (`BENCH_PANEL=…` for another one):

| Key | Meaning |
|---|---|
| `target.base_url` | Where the shop answers |
| `load.profiles` | The load every endpoint receives. Without `rate_per_second`: as many requests as `connections` allow, for `duration_seconds` (**throughput**). With it: exactly that rate, latency corrected for requests that had to wait (**fixed rate**) |
| `load.warmup_seconds`, `load.pause_seconds` | Warm-up before each measured run, pause after it |
| `workload` | What requests carry: the product, the order size, the upload size, the note length |
| `probe` | CPU and memory sampling of the server process (local targets only) |
| `endpoints` | Which endpoints to run; empty runs all |
| `output_dir` | Where reports go |

### The reports

**Per framework** (`reports/benchmark/<framework>/<time>.md`): the service, server, machine and load; then for each profile a table per endpoint with requests per second, p50 / p90 / p99 / max latency, time to first byte, MB/s, failures, server CPU and memory; then the preflight answers. The `.json` holds the same data.

**Comparison** (`reports/benchmark/final_<time>.md`), built from the latest run of each framework:

- **Summary**: a score per framework and profile (100 = best on every endpoint), the number of endpoints each framework won, its peak memory.
- **Same work everywhere**: confirms every framework returned the same bytes for every endpoint.
- **Per profile**: requests per second (throughput) or p99 latency (fixed rate) per endpoint and framework, the best in bold, how far behind the others are.
- **Server resources** and **how to read** the numbers.

`final_<time>.json` concatenates the runs of every framework with the computed comparison.

### Configure the shop

| Variable | Default | Meaning |
|---|---|---|
| `APP_ENV` | `debug` | Which `config/<APP_ENV>/` folder is read |
| `LOG_LEVEL` | `WARNING` | Log level; keep `WARNING` while benchmarking |
| `SHOP_DB_DIR` | `./var/db` | Folder of the SQLite database, rebuilt at each start |
| `WEB_BASE_PATH` | empty | A prefix for every route |
| `WEB_DOCS` | `false` | `true` serves the API documentation at `<base path>/docs` |

The work the shop does is set in `config/debug/`:

| File | What you set there |
|---|---|
| `server/asgi.yml` | `parameters`: the seed, the number of products, the image size |
| `operation/inventory.yml`, `pricing.yml` | `latency_ms`: how long each fake API call takes |
| `operation/market.yml` | `ticks` and `interval_ms`: the length and pace of the product stream |
| `connector/database.yml` | The SQLite database and its connection pool |

### Keeping the comparison fair

- Run every framework on the same machine, with the same control panel, and close what else uses the CPU.
- The load generator runs on the same machine and uses CPU too: the absolute numbers belong to that machine.
- Run each framework more than once; differences under about 5 % are noise.
- The final report says if the frameworks did not all return the same answers: then they did not do the same work.

---

## Working on web-framework

### Architecture

Hexagonal, like agent-runtime: the shop knows nothing about web frameworks; each framework is wired at the edge, in `bootstrap/application/<framework>/`, with its own native features. The benchmark is a separate program that only talks HTTP.

```text
  ┌─ bootstrap ──────────────────────────────────────────────────────────────┐
  │  configuration, DI, container (boot: schema, seed, use cases)            │
  │  application/fastapi │ litestar │ blacksheep : routes, schemas, the app  │
  │  ┌─ shop.adapter ─────────────────────────────────────────────────────┐  │
  │  │  inbound:  SSE presenter (shared by every framework)               │  │
  │  │  outbound: SQLite repositories, fake inventory/pricing/market APIs │  │
  │  │  ┌─ shop.application ───────────────────────────────────────────┐  │  │
  │  │  │  one use case per endpoint, ports                            │  │  │
  │  │  │  ┌─ shop.domain ──────────────────────────────────────────┐  │  │  │
  │  │  │  │  Product, Order, Note, Label, pricing rules            │  │  │  │
  │  │  │  └────────────────────────────────────────────────────────┘  │  │  │
  │  │  └──────────────────────────────────────────────────────────────┘  │  │
  │  └────────────────────────────────────────────────────────────────────┘  │
  └──────────────────────────────────────────────────────────────────────────┘
  shop_benchmark: domain ◄ application (ports) ◄ adapters (oha, httpx, psutil, reports) ◄ bootstrap (CLI)
```

`tests/architecture/test_boundaries.py` enforces it: the domain and the application import no framework; the shop imports no web framework and never `bootstrap`; each framework folder imports only its own framework; the benchmark never imports the shop.

### Project layout

| Path | What it holds |
|---|---|
| `src/shop/domain/` | `Product`, `ProductOffer`, `Label`, `OrderRequest`, `Order` (pricing rules), `TrackingEvent`, `Tick`, `StoredFile`, `Note` |
| `src/shop/application/` | One use case per endpoint (`GetProduct`, `PlaceOrder`, `FollowProduct`, `TrackOrder`, …), their inbound ports, the outbound ports, `ShopUseCases` |
| `src/shop/adapter/inbound/web/stream/` | `SsePresenter`: ticks and tracking events as SSE frames, the same bytes for every framework |
| `src/shop/adapter/outbound/sqlite/` | Schema, deterministic catalogue seed, repositories (pycraftcore's pooled SQLite) |
| `src/shop/adapter/outbound/api/` | Fake inventory, pricing and market APIs: fixed latency, answers from a formula |
| `src/bootstrap/` | Settings, `ShopDI` (wiring only), `ShopContainer`, `shop_application.py` (one factory per framework, Granian's targets) |
| `src/bootstrap/application/<framework>/` | `router/` (the routes, native), `schema/` (bodies: pydantic for FastAPI and BlackSheep, msgspec for Litestar), `<framework>_api.py` (the app, built with pycraftcore's toolkit) |
| `src/shop_benchmark/` | The benchmark: `domain/` (endpoint, profile, measurement, report, comparison), `application/` (`Benchmark`, `Preflight`, `CompareFrameworks`), `adapter/` (oha, httpx target, process probe, reports), `workload/` (the eight requests), `configuration/`, `bootstrap/` (CLI), `control_panel.json` |
| `config/` | YAML configuration (pycraftcore `application_configuration`) |
| `tests/` | Unit, adapter, contract (every framework, same bytes) and architecture tests |

### A request, start to finish

```text
oha ──GET /v1/products/SKU-00042──► Granian ─► Litestar (pycraftcore.web_litestar: request id, docs, base path)
                                                 └─► ShopRouter.get_product (msgspec)  ◄─ ShopUseCases injected
                                                       └─► GetProduct.handle
                                                             ├─ SqliteProductRepository.product      SQLite
                                                             ├─ FakeInventoryApi.stock   ┐ in parallel
                                                             └─ FakePricingApi.quote     ┘ fixed latency
                                                       ◄── ProductOffer ─► ProductSchema ─► JSON
```

### Making changes

| To add | Do |
|---|---|
| An endpoint | A use case and its port in `shop/application/`, wired in `ShopDI._use_cases` and `ShopUseCases`; a route in each `bootstrap/application/<framework>/router/`; its request in `shop_benchmark/workload/catalog.py`; a line in the contract test's `ENDPOINTS` |
| A framework | A pycraftcore toolkit for it (`pycraftcore.web_<name>`), then `bootstrap/application/<name>/` like the others, a `create_<name>_application` in `shop_application.py`, a `run_<name>` target, its folder in the architecture test and the contract tests' `EVERY_FRAMEWORK` |
| A load profile | An entry in `load.profiles` of the control panel; the reports and the comparison pick it up |
| More realistic work | Change the latencies, catalogue size or image size in `config/debug/`, or a fake API in `shop/adapter/outbound/api/` |

### Tests and checks

```bash
make check        # ruff + ty + pytest
make test
```

The contract tests start each framework's real app and check that all three answer every endpoint with the same bytes, the same media types and the same errors.
