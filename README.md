# DataFlow — E-Commerce Analytics Dashboard

### Business Intelligence · Data Engineering · QA Automation

DataFlow is an end-to-end Python analytics project that turns e-commerce CSV data into validated business records, SQL-based KPIs, JSON APIs, and an interactive dashboard.

Built with the Olist Brazilian E-Commerce dataset, the project combines BI development with a strong emphasis on automated testing, data-quality reporting, and reproducible engineering workflows.

## At a Glance

| Capability | Result |
|---|---|
| Business analytics | 99,441 orders available through the API and dashboard |
| Data ingestion | 443,707 input rows processed across five datasets |
| Quality reporting | 442,893 accepted rows; 814 duplicate-key review rows reported |
| Backend automation | 55 tests passed |
| Browser automation | 5 Playwright tests passed |
| Overall statement coverage | 80% displayed |
| Linting | Ruff checks passed; exit code `0` |
| REST API | Four FastAPI endpoints |
| Document storage | MongoDB ingestion metadata and quality reports |
| Performance testing | Local five-user Locust baseline completed |
| CI configuration | Windows-compatible Jenkins pipeline |
| Reproducibility | Included synthetic sample data and isolated test databases |

**60 automated test cases passed across the backend and browser suites.**

---

## Business Objective

E-commerce reporting needs more than attractive charts. Reliable analysis requires:

- Validated source records.
- Consistent metric definitions.
- Correct handling of one-to-many relationships.
- Predictable API responses.
- Visible data-quality findings.
- Repeatable tests that catch regressions.

DataFlow brings these responsibilities together in a small application designed to be understandable, testable, and easy to run locally.

## Architecture

```text
Real Olist CSVs / Synthetic Sample CSVs
                  |
                  v
        Pandas Validation Pipeline
                  |
          +-------+--------+
          |                |
          v                v
       SQLite           MongoDB
  Business Records   Operational Documents
          |           - ingestion_runs
          |           - quality_reports
          v                |
    SQL Analytics          |
          |                |
          +-------+--------+
                  |
         +--------+--------+
         |                 |
         v                 v
      FastAPI           Streamlit
     JSON APIs       Plotly Dashboard

Quality Assurance:
Pytest · HTTPX · Mocked MongoDB · Playwright · Locust · Ruff

Continuous Integration:
Jenkins Pipeline
```

SQLite is the source for business analytics. MongoDB stores operational documents rather than duplicating business records.

The Streamlit dashboard reads SQLite directly. FastAPI exposes the analytics through a separate REST interface.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Application and test implementation |
| Pandas | CSV processing and validation |
| SQLite | Relational storage and SQL aggregations |
| MongoDB / PyMongo | Ingestion metadata and quality documents |
| FastAPI / Pydantic | API endpoints and response schemas |
| Streamlit | Interactive dashboard |
| Plotly | Data visualizations |
| Pytest | Test orchestration |
| HTTPX / FastAPI TestClient | API testing |
| Playwright | Real Chromium browser automation |
| pytest-cov | Coverage reporting |
| Ruff | Static analysis and linting |
| Locust | Lightweight API load testing |
| Jenkins | Continuous-integration pipeline |
| Git | Version control and review workflow |

---

## Dashboard and Business Analytics

### Dashboard Features

- Total, delivered, and cancelled order counts.
- Merchandise sales and average order value.
- Average customer review score.
- Orders over time.
- Sales by product category.
- Top 10 categories by sales.
- Order-status distribution.
- Date and order-status controls.
- Helpful empty state when no orders match.
- Latest available MongoDB quality report.

### Recorded Results: Real Olist Dataset

| KPI | Observed Value |
|---|---:|
| Total orders | 99,441 |
| Delivered orders | 96,478 |
| Cancelled orders | 625 |
| Merchandise sales | R$13,496,408.43 |
| Average order value | R$137.43 |
| Average review score | 4.09 |

These results reflect the locally ingested dataset and the metric definitions below.

### KPI Definitions

