venv:
	uv venv

install:
	uv sync

install_dev:
	uv sync --group dev

update_dependency:
ifdef PACKAGE
	uv lock --upgrade-package $(PACKAGE)
else
	uv lock --upgrade
endif
	uv sync

test:
	uv run pytest --disable-warnings

lint:
	uv run ruff check .

fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

typecheck:
	uv run ty check

check:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

# --- run one framework (same Granian settings for all) ---------------------
PORT ?= 8765
GRANIAN = uv run granian --interface asgi --factory --host 127.0.0.1 --port $(PORT) \
	--workers 1 --runtime-threads 1 --loop uvloop --log-level warning

run_fastapi:
	$(GRANIAN) bootstrap.application.shop_application:create_fastapi_application

run_litestar:
	$(GRANIAN) bootstrap.application.shop_application:create_litestar_application

run_blacksheep:
	$(GRANIAN) bootstrap.application.shop_application:create_blacksheep_application

# --- benchmark -------------------------------------------------------------
BENCH_PANEL ?= src/shop_benchmark/control_panel.json

benchmark:
	uv run python -m shop_benchmark run --panel $(BENCH_PANEL) \
		$(if $(BASE_URL),--base-url $(BASE_URL)) \
		$(if $(DURATION),--duration $(DURATION)) \
		$(if $(WARMUP),--warmup $(WARMUP)) \
		$(if $(CONNECTIONS),--connections $(CONNECTIONS)) \
		$(if $(ENDPOINTS),--endpoints $(ENDPOINTS)) \
		$(if $(PROFILES),--profiles $(PROFILES)) \
		$(if $(OUTPUT_DIR),--output-dir $(OUTPUT_DIR)) \
		$(if $(DRY_RUN),--dry-run)

benchmark_quick:
	$(MAKE) benchmark DURATION=3 WARMUP=1

benchmark_report:
	uv run python -m shop_benchmark report --panel $(BENCH_PANEL) \
		$(if $(OUTPUT_DIR),--output-dir $(OUTPUT_DIR))

clean:
	rm -rf dist src/*.egg-info var

build:
	rm -rf dist src/*.egg-info
	uv build
