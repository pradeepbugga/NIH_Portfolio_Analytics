# NIH Audit (NIH Portfolio Analysis App)

**NIH Audit is an interactive analytics platform for exploring the NIH research portfolio using semantic search, LLM-based grant classification, and funding visualization.**

### Table of Contents
- [Overview](#1-overview)
- [Demo](#2-demo)
- [Features](#3-features)
- [Tech Stack](#4-tech-stack)
- [Technical Highlights](#5-technical-highlights)
- [System Architecture](#6-system-architecture)
- [Search Pipeline](#7-search-pipeline)
- [Ontology Development](#8-ontology-development)
- [LLM Classification Pipeline](#9-llm-classification-pipeline)
- [Evaluation](#10-evaluation)
- [Engineering Decisions/Challenges](#11-engineering-decisions/challenges)
- [Performance & Cost Optimizations](#12-performance-&-cost-optimizations)
- [Repository Structure](#13-repository-structure)
- [Installation](#14-installation)
- [Running](#15-running)


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

### 4. Tech Stack

<div align="center">

<table>
  <tr>
    <th align="center">Layer</th>
    <th align="center">Technologies</th>
  </tr>
  <tr>
    <td align="center">
      Frontend<br>
      Backend<br>
      Database<br>
      AI/ML<br>
      Infrastructure<br>
      Tooling
    </td>
    <td align="center">
      HTML, CSS, JavaScript, Plotly<br>
      FastAPI, Python<br>
      PostgreSQL, pgvector<br>
      OpenAI GPT-5.4-mini, PubMedBERT, MS MARCO (cross-encoder)<br>
      Modal, Hetzner VM<br>
      Git, GitHub, pytest, logging
    </td>
  </tr>
</table>

</div>


### 5. Technical Highlights
- Incremental NIH data ingestion and normalization pipeline
- Hybrid semantic retrieval (PubMedBERT embeddings + PostgreSQL pgvector)
- Domain-aware keyword search with synonym expansion
- Cross-encoder reranking
- Cross-encoder fine-tuning on manually labeled biomedical search data
- Vector search evaluation against RCDC (current method used by NIH for classifying Research, Conditions, or Diseases)
- Ontology development through iterative ML-assisted error analysis
- LLM-based grant classification pipeline
- OpenAI Batch API processing for large-scale annotation
- PostgreSQL relational database design
- FastAPI REST API backend
- Modal GPU inference for distributed reranking
- Interactive frontend with Plotly visualizations
- Automated testing with pytest
- GitHub Actions CI/CD
- Structured logging and performance monitoring

### 6. System Architecture

<img width="2736" height="1517" alt="image" src="https://github.com/user-attachments/assets/b6acd3cf-a1ea-4cc8-935d-8e715de58038" />

### 7. Search Pipeline

<p align="center">
<img width="610" height="549" alt="image" src="https://github.com/user-attachments/assets/9a842964-6f77-4df2-ba58-1fb5704102e0" />
</p>

For our search pipeline, we use a vector similarity search (with a similarity threshold) to ensure high recall, then re-rank with a fine-tuned cross-encoder essential for achieving high precision.  Without the cross-encoder, a "multiple sclerosis" query would return confounding grants containing "systemic sclerosis", for example.      

### 8. Ontology Development
<p align="center">
<img width="514" height="636" alt="image" src="https://github.com/user-attachments/assets/5faed176-1140-409e-94ab-fe2919eebe59" />
</p>
It was not clear a priori how to categorize NIH research grants into meaningful translational research areas. We therefore developed an iterative pipeline (shown above) that proposed an initial ontology, refined it through repeated analysis of classification errors, and ultimately produced high-precision LLM prompts for large-scale annotation.

### 9. LLM Classification Pipeline
<br>
<img width="2752" height="257" alt="image" src="https://github.com/user-attachments/assets/95ebf790-a97b-4b3b-a2e6-b1bcc0dba22c" />

### 10. Evaluation

#### Semantic Search

The semantic search pipeline was benchmarked against 15 NIH Research, Condition, and Disease Categorization (RCDC) portfolios spanning both narrowly defined diseases (e.g., Multiple Sclerosis, Endometriosis) and broader clinical concepts (e.g., Breast Cancer, Heart Disease). The [RCDC categorization](https://report.nih.gov/funding/categorical-spending) is what is officially used by NIH for congressional reporting and therefore makes for 
the most suitable comparison.  Retrieval quality was measured using precision and recall before and after cross-encoder reranking.  

<p align="center">
<img width="600" height="600" alt="image" src="https://github.com/user-attachments/assets/cfa121f6-c924-4de8-b5b4-3ec73222f6c1" />
</p>

The evaluation above demonstrates the intended behavior of the hybrid retrieval architecture.

First, high-recall embedding retrieval generates a broad candidate set.  Then, cross-encoder reranking substantially improves precision while preserving most relevant grants.  Varying the score threshold of our reranker can toggle the precision/recall tradeoff, but we found that threshold = -2.0 provides the right balance.

The key findings from evaluation were that narrowly defined disease entities (e.g., multiple Sclerosis, endometriosis) showed strong agreement with RCDC, while broader umbrella categories (e.g., heart disease) were more challenging.  Broad RCDC categories encompass diverse disease subtypes and clinical concepts, suggesting that additional query expansion, ontology-aware retrieval, or task-specific training examples may further improve recall.


#### LLM Categorization

Because no public benchmark exists for categorizing NIH grants into the proposed translational research ontology, I used  expert-curated challenge sets rather than randomly sampled grants for evaluation.

I constructed challenge sets by collecting grants that were difficult to classify during ontology development, including:

- Grants with overlapping research objectives
- False positives and false negatives identified during classifier evaluation
- Semantically similar but conceptually distinct research projects
- Borderline cases requiring careful interpretation of category definitions

Below are examples of ambiguities in research categories represented in the challenge sets:

<div align="center">

<table>
  <tr>
    <th>Category</th>
    <th>Difficult Distinction</th>
  </tr>
  <tr>
    <td align="center">
      Diagnostic<br>
      Therapeutic<br>
      Research Tool
    </td>
    <td align="left">
      Diagnostic tool vs. biomarker discovery<br>
      Therapeutic development vs. mechanistic biology<br>
      Method development vs. use of an existing method
    </td>
  </tr>
</table>

</div>

Model performance was evaluated using precision, recall, and F1 score. Though these metrics are far less than what they would be with a randomly sampled grant dataset, they provide a useful benchmark for future models.  

Finally, our final production prompts achieved approximately 97% coverage across the NIH grant corpus for FY2025 (65K grants). The remaining ~3% of grants represented ambiguous or out-of-scope cases, requiring additional prompt optimization.

### 11. Engineering Decisions

### 12. Performance & Cost Optimizations

### 13. Repository Structure


### 7. Repository Structure

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