| Metric | Definition |
|---|---|
| Total orders | Count of orders matching the selected filters |
| Delivered orders | Matching orders with status `delivered` |
| Cancelled orders | Matching orders with status `canceled` |
| Merchandise sales | Sum of accepted order-item prices for non-cancelled matching orders |
| Average order value | Merchandise sales divided by distinct non-cancelled matching orders with at least one stored order item |
| Average review score | Mean stored review score for matching orders |

Merchandise sales excludes freight and is not labelled as total customer payment.

Order counts are calculated from the orders table rather than an expanded order-item join, preventing multi-item orders from inflating order counts.

---

## Data Pipeline and Quality Reporting

### Supported Source Datasets

- Customers
- Products
- Orders
- Order items
- Reviews

### Validation Rules

| Condition | Handling |
|---|---|
| Missing required column | Clear validation error |
| Missing order ID in orders or order items | Row rejected |
| Invalid purchase timestamp | Order rejected |
| Missing, invalid, or negative item price | Order item rejected |
| Duplicate configured primary key | First occurrence retained; later occurrences reported as rejected |
| Missing product category | Replaced with `unknown` |
| Missing customer city or state | Replaced with `unknown` |
| Missing or nonnumeric freight | Replaced with zero |
| Missing or out-of-range review score | Review rejected |
| Reviews file absent | Pipeline continues; review KPI is unavailable |

### Recorded Ingestion Results

| Measure | Count |
|---|---:|
| Input rows | 443,707 |
| Accepted rows | 442,893 |
| Rejected rows | 814 |
| Duplicate-key review rows | 814 |

```text
442,893 accepted + 814 rejected = 443,707 input rows
```

Every pipeline run receives a unique run ID.

### Interpreting the Quality Report

- Row counts cover all loaded datasets, not only orders.
- Accepted rows are accepted by cleaning; they are not necessarily newly inserted database rows.
- Repeated ingestion uses primary keys and `INSERT OR IGNORE` to prevent duplicate inserts.
- Existing database keys are retained rather than updated.
- Missing-value counts cover retained CSV data, including additional source columns.
- Review deduplication currently uses `review_id`; duplicate-key counts do not necessarily mean identical full-row duplicates.

---

## Database Design

### SQLite: Business Records

```text
customers
products
orders
order_items
reviews
```

The schema declares primary keys and relational references. Analytics queries use parameterized filter values.

### MongoDB: Operational Documents

```text
ingestion_runs
quality_reports
```

Each collection uses a unique `run_id` index. Repository writes use upserts to avoid accidental duplicate documents for the same run.

### Example Ingestion Metadata

Illustrative document:

```json
{
  "run_id": "example-run-id",
  "status": "completed",
  "started_at": "2026-10-23T08:39:30+00:00",
  "completed_at": "2026-10-23T08:39:33+00:00",
  "input_rows": 443707,
  "accepted_rows": 442893,
  "rejected_rows": 814,
  "error_summary": null
}
```

### Example Quality Report

Illustrative JSON representation:

```json
{
  "run_id": "example-run-id",
  "created_at": "2026-10-23T08:39:33.281000",
  "total_rows": 443707,
  "accepted_rows": 442893,
  "rejected_rows": 814,
  "missing_values": {
    "customers": 0,
    "products": 1838,
    "orders": 4908,
    "order_items": 0,
    "reviews": 144633
  },
  "duplicate_counts": {
    "customers": 0,
    "products": 0,
    "orders": 0,
    "order_items": 0,
    "reviews": 814
  },
  "validation_findings": []
}
```

MongoDB stores report creation time as a datetime; the API serializes it in JSON responses.

### Graceful Reporting Availability

SQLite ingestion and analytics remain usable when MongoDB reporting is not configured.

The loader explicitly reports when MongoDB reporting is skipped. The API provides a clear unavailable response rather than pretending a report was saved.

---

## REST API

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Basic service/database check |
| GET | `/api/summary` | Calculated business KPIs |
| GET | `/api/orders` | Paginated order records |
| GET | `/api/quality-report` | Latest MongoDB quality report |

### Example Requests

