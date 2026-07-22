# NIH Audit (NIH Portfolio Analysis App)

**NIH Audit is an interactive analytics platform for exploring the NIH research portfolio using semantic search, LLM-based grant classification, and funding visualization.**

### Table of Contents
- [Overview](#1-overview)
- [Demo](#2-demo)
- [Features](#3-features)
- [Technical Highlights](#4-technical-highlights)
- [System Architecture](#5-system-architecture)
- [Repository Structure](#6-repository-structure)
- [Search Pipeline](#7-search-pipeline)

### 1. Overview
The NIH funds over $50 billion in biomedical research annually across hundreds of disease areas and research programs. While NIH RePORTER provides access to individual grants, it offers limited insight into the type of research being funded (e.g., basic science versus therapeutic development) across agencies, disease areas, or funding mechanisms.

This project builds an end-to-end analytics pipeline that ingests NIH grant data, classifies grants into eight research categories using large language models, and provides interactive tools for exploring funding patterns across the NIH portfolio.

Users can analyze funding at multiple levels, including:

The entire NIH portfolio
Individual NIH institutes and centers (e.g., National Cancer Institute)
Activity codes (e.g., R01, R21, SBIR/STTR)
Disease or research topics using hybrid semantic search

Each portfolio includes interactive visualizations that allow users to drill down from aggregate funding statistics to the individual grants contributing to those results.


### 2. Demo
Visit https://nihaudit.com

The application allows users to:

- Search grants using hybrid semantic and keyword search
- Explore funding by NIH institute or center
- Compare funding across activity codes
- Analyze research portfolios by disease area
- View funding distributions across eight LLM-derived research categories
- Drill down from portfolio-level summaries to individual grant records

<p align="center">
  <img width="1365" height="803" alt="image" src="https://github.com/user-attachments/assets/beb393fa-5eb1-40f7-a9b7-45c74a6009fc" />
</p>
The above chart shows the categorical breakdown of NIH research grants in FY2025 for "multiple sclerosis."  One can easily observe that the majority of grants for this disease are in mechanistic / basic science, therapeutic, or research infrastructure (i.e. research centers).

### 3. Features

#### 📊 Interactive Portfolio Analytics
- Explore NIH funding across the entire research portfolio or within individual NIH institutes and centers.
- Visualize funding distributions across eight research categories with interactive charts.

#### 🔍 Semantic Grant Search
- Search NIH grants using a hybrid semantic and keyword search engine.
- Supports natural-language queries (e.g., *multiple sclerosis*, *CRISPR gene editing*, and *spatial transcriptomics*).

#### 🧬 Data-Driven Ontology Development
- Developed an eight-category research ontology through an iterative machine learning workflow rather than defining categories *a priori*.
- Proposed candidate research categories, trained embedding-based classifiers to identify systematic errors, and performed false positive/false negative analysis to refine category definitions.
- Merged overlapping concepts, introduced new categories where necessary, and used the resulting ontology as the foundation for large-scale LLM classification of NIH grants.
- 
#### 🧠 LLM-Based Research Classification
Automatically categorizes grants into eight research stages:

- Mechanistic / Basic Science
- Therapeutic
- Diagnostic
- Research Tool
- Clinical / Health Systems
- Observational Epidemiology
- Research Infrastructure
- Education / Training

#### 📂 Portfolio Drill-Down
- Navigate from portfolio-level funding summaries to individual grant records.
- Filter portfolios by agency, activity code, research category, and search query.

#### 📝 Grant Summaries
- Generate concise AI-written summaries of complex NIH abstracts.

#### 💰 Funding Analytics
- Compare funding across institutes, activity codes, disease areas, and research categories.
- Aggregate award amounts and visualize portfolio composition.

### 4. Technical Highlights
- Incremental NIH data ingestion and normalization pipeline
- Hybrid semantic retrieval (PubMedBERT embeddings + PostgreSQL pgvector)
- Domain-aware keyword search with synonym expansion
- Cross-encoder reranking
- Cross-encoder fine-tuning on manually labeled biomedical search data
- Vector search evaluation against RCDC (current method used by NIH for classifying Research, Conditions, or Diseases)
- Ontology development through iterative ML-assisted error analysis
- LLM-based grant classification pipeline
- OpenAI Batch API processing for large-scale annotation
- Incremental NIH data ingestion and normalization pipeline
- PostgreSQL relational database design
- FastAPI REST API backend
- Modal GPU inference for distributed reranking
- Interactive frontend with Plotly visualizations
- Automated testing with pytest
- GitHub Actions CI/CD
- Structured logging and performance monitoring

### 5. System Architecture

<img width="2736" height="1517" alt="image" src="https://github.com/user-attachments/assets/b6acd3cf-a1ea-4cc8-935d-8e715de58038" />

### 6. Repository Structure

```
├── .github/
│   └── workflows/
│       └── tests.yaml
├── .gitignore
├── LICENSE
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── startup.py
│   ├── static/
│   │   ├── css/
│   │   │   ├── styles.css
│   │   │   └── styles_v12.css
│   │   ├── fonts/
│   │   │   └── primer.ttf
│   │   ├── images/
│   │   │   └── curved-thin-arrow-icon.svg
│   │   └── js/
│   │       └── script.js
│   └── templates/
│       ├── categories.html
│       ├── contact_us.html
│       ├── index.html
│       ├── partials/
│       │   └── search_bar.html
│       ├── portfolio.html
│       └── results.html
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── constants.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── embedding/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── embedding_job.py
│   │   ├── model.py
│   │   ├── persistence.py
│   │   └── selection.py
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── hashing.py
│   │   ├── ingest.py
│   │   ├── normalize.py
│   │   ├── org_resolution.py
│   │   ├── persistence.py
│   │   ├── process.py
│   │   └── reporter_client.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── batch.py
│   │   ├── constants.py
│   │   ├── parser.py
│   │   ├── prompt_loader.py
│   │   └── prompts/
│   │       └── README.md
│   ├── logging_config.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── cache.py
│   │   ├── candidate_retrieval.py
│   │   ├── combine.py
│   │   ├── constants.py
│   │   ├── fill_abstract.py
│   │   ├── hybrid.py
│   │   ├── load_docs.py
│   │   ├── modal_reranker.py
│   │   ├── postprocess.py
│   │   ├── query_embedding.py
│   │   └── reranker.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── activity_service.py
│   │   ├── agency_service.py
│   │   ├── formatting.py
│   │   ├── grant_service.py
│   │   ├── portfolio_service.py
│   │   └── search_service.py
│   └── utils/
│       ├── __init__.py
│       ├── abstract_tokens.py
│       ├── compile_parquet.py
│       └── query_expansion.py
├── data/
│   ├── activity_code_list.csv
│   ├── agencies_list.csv
│   └── rcdc_synonyms.json
├── evaluation/
│   ├── __init__.py
│   ├── categorization/
│   │   ├── __init__.py
│   │   ├── challenge_sets/
│   │   │   └── research_tool.csv
│   │   ├── classify.py
│   │   ├── grant_loader.py
│   │   ├── metrics.py
│   │   └── run_eval.py
│   └── search/
│       ├── __init__.py
│       ├── benchmark.csv
│       ├── ground_truth/
│       │   ├── Alzheimer's_Disease.csv
│       │   ├── Amyotrophic_Lateral_Sclerosis_(ALS).csv
│       │   ├── Asthma.csv
│       │   ├── Autism.csv
│       │   ├── Breast_Cancer.csv
│       │   ├── Crohn's_Disease.csv
│       │   ├── Cystic_Fibrosis.csv
│       │   ├── Depression.csv
│       │   ├── Diabetes.csv
│       │   ├── Endometriosis.csv
│       │   ├── HIV_AIDS.csv
│       │   ├── Heart_Disease.csv
│       │   ├── Lupus.csv
│       │   ├── Multiple_Sclerosis.csv
│       │   └── Parkinson's_Disease.csv
│       ├── metrics.py
│       ├── rcdc.py
│       └── run_eval.py
├── modal/
│   ├── __init__.py
│   └── reranker_app.py
├── pipelines/
│   ├── __init__.py
│   ├── ingest_nih.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── combine_results.py
│   │   ├── generate_classification_batch.py
│   │   ├── generate_summary_batch.py
│   │   ├── import_classification_results.py
│   │   ├── import_summary_results.py
│   │   ├── retrieve_batch.py
│   │   └── submit_batch.py
│   ├── migration/
│   │   ├── __init__.py
│   │   └── hash_historical.py
│   ├── run_embedding.py
│   └── train_reranker.py
├── requirements.txt
├── scripts/
│   ├── compare_pairs_reranker.py
│   └── update_agency_code.py
└── tests/
    ├── embedding/
    │   ├── test_embedding_job.py
    │   ├── test_model.py
    │   ├── test_persistence.py
    │   └── test_selection.py
    ├── ingest/
    │   ├── test_config.py
    │   ├── test_hashing.py
    │   ├── test_ingest.py
    │   ├── test_normalize.py
    │   ├── test_org_resolution.py
    │   ├── test_persistence.py
    │   ├── test_process.py
    │   └── test_reporter_client.py
    ├── llm/
    │   ├── test_batch.py
    │   ├── test_parser.py
    │   └── test_prompt_loader.py
    ├── search/
    │   ├── test_cache.py
    │   ├── test_candidate_retrieval.py
    │   ├── test_combine.py
    │   ├── test_fill_abstracts.py
    │   ├── test_hybrid.py
    │   ├── test_load_docs.py
    │   ├── test_postprocess.py
    │   ├── test_query_embedding.py
    │   └── test_reranker.py
    ├── services/
    │   ├── test_formatting.py
    │   ├── test_grant_service.py
    │   ├── test_portfolio_service.py
    │   └── test_search_service.py
    ├── test_main.py
    └── utils/
        └── test_query_expansion.py
```
### 7. Search Pipeline

<p align="center">
<img width="610" height="549" alt="image" src="https://github.com/user-attachments/assets/9a842964-6f77-4df2-ba58-1fb5704102e0" />
</p>



### 8. Ontology Development

### 9. LLM Classification Pipeline

### 10. Evaluation

### 11. 


