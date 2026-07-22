# NIH Audit (NIH Portfolio Analysis App)

**NIH Audit is an interactive analytics platform for exploring the NIH research portfolio using semantic search, LLM-based grant classification, and funding visualization.**

### Table of Contents
- [Overview](#overview)
- [Demo](#demo)
- [Features](#features)
- [Technical Highlights](#technical_highlights)
- [System Architecture](#system_architecture)
- [Repository Structure](#repository_structure)

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