```text
GET /api/summary
GET /api/summary?status=delivered
GET /api/summary?date_from=2017-01-01&date_to=2017-12-31
GET /api/orders?page=1&page_size=10
GET /api/orders?page=2&page_size=5&status=delivered
```

### Recorded Summary Response

```json
{
  "total_orders": 99441,
  "delivered_orders": 96478,
  "cancelled_orders": 625,
  "merchandise_sales": 13496408.43,
  "average_order_value": 137.43,
  "average_review_score": 4.09
}
```

### Response Behaviour

- Pagination requires `page >= 1`.
- Page size must be between 1 and 100.
- Invalid pagination parameters return `422`.
- An unavailable page beyond page one returns `404`.
- A missing quality report returns `404`.
- Unconfigured or unavailable MongoDB reporting returns `503`.
- Empty analytics return zero counts and unavailable averages where appropriate.

Use `/docs` for API exploration. The dashboard runs separately on port `8501`.

---

## QA Automation and Verified Results

### Latest Recorded Verification

Environment: Windows, Python 3.11.9.

| Check | Recorded Result |
|---|---|
| Backend unit, API, and integration suite | 55 passed in 15.20 seconds |
| Browser automation suite | 5 passed in 32.48 seconds |
| Ruff lint | All checks passed |
| Saved Ruff command exit code | `0` |
| Dependency consistency | `No broken requirements found` |
| Overall displayed statement coverage | 80% |

The backend run completed with two non-failing warnings: a dependency deprecation warning and a Pandas date-parsing warning.

### Coverage by Module

| Module | Statement Coverage |
|---|---:|
| `data_pipeline.py` | 97% |
| `mongo_repository.py` | 95% |
| `main.py` | 91% |
| `analytics.py` | 88% |
| `schemas.py` | 100% |
| `sql_database.py` | 100% |
| `dashboard.py` in backend coverage run | 0% |
| Overall displayed coverage | 80% |

The latest report contains 343 statements and 70 missing statements: approximately 79.59%, displayed as 80%.

The dashboard is exercised separately through Playwright. Its server-process execution is not included in the backend coverage report.

### Test Design

- Deterministic sample records with explicit expected values.
- Temporary SQLite databases for isolated backend tests.
- Mocked MongoDB clients and distinct collection mocks.
- FastAPI TestClient requests.
- Real Chromium interactions with a running Streamlit application.
- Separate sample database for browser automation.
- JUnit XML and HTML/XML coverage artifacts.

### Verified Browser Scenarios

1. Dashboard title and heading appear.
2. KPI section displays the expected sample order count.
3. Four Plotly chart containers render.
4. Selecting `delivered` changes the order count.
5. Selecting a status without matching orders displays the empty state.

These scenarios provide a browser smoke/regression suite alongside backend business-logic tests.

---

## Performance Testing

A local Locust baseline exercised the summary and orders APIs.

### Workload

```text
Target users: 5
Spawn rate: 1 user/second
Configured duration: 30 seconds
Host: http://127.0.0.1:8000
```

### Recorded Results

| Endpoint | Completed Requests | Recorded Failures | Average Response Time |
|---|---:|---:|---:|
| `/api/orders?page=1&page_size=10` | 10 | 0 | 4,083 ms |
| `/api/summary` | 8 | 0 | 5,153 ms |
| Aggregate | 18 | 0 | 4,559 ms |

Additional measurements:

- Aggregate throughput: approximately 0.70 requests/second.
- Minimum response time: approximately 2,809 ms.
- Maximum response time: approximately 8,773 ms.
- Approximate aggregate p95: 8,800 ms.

This is a local baseline for reproducible measurement and future profiling. It is not a production-capacity benchmark.

Zero recorded failures applies to this run and the checks implemented in its Locust tasks.

---

## Project Structure

