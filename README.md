# InsightOps AI

## Agentic Data Analyst & Business Intelligence Platform

InsightOps AI is a full-stack AI/data analytics platform that lets users upload CSV datasets, inspect dataset profiles, ask business questions in natural language, and receive pandas-backed computed answers with an analysis plan, supporting table, and calculation trace.

This project is being built as a production-style AI software engineering portfolio project, not a basic chatbot demo.

---

## Current Phase

### Phase 1 MVP: CSV Upload + Dataset Profiling + Pandas Analysis

Current working flow:

1. Upload a CSV dataset
2. Generate dataset profile
3. Detect identifier, metric, numeric, categorical, and date-like columns
4. Preview uploaded dataset
5. Ask a business question
6. Generate a structured analysis plan
7. Run pandas-backed calculations
8. Display computed answer
9. Display supporting table
10. Display calculation trace

---

## Tech Stack

### Backend

- Python
- FastAPI
- pandas
- NumPy
- Uvicorn

### Frontend

- React
- Vite
- Axios
- CSS

---

## Current Features

- CSV upload API
- Local dataset storage
- Dataset profiling
- Missing value detection
- Duplicate row detection
- Identifier column detection
- Metric column detection
- Date-like column detection
- Dataset preview
- Rule-based analysis planner
- Pandas execution engine
- Natural-language question interface
- Suggested dataset questions
- Supporting result tables
- Calculation trace output

---

## Example Questions

The current MVP supports questions like:

- Which region has the highest revenue?
- Which product category has the highest revenue?
- Which customer segment has the highest revenue?
- What is the total revenue?
- What is the average revenue?
- Show missing values
- Give me a summary of this dataset

---

## Example Output

For the question:

```text
Which region has the highest revenue?
```

The system returns:

```text
North has the highest total revenue with 110.25.
```

With a calculation trace:

```json
{
  "operation": "groupby_sum",
  "group_by": "region",
  "metric": "revenue",
  "sort_direction": "desc",
  "rows_returned": 4
}
```

---

## Project Architecture

```text
Frontend React App
        |
        v
FastAPI Backend
        |
        v
File Upload Service
        |
        v
Dataset Profiling Service
        |
        v
Analysis Planner
        |
        v
Pandas Execution Engine
        |
        v
Computed Answer + Table + Trace
```

---

## Project Structure

```text
InsightOps-AI/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_analysis.py
│   │   │   └── routes_upload.py
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py
│   │   │
│   │   ├── services/
│   │   │   ├── analysis_service.py
│   │   │   ├── file_service.py
│   │   │   ├── planning_service.py
│   │   │   └── profiling_service.py
│   │   │
│   │   ├── storage/
│   │   │   └── uploads/
│   │   │
│   │   └── main.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js
│   │   │
│   │   ├── components/
│   │   │   ├── AnalysisResult.jsx
│   │   │   ├── DatasetPreview.jsx
│   │   │   ├── DatasetProfile.jsx
│   │   │   ├── DatasetUpload.jsx
│   │   │   ├── QuestionBox.jsx
│   │   │   └── SuggestedQuestions.jsx
│   │   │
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## Backend Setup

Go to the backend folder:

```powershell
cd backend
```

Create a virtual environment:

```powershell
python -m venv venv
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the backend server:

```powershell
python -m uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Swagger API docs:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

Go to the frontend folder:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Run the frontend server:

```powershell
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

## API Endpoints

### Health Check

```http
GET /health
```

### Upload CSV

```http
POST /api/upload/csv
```

Uploads a CSV file, stores it locally, and returns a dataset profile.

### Get Dataset Profile

```http
GET /api/datasets/{dataset_id}/profile
```

Returns profiling information for a previously uploaded dataset.

### Get Dataset Preview

```http
GET /api/datasets/{dataset_id}/preview
```

Returns the first rows of a previously uploaded dataset.

### Ask Dataset Question

```http
POST /api/analysis/question
```

Request body:

```json
{
  "dataset_id": "dataset-id-here",
  "question": "Which region has the highest revenue?"
}
```

Example response:

```json
{
  "dataset_id": "dataset-id-here",
  "question": "Which region has the highest revenue?",
  "analysis_plan": {
    "analysis_type": "groupby_aggregation_desc",
    "steps": [
      "Identify the metric column from the question",
      "Identify the grouping column from the question",
      "Group the dataset by the selected category",
      "Calculate the total value for the selected metric",
      "Sort the results from highest to lowest",
      "Return the top result and supporting table"
    ],
    "requires_grouping": true,
    "requires_metric": true
  },
  "answer": "North has the highest total revenue with 110.25.",
  "table": [
    {
      "region": "North",
      "revenue": 110.25
    },
    {
      "region": "West",
      "revenue": 68.99
    },
    {
      "region": "East",
      "revenue": 41.5
    },
    {
      "region": "South",
      "revenue": 23.96
    }
  ],
  "calculation_trace": {
    "operation": "groupby_sum",
    "group_by": "region",
    "metric": "revenue",
    "sort_direction": "desc",
    "rows_returned": 4
  }
}
```

---

## Phase 1 Sample Dataset

A simple sample CSV can be used for testing:

```csv
order_id,order_date,region,product_category,customer_segment,quantity,revenue,discount
1,2026-01-05,East,Burgers,Student,2,24.50,0
2,2026-01-06,West,Drinks,Worker,1,5.99,0
3,2026-01-07,East,Sides,Student,3,12.75,0.1
4,2026-02-01,North,Burgers,Family,4,49.00,0.05
5,2026-02-03,West,Burgers,Worker,2,25.50,0
6,2026-02-04,South,Drinks,Student,2,11.98,0
7,2026-03-01,East,Sides,Family,1,4.25,0
8,2026-03-04,North,Burgers,Worker,5,61.25,0.15
9,2026-03-07,South,Drinks,Student,2,11.98,0
10,2026-03-09,West,Burgers,Family,3,37.50,0.05
```

---

## Current MVP Limitations

The current version is intentionally simple and focused on Phase 1 functionality.

Current limitations:

- Only CSV files are supported.
- Analysis planning is rule-based.
- No LLM integration yet.
- No authentication yet.
- No database persistence yet.
- Uploaded files are stored locally.
- No chart generation yet.
- No report export yet.
- No evaluator/critic agent yet.
- No deployment yet.

These limitations are planned for later phases.

---

## Roadmap

### Phase 1: Core MVP

- CSV upload
- Dataset profiling
- Question interface
- Rule-based analysis planner
- Pandas execution
- Frontend display
- Suggested questions

### Phase 2: Visualization Layer

- Chart recommendations
- Bar charts
- Line charts
- Histograms
- Dashboard view
- Visual explanation of analysis results

### Phase 3: LLM Planning Layer

- Structured LLM-generated analysis plans
- Safer tool/function calling
- Plan validation
- Better natural-language question understanding
- Guardrails to prevent unsupported calculations

### Phase 4: Evaluator Layer

- Claim verification
- Unsupported claim detection
- Confidence scoring
- Result limitations
- Validation against computed pandas outputs

### Phase 5: Reports and History

- HTML report export
- PDF report export
- Analysis history
- Saved datasets
- Saved reports
- PostgreSQL integration

### Phase 6: Production Polish

- Authentication
- Docker
- Tests
- CI/CD
- Deployment
- Demo video
- Portfolio case study
- Resume and LinkedIn positioning

---

## Engineering Principle

InsightOps AI separates:

- natural-language question understanding
- analysis planning
- actual pandas computation
- result explanation
- calculation traceability

The core principle is:

```text
AI should help plan and explain.
Python/pandas should calculate.
```

This avoids hallucinated numeric answers and keeps insights grounded in real dataset calculations.

---

## Positioning

InsightOps AI is an independent AI software engineering project focused on building reliable AI-assisted business intelligence workflows.

The goal is to demonstrate practical full-stack AI software development skills, including backend API design, data processing, analysis execution, frontend integration, explainability, and future agentic workflow orchestration.

---

## Current Status

Phase 1 MVP is working locally.

Completed:

- Backend API skeleton
- CSV upload
- Dataset profiling
- Identifier, metric, categorical, and date-like column detection
- Dataset preview
- Question endpoint
- Rule-based analysis planning
- Pandas-backed analysis execution
- Frontend upload flow
- Frontend profile display
- Frontend preview table
- Suggested questions
- Analysis result display
- Supporting table
- Calculation trace

Next planned phase:

```text
Phase 2: Chart generation and visual analytics
```