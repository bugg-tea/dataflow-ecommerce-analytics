# Agile Workflow

## User Stories
1. As a BI analyst, I want KPIs so I can monitor e-commerce performance.
2. As a QA engineer, I want automated tests so regressions are caught early.
3. As a data engineer, I want data-quality reports so bad records are visible.
4. As a manager, I want a dashboard so I can view trends quickly.
5. As a developer, I want API endpoints so other tools can consume analytics.
6. As a reviewer, I want CI checks so code quality is enforced.

## Example Bug Report
**Title:** Cancelled orders included in merchandise sales  
**Steps:** Load sample data, open `/api/summary`  
**Expected:** Cancelled order revenue excluded  
**Actual:** Cancelled revenue included  
**Severity:** High  

## Sprint Backlog
- Implement data pipeline
- Build SQLite schema
- Create FastAPI endpoints
- Build Streamlit dashboard
- Add unit and API tests
- Add Playwright UI tests
- Configure Jenkins CI

## Git/Bitbucket Guide
- Create feature branches: `feature/pipeline`
- Commit with clear messages: `feat: add data quality report`
- Push and open a pull request
- Require at least one review before merge