```text
dataflow/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── dashboard.py
│   ├── data_pipeline.py
│   ├── analytics.py
│   ├── sql_database.py
│   ├── mongo_repository.py
│   └── schemas.py
├── data/
│   ├── raw/
│   └── sample/
├── tests/
│   ├── conftest.py
│   ├── test_pipeline.py
│   ├── test_analytics.py
│   ├── test_mongo_repository.py
│   ├── test_mongo_repository_actual.py
│   ├── test_api.py
│   └── test_integration.py
├── qa/
│   ├── test_dashboard.py
│   └── locustfile.py
├── scripts/
│   └── load_data.py
├── docs/
│   └── AGILE_WORKFLOW.md
├── requirements.txt
├── pytest.ini
├── pyproject.toml
├── Jenkinsfile
├── .env.example
├── .gitignore
└── README.md
```

Reports, browser binaries, virtual environments, and local databases are generated artifacts.

---

## Local Setup: Windows PowerShell

Run commands from the repository directory containing `app`, `tests`, and `requirements.txt`.

### Prerequisites

- Stable Python 3.11.
- MongoDB server for operational reporting.
- Git for repository workflows.
- Internet access for dependency and browser installation.

MongoDB Compass is optional. MySQL is not required.

### 1. Create the Environment

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\Activate.ps1

python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

For later sessions:

```powershell
.\.venv311\Scripts\Activate.ps1
```

### 2. Check MongoDB

For a Windows-service installation:

```powershell
Get-Service MongoDB
```

If stopped, use Administrator PowerShell:

```powershell
Start-Service MongoDB
```

Check connectivity:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 27017
```

For a manually started server, keep its MongoDB terminal open instead.

### 3. Configure the Application

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:DATAFLOW_DB_PATH = "data/dataflow.sqlite"
$env:MONGO_URI = "mongodb://127.0.0.1:27017"
```

The MongoDB repository defaults to database `dataflow`.

Environment variables apply to the current terminal and child processes. Set them in each application terminal where required.

`.env.example` documents configuration; the PowerShell commands above explicitly configure this workflow.

### 4. Load Sample Data

```powershell
python scripts/load_data.py --data-dir data/sample --db data/dataflow.sqlite
```

The sample workflow requires no Kaggle download.

Keep sample and real data in separate SQLite databases.

### 5. Start FastAPI

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

### 6. Start Streamlit

Open another terminal in the same repository directory:

```powershell
.\.venv311\Scripts\Activate.ps1

$env:PYTHONPATH = (Get-Location).Path
$env:DATAFLOW_DB_PATH = "data/dataflow.sqlite"
$env:MONGO_URI = "mongodb://127.0.0.1:27017"

python -m streamlit run app/dashboard.py --server.port 8501
```

Open:

```text
http://localhost:8501
```

Stop either application using `Ctrl+C`.

---

## Use the Real Olist Dataset

Dataset:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Download and extract the dataset manually. The application does not download external data at runtime.

Place these files in `data/raw/`:

| Original Filename | Required Project Filename |
|---|---|
| `olist_orders_dataset.csv` | `orders.csv` |
| `olist_order_items_dataset.csv` | `order_items.csv` |
| `olist_products_dataset.csv` | `products.csv` |
| `olist_customers_dataset.csv` | `customers.csv` |
| `olist_order_reviews_dataset.csv` | `reviews.csv` |

### Required Columns

| File | Required Columns |
|---|---|
| `orders.csv` | `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp` |
| `order_items.csv` | `order_id`, `order_item_id`, `product_id`, `price`, `freight_value` |
| `products.csv` | `product_id`, `product_category_name` |
| `customers.csv` | `customer_id`, `customer_city`, `customer_state` |
| `reviews.csv` | `review_id`, `order_id`, `review_score` |

Extra source columns are supported. Reviews are optional; all five files are recommended for the full workflow.

### Load a Separate Real-Data Database

```powershell
$env:DATAFLOW_DB_PATH = "data/olist.sqlite"

python scripts/load_data.py --data-dir data/raw --db data/olist.sqlite
```

Before starting the API and dashboard, set this in both terminals:

```powershell
$env:DATAFLOW_DB_PATH = "data/olist.sqlite"
```

Using separate database paths prevents synthetic records from mixing with real records.

---

## Reproduce the Quality Checks

### Backend Tests and Coverage

Run in a dedicated test terminal:

