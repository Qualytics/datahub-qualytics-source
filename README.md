# datahub-qualytics

A [DataHub](https://datahub.com) metadata ingestion source for
[Qualytics](https://www.qualytics.io).

Point it at a Qualytics deployment and it publishes your data-quality metadata into
DataHub: quality checks become **assertions**, check results and anomalies become
**assertion run events**, and Qualytics profiles become **dataset and field profiles** —
on the datasets your team already browses.

> **Status: Beta, 0.1.0.** Feature-complete for its scope and verified against a live
> Qualytics deployment and DataHub 1.7. It is being proposed for inclusion in
> [`datahub-project/datahub`](https://github.com/datahub-project/datahub); until then it
> installs as a plugin and runs from the DataHub CLI.

## How it works

Qualytics profiles tables that your DataHub already catalogues from Snowflake, BigQuery,
Databricks, Postgres, S3 and similar. So this connector **attaches to those existing
datasets** rather than creating a parallel Qualytics catalog. It reconstructs each
dataset's URN from the Qualytics datastore's connection metadata — or from an explicit
`datastore_to_platform_map` — and emits only enrichment onto it:

| Qualytics | DataHub |
| --- | --- |
| Quality check | Assertion (`CUSTOM`, rule type in `nativeType`); all 49 rule types mapped |
| Check state (`is_passing`) | Assertion run event — the current verdict, and the only source of passes |
| Anomaly | Assertion run event — a failure, with Qualytics' message and offending-record count |
| Container and field profiles | Dataset profile, with per-column statistics and histograms |

Two rules keep it from damaging metadata it does not own:

- **It never creates a dataset.** A profile is written only to a dataset DataHub already
  has; for a table the warehouse source has not ingested yet, the profile is skipped and
  counted, and arrives on the first run after the table does.
- **It never soft-deletes a dataset.** Stateful ingestion removes stale *assertions*
  when a check disappears from Qualytics; the datasets it attaches to are never entered
  into its state.

It emits no schemas, tags, ownership, lineage, incidents or structured properties. See
[`docs/sources/qualytics/`](docs/sources/qualytics/) for the full concept mapping,
prerequisites, caveats and troubleshooting.

## Install

Into the environment where the DataHub CLI runs:

```bash
pip install "acryl-datahub>=1.7" "datahub-qualytics @ git+https://github.com/qualytics/datahub-qualytics-source.git"
```

The package registers itself under DataHub's `datahub.ingestion.source.plugins`
entry-point group, so `type: qualytics` works in a recipe with no changes to your DataHub
install. Until the connector is merged upstream it runs from CLI recipes only: DataHub's
[custom ingestion source guide](https://docs.datahub.com/docs/how/add-custom-ingestion-source)
notes that UI-based ingestion does not support custom sources.

## Recipe

```yaml
pipeline_name: "qualytics-acme" # required for stateful ingestion; keep it stable

source:
  type: qualytics
  config:
    base_url: "https://acme.qualytics.io/api"
    token: "${QUALYTICS_TOKEN}"
    platform_instance: "acme" # names this Qualytics deployment
    env: PROD

    datastore_to_platform_map:
      sales-warehouse: # Qualytics datastore name or id
        platform: snowflake
        platform_instance: prod-sf # the warehouse's instance, if its recipe set one
        env: PROD

    stateful_ingestion:
      enabled: true

sink:
  type: datahub-rest
  config:
    server: "https://datahub.example.com/api/gms"
    token: "${DATAHUB_TOKEN}"
```

[`qualytics_recipe.yml`](docs/sources/qualytics/qualytics_recipe.yml) is the fully
annotated version. Run `datahub ingest -c recipe.yml --test-source-connection` first: it
checks connectivity and each capability separately, and detects a `base_url` missing its
`/api` suffix.

## Running alongside the Qualytics push integration

Qualytics can also push metadata into DataHub from the Qualytics side. The two directions
are designed to run together and do not write the same aspects: the push integration owns
descriptions, structured properties (quality scores) and incidents; this connector owns
assertions, assertion run events and profiles. Nothing needs configuring on either side.

## Development

Requires Python 3.10–3.12, matching upstream DataHub.

```bash
uv venv --python 3.12
uv sync --all-extras
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy src
```

Tests are unit and golden-file tests against recorded, sanitized fixtures. Qualytics has
no public sandbox, so there is no containerised integration test. In its place, the API
contract is checked directly: `tests/unit/fixtures/openapi.json` is a slice of a real
deployment's OpenAPI spec, and tests assert that every path, query parameter and model
the connector relies on matches it. Refresh it with `scripts/capture_openapi.py`.

The design record — entity mapping, the corrections made along the way, and the
standards review with its outcomes — is in [`skill_docs/`](skill_docs/).

## Upstream layout

The repo mirrors the DataHub monorepo so the port is a mechanical copy:

| Here | `datahub-project/datahub` |
| --- | --- |
| `src/datahub_qualytics/` | `metadata-ingestion/src/datahub/ingestion/source/qualytics/` |
| `tests/unit/` (with `fixtures/` and `golden/`) | `metadata-ingestion/tests/unit/qualytics/` |
| `docs/sources/qualytics/` | `metadata-ingestion/docs/sources/qualytics/` |
| `assets/qualyticslogo.png` | `datahub-web-react/src/images/qualyticslogo.png` |

## License

Apache-2.0. See [LICENSE](LICENSE).