```powershell
.\.venv311\Scripts\Activate.ps1

Remove-Item Env:MONGO_URI -ErrorAction SilentlyContinue
Remove-Item Env:MONGO_DATABASE -ErrorAction SilentlyContinue

$env:PYTHONPATH = (Get-Location).Path

New-Item -ItemType Directory -Force -Path reports | Out-Null

python -m pytest tests -ra --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:reports/coverage.xml --junitxml=reports/test-results.xml
```

MongoDB is intentionally unset here because the backend tests supply mocks where required.

Open coverage:

```powershell
Start-Process .\htmlcov\index.html
```

### Individual Test Suites

```powershell
python -m pytest tests/test_pipeline.py -ra
python -m pytest tests/test_analytics.py -ra
python -m pytest tests/test_mongo_repository.py tests/test_mongo_repository_actual.py -ra
python -m pytest tests/test_api.py -ra
python -m pytest tests/test_integration.py -ra
```

### Browser Tests

Install Chromium once:

```powershell
python -m playwright install chromium
```

Prepare the isolated sample database:

```powershell
Remove-Item Env:MONGO_URI -ErrorAction SilentlyContinue

python scripts/load_data.py --data-dir data/sample --db data/ui-test.sqlite
```

Run:

```powershell
python -m pytest qa/test_dashboard.py -v --junitxml=reports/ui-test-results.xml
```

The browser fixture starts a separate Streamlit instance on port `8599` and uses `data/ui-test.sqlite`.

### Ruff Lint

```powershell
python -m ruff check app tests qa scripts
```

Save the result:

```powershell
python -m ruff check app tests qa scripts > reports/ruff-results.txt
$LASTEXITCODE
```

Recorded result:

```text
All checks passed!
0
```

### Formatting

Apply formatting:

```powershell
python -m ruff format app tests qa scripts
```

Check formatting without changing files:

```powershell
python -m ruff format --check app tests qa scripts
```

### Locust

With the API running in a separate terminal:

```powershell
python -m locust -f qa/locustfile.py --host=http://127.0.0.1:8000 --headless -u 5 -r 1 -t 30s --csv=reports/locust
```

Inspect results:

```powershell
Get-Content .\reports\locust_stats.csv
Get-Content .\reports\locust_failures.csv
```

---

## Jenkins Continuous Integration

A Windows-compatible Jenkins pipeline is configured to automate the quality workflow.

### Pipeline Stages

```text
Checkout
   |
Python Environment and Dependencies
   |
Ruff Lint
   |
Backend Tests and Coverage
   |
Browser Setup and Sample Ingestion
   |
Playwright Tests
   |
JUnit Reporting and Artifact Archiving
```

### Agent Prerequisites

- Windows agent with the label expected by the Jenkinsfile.
- Python 3.11 and an accessible Python launcher.
- Git.
- Pipeline, Git, and JUnit plugins.
- Network access for dependencies and Chromium.
- Permission to start local browser/server processes.

The pipeline uses mocked MongoDB operations and deterministic sample data rather than requiring the real dataset.

### Run the Pipeline

1. Push the repository and Jenkinsfile to GitHub.
2. Create a Jenkins Pipeline job.
3. Select `Pipeline script from SCM`.
4. Configure the Git repository and branch.
5. Set the script path to `Jenkinsfile`.
6. Run `Build Now`.
7. Review stage results, JUnit results, and archived reports.

Keep `app/`, `tests/`, `requirements.txt`, and `Jenkinsfile` at the repository root, or adjust the pipeline working directory accordingly.

The verification tables above report the supplied local execution results. Jenkins build-specific evidence is available through the configured job.

---

## Engineering Challenges and Solutions

### Reproducible Python Environment

An initial Python `3.10.0rc2` environment encountered a Streamlit/Tornado WebSocket initialization error.

The project was moved to a clean Python 3.11 environment. Dependencies were reinstalled, and the dashboard, backend tests, and browser tests subsequently ran successfully.

### Browser Synchronization

An immediate title assertion observed Streamlit's initial loading title rather than the final application title.

The test was changed to use retrying Playwright assertions, synchronizing with visible application state.

### Accessible Custom-Control Automation

Streamlit's status selector is a custom combobox rather than a native HTML `<select>`.

Tests now interact through accessible combobox and option roles, then verify the resulting KPI change.

### Correct MongoDB Mock Behaviour

An initial mock shared one collection object across two collection names, combining their index calls.

Distinct collection mocks were introduced so tests verify each collection's unique-index setup and repository behaviour independently.

### Code Quality Cleanup

Ruff identified unused imports, combined imports, semicolon-separated statements, and assigned lambda expressions.

The code was cleaned up through standard fixes, formatting, and explicit test refactoring. Backend and browser suites were rerun successfully afterward.

### Isolated Test Data

Real analytics and deterministic browser tests use separate SQLite databases.

MongoDB reporting is disabled during sample-test preparation so a sample report does not replace the real dashboard's latest operational report.

---

## Git and Collaboration Workflow

Example feature-branch workflow:

```powershell
git switch -c feature/quality-report-tests

git add app tests qa scripts docs README.md Jenkinsfile
git diff --cached

git commit -m "test: strengthen repository and dashboard verification"
git push -u origin feature/quality-report-tests
```

### Pull Request Contents

- Change summary.
- Associated task or user story.
- Test commands and results.
- Screenshots for dashboard changes.
- Any changes to KPI definitions or data-quality rules.

### Review Checklist

- Expected values are explicitly defined.
- SQL filter values are parameterized.
- Tests do not depend on an unconfigured external database.
- Browser and database resources are cleaned up.
- Sample data is isolated from real analytics.
- Secrets and local artifacts are excluded.
- Documentation matches implemented behaviour.

See `docs/AGILE_WORKFLOW.md` for example stories, backlog items, and a bug-report format suitable for an Agile/JIRA workflow.

---

## Troubleshooting

| Symptom | Action |
|---|---|
| `source` is not recognized | Use `.\.venv311\Scripts\Activate.ps1` in PowerShell |
| Pytest cannot find `tests` | Run from the repository directory containing `tests/` and `pytest.ini` |
| Python shows `3.10.0rc2` | Activate `.venv311`, not the old `.venv` |
| API `/` returns `404` | Use `/docs` or a defined API endpoint |
| MongoDB reporting skipped during sample setup | Expected when `MONGO_URI` is unset |
| MongoDB reporting unavailable | Check the server, port, and current terminal configuration |
| Unexpected sample totals | Check the SQLite database selected by `DATAFLOW_DB_PATH` |
| Browser installation initially times out | Check whether its retry completed successfully |
| `KeyboardInterrupt` during import | Check whether execution was interrupted before diagnosing a package failure |

---

## Security and Reproducibility

- Keep credentials and `.env` files out of version control.
- Keep local MongoDB bound to loopback for this development workflow.
- Exclude virtual environments, downloaded raw datasets, and generated databases.
- Use synthetic sample records for reproducible tests.
- Keep real analytics and test databases separate.
- Preserve test reports and performance measurements as evidence.
- Treat CI configuration and executed build results as distinct artifacts.

## Future Development

- Profile the API response-time baseline.
- Extend browser coverage to date and combined filters.
- Strengthen identifier and relationship validation.
- Evaluate the review-ID uniqueness policy.
- Collect coverage from the dashboard server process.
- Add authentication and deployment controls before public hosting.

## Skills Demonstrated

### BI and Data Engineering

- Business KPI definition.
- Relational data modelling.
- SQL aggregation and one-to-many join handling.
- Pandas validation and repeatable ingestion.
- MongoDB document modelling.
- Dashboard development and quality-report interpretation.

### QA and Automation

- Unit, API, integration, and browser testing.
- Dependency mocking.
- Temporary databases and deterministic fixtures.
- Explicit business-value assertions.
- Regression diagnosis and test repair.
- Coverage analysis and reporting.
- Static analysis.
- Load-test measurement.
- CI pipeline configuration.

---

## Dataset Attribution

This project uses the Olist Brazilian E-Commerce Public Dataset:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

The included sample CSV files are synthetic and intended for demonstrations and automated testing.