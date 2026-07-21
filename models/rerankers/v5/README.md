---
tags:
- sentence-transformers
- cross-encoder
- reranker
- generated_from_trainer
- dataset_size:438
- loss:BinaryCrossEntropyLoss
base_model: cross-encoder/ms-marco-MiniLM-L6-v2
pipeline_tag: text-ranking
library_name: sentence-transformers
metrics:
- pearson
- spearman
model-index:
- name: CrossEncoder based on cross-encoder/ms-marco-MiniLM-L6-v2
  results:
  - task:
      type: cross-encoder-correlation
      name: Cross Encoder Correlation
    dataset:
      name: disease relevance
      type: disease-relevance
    metrics:
    - type: pearson
      value: 0.7350289284199164
      name: Pearson
    - type: spearman
      value: 0.7172285226194447
      name: Spearman
---

# CrossEncoder based on cross-encoder/ms-marco-MiniLM-L6-v2

This is a [Cross Encoder](https://www.sbert.net/docs/cross_encoder/usage/usage.html) model finetuned from [cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) using the [sentence-transformers](https://www.SBERT.net) library. It computes scores for pairs of texts, which can be used for text reranking and semantic search.

## Model Details

### Model Description
- **Model Type:** Cross Encoder
- **Base model:** [cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) <!-- at revision c5ee24cb16019beea0893ab7796b1df96625c6b8 -->
- **Maximum Sequence Length:** 512 tokens
- **Number of Output Labels:** 1 label
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Documentation:** [Cross Encoder Documentation](https://www.sbert.net/docs/cross_encoder/usage/usage.html)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/UKPLab/sentence-transformers)
- **Hugging Face:** [Cross Encoders on Hugging Face](https://huggingface.co/models?library=sentence-transformers&other=cross-encoder)

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import CrossEncoder

# Download from the 🤗 Hub
model = CrossEncoder("cross_encoder_model_id")
# Get scores for pairs of texts
pairs = [
    ['Breast Cancer', "Cholesterol promotes breast cancer progression: establishing the mechanisms \ufeff   \nDESCRIPTION (provided by applicant): The purpose of this K08 Mentored Clinical Scientist Development Award proposal is to describe the five year training, development and mentorship plan for Dr. Emily Gallagher, in addition to her research plans to understand the link between obesity, Type 2 diabetes and breast cancer, specifically by examining the effect of high circulating cholesterol on breast cancer progression. Dr. Gallagher received her MD with honors from the University College Dublin, Ireland. She trained clinically in Ireland before moving to New York and is Board Certified in Internal Medicine and Endocrinology. As a clinician, Dr. Gallagher recognized the importance of basic science research in advancing clinical medicine. She moved to the United States to develop her career as a clinician-scientist and began her research studying the mechanisms linking obesity and Type 2 diabetes with breast cancer as a fellow in 2010. She graduated from fellowship in 2012 and was promoted to Assistant Professor in the Department of Medicine at Mount Sinai School of Medicine and given her own lab space to develop her research into cholesterol and breast cancer. She spends 80% of her time conducting research and the remaining 20% of her time treating endocrinology patients, many of who are also oncology patients, giving her first hand experience of the growing number of patients with obesity and Type 2 diabetes with cancer and the need to understand the links between metabolic conditions and cancer to appropriately treat these patients. Dr. Gallagher's goals during the K08 Award period are to develop her skills in a core set of molecular biology techniques; broaden her knowledge of cancer biology and lipidology; form collaborations for future research projects and advance our understanding of the mechanisms linking elevated cholesterol and breast cancer. Dr. Gallagher's mentors, Drs. LeRoith, Parsons, and Ginsberg, individually have many years of successful mentoring experience and are all experts in their own areas of research. In addition to her mentors, Dr. Gallagher has succeeded in putting together a team of advisors in the fields of oncology and metabolism from Mount Sinai and Columbia University who will provide their support in specific aspects of the current project, her career progression and the development of future basic science and clinical research projects based on the results of the experiments described in this proposal. Furthermore, Mount Sinai School of Medicine offers all of the environmental support Dr. Gallagher needs to succeed in her research and overall career objectives. The proposed research project aims to examine the mechanisms linking obesity, Type 2 diabetes and increased breast cancer risk, in order to identify targets for therapies that will improve survival in these women. Elevated serum cholesterol is frequently seen in people with obesity and Type 2 diabetes. These patients may have elevated low density lipoprotein (LDL) or very low density lipoprotein (VLDL). These abnormal elevations in serum cholesterol have been associated with an increased risk of hormone receptor negative and Her2 overexpressing breast cancers and a poor prognosis in breast cancer patients. It is hypothesized that increased cholesterol delivery to breast cancers by VLDL and/or LDL is driving breast cancer growth and spread, particularly in breast cancers with high levels of the low-density lipoprotein receptor (LDLR) that mediates cholesterol uptake from VLDL and LDL. This cholesterol uptake may promote tumor growth by activating signaling pathways that promote survival and proliferation. In addition, cholesterol may be metabolized into biologically active metabolites (one of which is 25-hydroxycholesterol) that may promote tumor metastasis. Therefore, the research hypothesis for this proposal is that elevated circulating cholesterol in the form of VLDL or LDL cholesterol promotes breast cancer growth and metastasis by delivery of cholesterol to cancer cells via the LDLR. The main aims of Dr. Gallagher's proposed research are: (1) To determine if high circulating cholesterol promotes breast cancer growth directly by increased cholesterol uptake through the LDLR in estrogen receptor positive, hormone receptor negative and Her2 overexpressing breast cancers; (2) To examine if cholesterol uptake through the LDLR leads to activation of a particular signaling pathway in all breast cancer subtypes and if lowering serum lipid levels and silencing the LDLR on tumor cells prevents activation of this pathway; (3) To determine the role of the cholesterol metabolite 25-hydroxycholesterol on tumor growth and metastasis by targeting the enzymes involved in its formation and studying the effects of 25- hydroxycholesterol on intracellular signaling, cytokine expression and epithelial-to-mesenchymal transition. Through these studies Dr. Gallagher aims to advance the field of metabolism and cancer by understanding the role of cholesterol in different breast cancer subtypes. With the results of these studies and through her collaborators and advisors, she plans to develop translational projects to change clinical practice and appropriately treat patients with obesity, Type 2 diabetes and breast cancer. Her abilities, dedication and determination to succeed in her goals are recognized by the Dean and Chair of Medicine at Mount Sinai School of Medicine, as well as her mentors and advisors, who are all offering their support to help her successfully complete her project and become an independent investigator and expert in the field of metabolism and cancer."],
    ['Progressive supranuclear palsy', 'Multi-modal magnetic resonance imaging in progressive supranuclear palsy (PSP) PROJECT SUMMARY/ABSTRACT\nThis is an application for a Mentored Patient-Oriented Research Career Development Award (K23). The goal\nof the proposed project is to provide the candidate with skills necessary to develop an independent research\nprogram dedicated to the development of neuroimaging biomarkers in Progressive Supranuclear Palsy (PSP)\nand other Alzheimer disease-related dementias. To facilitate this long-term career goal the candidate will: 1)\nidentify multimodal (volumetric, structural and functional connectivity) magnetic resonance imaging (MRI)\ndifferences among 3 PSP subtypes (PSP-Richardson syndrome (PSP-RS), PSP-Speech/Language Disorder\n(PSP-SL), and PSP-Corticobasal syndrome (PSP-CBS)) as delineated in the recently revised PSP diagnostic\ncriteria, and 2) examine the associations between these imaging features with cross-sectional characteristics\nand 1-year clinical change. The candidate proposes a comprehensive training plan, combining formal\ncoursework, meetings and tutorials overseen by his mentors, participation in applied training experiences, and\ninvolvement in seminars and workshops. Specific training goals include: 1) training in neuroimaging methods\nand image analysis; 2) advanced training in experimental study design and statistical analysis; 3) advanced\ntraining in clinical trials methodology; 4) training in manuscript preparation, grant writing and leadership\ncapability; and 5) continued training in the responsible conduct of research. The training plan will be\nimplemented in coordination with a research project based on preliminary data collected by the applicant. The\nprimary hypotheses to be examined are: 1) In PSP-RS, there will be greater structural and functional\nconnectivity disruptions in bilateral dorsal midbrain and frontostriatal gray matter compared with other PSP\nsubtypes, and significant associations between baseline bilateral diffusion tensor imaging (DTI) dorsal\nmidbrain/resting state-fMRI (rs-fMRI) frontostriatal connectivity and executive function; 2) In PSP-SL, there will\nbe greater structural and functional connectivity disruptions in the dominant inferior frontal cortex and its\nsubcortical speech network connections, and significant associations between baseline DTI and rs-fMRI\nmeasures in the dominant inferior frontal lobe and language function; and 3) In PSP-CBS, there will be greater\nstructural and functional connectivity disruptions in the parietal lobe-dorsolateral striatum network contralateral\nto the most affected side, and significant associations between baseline DTI and rs-fMRI measures in the\nparietal lobe-dorsolateral striatum and praxis. Results from this research will be used to develop a R01\nresearch proposal that will facilitate the candidate’s transition to an independent researcher.'],
    ['multiple sclerosis ', 'A novel monobody-drug conjugate to treat mutant Ras multiple myeloma Project Summary: Multiple myeloma is an incurable hematologic malignancy with an expected\nmedian survival of 7-8 years. The proteasome inhibitors, bortezomib, carfilzomib and the recently\napproved ixazomib, are a mainstay of current myeloma treatment. Despite an initial response rate\napproaching 90% to proteasome inhibitor-containing combinations, all patients relapse and\neventually become resistant to any treatments. Approximately 50% of these patients harbor\nmutant NRas or KRas. We have observed that mutant Ras multiple myeloma cells display high\nlevels of macropinocytosis, a nutrient scavenging process that facilitates the bulk engulfment of\nextracellular fluid and its solutes. Harnessing this metabolic adaptation, we have created\nmacropinocytosis-targeting monobodies that carry an FDA-approved cytotoxic payload (vc-\nMMAE). In vitro proliferation assays demonstrate that the monobody-drug conjugates show\nselectivity for macropinocytosis-positive cancer cells, and maintain potency in the low nanomolar\nrange. Monobody-based technologies display fast clearance rates in humans (1-2hr), but maintain\nbeneficial characteristics of biologics such as tumor accumulation through enhanced permeability\nand retention (EPR) effect. Thus, we hypothesize that our novel macropinocytosis-targeting\nmonobody-drug conjugates will reduce on-target and off-target effects often seen with traditional\nantibody-drug conjugates, and fill a void of therapeutic options for patients with mutant Ras\nmultiple myeloma. We propose a Phase I STTR program for investigators at TEZCAT\nLaboratories and New York University Langone Health to advance this lead through Specific Aims\nthat evaluate the lead drug candidate in controlling human cancer cell growth in vitro (Aim 1) and\nin a clinically-relevant mouse model of multiple myeloma (Aim 2 & 3). TEZCAT Laboratories has\nentered into an Option Agreement with NYU for exclusive rights to the technology being\ndeveloped. The commercialization strategy will be based on establishing initial efficacy and\nnontoxicity of the lead compound in relation to cellular macropinocytosis levels in Phase I STTR\nstudies, further development towards IND status in Phase II SBIR studies, and then first-in-human\nclinical trials. Thus, we expect Phase I STTR to provide the basis for pursuit of additional data in\nPhase II aimed at GMP protocols and further non-GLP and GLP safety and toxicity studies.'],
    ['Spatial transcriptomics', 'Microfluidic, molecular, and optical tools for multimodal measurement of single cells and tissues The development of single-cell genomics technologies has been a driving force in biomedical research over the\npast decade because of the throughput, sensitivity, and precision with which such techniques can dissect\ncomplex biological systems. A primary example of the impact of these tools is the rapid translation of single-cell\nRNA sequencing (scRNAseq) for comprehensively cataloging cellular states for the Human Cell Atlas project.\nTechnology that combine microfluidic platforms with DNA barcoding strategies have drastically increased the\nthroughput and accessibility of scRNAseq so that to-date, the Human Cell Atlas consortium has logged over 67\nmillion cells, enabling unprecedented insight into the cellular diversity in healthy and diseased organs and\ntissues. However, while the transcriptome provides a comprehensive and quantitative proxy for cellular state,\nproteomic measurements provide a more direct understanding of cellular function, and epigenetic measurements\nthat profile methylation, histone modifications, and protein-DNA interactions, provide a more complete picture of\nthe regulatory mechanisms that maintain cell state or drive cellular transitions. Furthermore, cell morphology and\nthe spatial distribution of proteins and chemicals within the cell can reveal important cellular phenotypes that can\nonly be characterized by microscopy. Finally, the relative positions of cells within tissues and organs are\nnecessary for a more complete understanding of the cellular interactions that lead to functional tissues and\norgans. This research program focuses on the development of technology to facilitate multimodal precision\nmeasurements in single cells and tissues. We use molecular biology tools and DNA sequencing platforms to\nmeasure the proteome, transcriptome, and epigenome of single cells and nonlinear optical imaging to\ncharacterize chemical composition and morphology of cells. We leverage microfluidic technology to integrate\nmolecular and optical measurements to enable multimodal single-cell measurement. Additionally, this research\nprogram aims to develop novel computational approaches for integrated analysis of multimodal single-cell\nmeasurements. Our ultimate goal is to develop a tool to make all of these measurements in situ, in order to retain\nsingle-cell spatial information and cellular context in a developing tissue or whole organism.'],
    ['Spatial biology', 'Spatial and temporal mapping of cell fate within lymphoid tissue Summary: Spectacular recent advances in single cell genomics have provided high-resolution information\nabout cell identity, however relating molecular information to the spatial and temporal context remains a\nmajor challenge. This is particularly relevant for the immune system, since immune responses occur in\nhighly organized tissue environments, and involve tightly-controlled changes in cell state over time. Here\nwe propose to develop new approaches to increase the spatial and temporal resolution of single cell\nanalyses, and to use these methods to generate and then disseminate a 4-dimensional (time and 3D\nspatial coordinates) map of T cell development and the associated microenvironment in the thymus. In\nAim 1, we will use simultaneous measurement of mRNA and surface proteins on single cells, together with\ncomputation and experimental approaches to develop a temporal map of cell state transitions during T cell\ndevelopment in the thymus. In Aim 2, we will use coherent Raman and multiphoton microscopy of living\nthymic tissue slices, together with laser microdissection, to isolate functionally relevant regions of tissues.\nWe will then perform single cell analyses of individual cells within these defined regions and use\ncomputational analyses to define cell types and resolve cellular cross-talk. In Aim 3, we will increase the\nvalue of this resource to the scientific community, we will make the data readily accessible to researchers\nvia a user-friendly interface.\n!'],
]
scores = model.predict(pairs)
print(scores.shape)
# (5,)

# Or rank different texts based on similarity to a single text
ranks = model.rank(
    'Breast Cancer',
    [
        "Cholesterol promotes breast cancer progression: establishing the mechanisms \ufeff   \nDESCRIPTION (provided by applicant): The purpose of this K08 Mentored Clinical Scientist Development Award proposal is to describe the five year training, development and mentorship plan for Dr. Emily Gallagher, in addition to her research plans to understand the link between obesity, Type 2 diabetes and breast cancer, specifically by examining the effect of high circulating cholesterol on breast cancer progression. Dr. Gallagher received her MD with honors from the University College Dublin, Ireland. She trained clinically in Ireland before moving to New York and is Board Certified in Internal Medicine and Endocrinology. As a clinician, Dr. Gallagher recognized the importance of basic science research in advancing clinical medicine. She moved to the United States to develop her career as a clinician-scientist and began her research studying the mechanisms linking obesity and Type 2 diabetes with breast cancer as a fellow in 2010. She graduated from fellowship in 2012 and was promoted to Assistant Professor in the Department of Medicine at Mount Sinai School of Medicine and given her own lab space to develop her research into cholesterol and breast cancer. She spends 80% of her time conducting research and the remaining 20% of her time treating endocrinology patients, many of who are also oncology patients, giving her first hand experience of the growing number of patients with obesity and Type 2 diabetes with cancer and the need to understand the links between metabolic conditions and cancer to appropriately treat these patients. Dr. Gallagher's goals during the K08 Award period are to develop her skills in a core set of molecular biology techniques; broaden her knowledge of cancer biology and lipidology; form collaborations for future research projects and advance our understanding of the mechanisms linking elevated cholesterol and breast cancer. Dr. Gallagher's mentors, Drs. LeRoith, Parsons, and Ginsberg, individually have many years of successful mentoring experience and are all experts in their own areas of research. In addition to her mentors, Dr. Gallagher has succeeded in putting together a team of advisors in the fields of oncology and metabolism from Mount Sinai and Columbia University who will provide their support in specific aspects of the current project, her career progression and the development of future basic science and clinical research projects based on the results of the experiments described in this proposal. Furthermore, Mount Sinai School of Medicine offers all of the environmental support Dr. Gallagher needs to succeed in her research and overall career objectives. The proposed research project aims to examine the mechanisms linking obesity, Type 2 diabetes and increased breast cancer risk, in order to identify targets for therapies that will improve survival in these women. Elevated serum cholesterol is frequently seen in people with obesity and Type 2 diabetes. These patients may have elevated low density lipoprotein (LDL) or very low density lipoprotein (VLDL). These abnormal elevations in serum cholesterol have been associated with an increased risk of hormone receptor negative and Her2 overexpressing breast cancers and a poor prognosis in breast cancer patients. It is hypothesized that increased cholesterol delivery to breast cancers by VLDL and/or LDL is driving breast cancer growth and spread, particularly in breast cancers with high levels of the low-density lipoprotein receptor (LDLR) that mediates cholesterol uptake from VLDL and LDL. This cholesterol uptake may promote tumor growth by activating signaling pathways that promote survival and proliferation. In addition, cholesterol may be metabolized into biologically active metabolites (one of which is 25-hydroxycholesterol) that may promote tumor metastasis. Therefore, the research hypothesis for this proposal is that elevated circulating cholesterol in the form of VLDL or LDL cholesterol promotes breast cancer growth and metastasis by delivery of cholesterol to cancer cells via the LDLR. The main aims of Dr. Gallagher's proposed research are: (1) To determine if high circulating cholesterol promotes breast cancer growth directly by increased cholesterol uptake through the LDLR in estrogen receptor positive, hormone receptor negative and Her2 overexpressing breast cancers; (2) To examine if cholesterol uptake through the LDLR leads to activation of a particular signaling pathway in all breast cancer subtypes and if lowering serum lipid levels and silencing the LDLR on tumor cells prevents activation of this pathway; (3) To determine the role of the cholesterol metabolite 25-hydroxycholesterol on tumor growth and metastasis by targeting the enzymes involved in its formation and studying the effects of 25- hydroxycholesterol on intracellular signaling, cytokine expression and epithelial-to-mesenchymal transition. Through these studies Dr. Gallagher aims to advance the field of metabolism and cancer by understanding the role of cholesterol in different breast cancer subtypes. With the results of these studies and through her collaborators and advisors, she plans to develop translational projects to change clinical practice and appropriately treat patients with obesity, Type 2 diabetes and breast cancer. Her abilities, dedication and determination to succeed in her goals are recognized by the Dean and Chair of Medicine at Mount Sinai School of Medicine, as well as her mentors and advisors, who are all offering their support to help her successfully complete her project and become an independent investigator and expert in the field of metabolism and cancer.",
        'Multi-modal magnetic resonance imaging in progressive supranuclear palsy (PSP) PROJECT SUMMARY/ABSTRACT\nThis is an application for a Mentored Patient-Oriented Research Career Development Award (K23). The goal\nof the proposed project is to provide the candidate with skills necessary to develop an independent research\nprogram dedicated to the development of neuroimaging biomarkers in Progressive Supranuclear Palsy (PSP)\nand other Alzheimer disease-related dementias. To facilitate this long-term career goal the candidate will: 1)\nidentify multimodal (volumetric, structural and functional connectivity) magnetic resonance imaging (MRI)\ndifferences among 3 PSP subtypes (PSP-Richardson syndrome (PSP-RS), PSP-Speech/Language Disorder\n(PSP-SL), and PSP-Corticobasal syndrome (PSP-CBS)) as delineated in the recently revised PSP diagnostic\ncriteria, and 2) examine the associations between these imaging features with cross-sectional characteristics\nand 1-year clinical change. The candidate proposes a comprehensive training plan, combining formal\ncoursework, meetings and tutorials overseen by his mentors, participation in applied training experiences, and\ninvolvement in seminars and workshops. Specific training goals include: 1) training in neuroimaging methods\nand image analysis; 2) advanced training in experimental study design and statistical analysis; 3) advanced\ntraining in clinical trials methodology; 4) training in manuscript preparation, grant writing and leadership\ncapability; and 5) continued training in the responsible conduct of research. The training plan will be\nimplemented in coordination with a research project based on preliminary data collected by the applicant. The\nprimary hypotheses to be examined are: 1) In PSP-RS, there will be greater structural and functional\nconnectivity disruptions in bilateral dorsal midbrain and frontostriatal gray matter compared with other PSP\nsubtypes, and significant associations between baseline bilateral diffusion tensor imaging (DTI) dorsal\nmidbrain/resting state-fMRI (rs-fMRI) frontostriatal connectivity and executive function; 2) In PSP-SL, there will\nbe greater structural and functional connectivity disruptions in the dominant inferior frontal cortex and its\nsubcortical speech network connections, and significant associations between baseline DTI and rs-fMRI\nmeasures in the dominant inferior frontal lobe and language function; and 3) In PSP-CBS, there will be greater\nstructural and functional connectivity disruptions in the parietal lobe-dorsolateral striatum network contralateral\nto the most affected side, and significant associations between baseline DTI and rs-fMRI measures in the\nparietal lobe-dorsolateral striatum and praxis. Results from this research will be used to develop a R01\nresearch proposal that will facilitate the candidate’s transition to an independent researcher.',
        'A novel monobody-drug conjugate to treat mutant Ras multiple myeloma Project Summary: Multiple myeloma is an incurable hematologic malignancy with an expected\nmedian survival of 7-8 years. The proteasome inhibitors, bortezomib, carfilzomib and the recently\napproved ixazomib, are a mainstay of current myeloma treatment. Despite an initial response rate\napproaching 90% to proteasome inhibitor-containing combinations, all patients relapse and\neventually become resistant to any treatments. Approximately 50% of these patients harbor\nmutant NRas or KRas. We have observed that mutant Ras multiple myeloma cells display high\nlevels of macropinocytosis, a nutrient scavenging process that facilitates the bulk engulfment of\nextracellular fluid and its solutes. Harnessing this metabolic adaptation, we have created\nmacropinocytosis-targeting monobodies that carry an FDA-approved cytotoxic payload (vc-\nMMAE). In vitro proliferation assays demonstrate that the monobody-drug conjugates show\nselectivity for macropinocytosis-positive cancer cells, and maintain potency in the low nanomolar\nrange. Monobody-based technologies display fast clearance rates in humans (1-2hr), but maintain\nbeneficial characteristics of biologics such as tumor accumulation through enhanced permeability\nand retention (EPR) effect. Thus, we hypothesize that our novel macropinocytosis-targeting\nmonobody-drug conjugates will reduce on-target and off-target effects often seen with traditional\nantibody-drug conjugates, and fill a void of therapeutic options for patients with mutant Ras\nmultiple myeloma. We propose a Phase I STTR program for investigators at TEZCAT\nLaboratories and New York University Langone Health to advance this lead through Specific Aims\nthat evaluate the lead drug candidate in controlling human cancer cell growth in vitro (Aim 1) and\nin a clinically-relevant mouse model of multiple myeloma (Aim 2 & 3). TEZCAT Laboratories has\nentered into an Option Agreement with NYU for exclusive rights to the technology being\ndeveloped. The commercialization strategy will be based on establishing initial efficacy and\nnontoxicity of the lead compound in relation to cellular macropinocytosis levels in Phase I STTR\nstudies, further development towards IND status in Phase II SBIR studies, and then first-in-human\nclinical trials. Thus, we expect Phase I STTR to provide the basis for pursuit of additional data in\nPhase II aimed at GMP protocols and further non-GLP and GLP safety and toxicity studies.',
        'Microfluidic, molecular, and optical tools for multimodal measurement of single cells and tissues The development of single-cell genomics technologies has been a driving force in biomedical research over the\npast decade because of the throughput, sensitivity, and precision with which such techniques can dissect\ncomplex biological systems. A primary example of the impact of these tools is the rapid translation of single-cell\nRNA sequencing (scRNAseq) for comprehensively cataloging cellular states for the Human Cell Atlas project.\nTechnology that combine microfluidic platforms with DNA barcoding strategies have drastically increased the\nthroughput and accessibility of scRNAseq so that to-date, the Human Cell Atlas consortium has logged over 67\nmillion cells, enabling unprecedented insight into the cellular diversity in healthy and diseased organs and\ntissues. However, while the transcriptome provides a comprehensive and quantitative proxy for cellular state,\nproteomic measurements provide a more direct understanding of cellular function, and epigenetic measurements\nthat profile methylation, histone modifications, and protein-DNA interactions, provide a more complete picture of\nthe regulatory mechanisms that maintain cell state or drive cellular transitions. Furthermore, cell morphology and\nthe spatial distribution of proteins and chemicals within the cell can reveal important cellular phenotypes that can\nonly be characterized by microscopy. Finally, the relative positions of cells within tissues and organs are\nnecessary for a more complete understanding of the cellular interactions that lead to functional tissues and\norgans. This research program focuses on the development of technology to facilitate multimodal precision\nmeasurements in single cells and tissues. We use molecular biology tools and DNA sequencing platforms to\nmeasure the proteome, transcriptome, and epigenome of single cells and nonlinear optical imaging to\ncharacterize chemical composition and morphology of cells. We leverage microfluidic technology to integrate\nmolecular and optical measurements to enable multimodal single-cell measurement. Additionally, this research\nprogram aims to develop novel computational approaches for integrated analysis of multimodal single-cell\nmeasurements. Our ultimate goal is to develop a tool to make all of these measurements in situ, in order to retain\nsingle-cell spatial information and cellular context in a developing tissue or whole organism.',
        'Spatial and temporal mapping of cell fate within lymphoid tissue Summary: Spectacular recent advances in single cell genomics have provided high-resolution information\nabout cell identity, however relating molecular information to the spatial and temporal context remains a\nmajor challenge. This is particularly relevant for the immune system, since immune responses occur in\nhighly organized tissue environments, and involve tightly-controlled changes in cell state over time. Here\nwe propose to develop new approaches to increase the spatial and temporal resolution of single cell\nanalyses, and to use these methods to generate and then disseminate a 4-dimensional (time and 3D\nspatial coordinates) map of T cell development and the associated microenvironment in the thymus. In\nAim 1, we will use simultaneous measurement of mRNA and surface proteins on single cells, together with\ncomputation and experimental approaches to develop a temporal map of cell state transitions during T cell\ndevelopment in the thymus. In Aim 2, we will use coherent Raman and multiphoton microscopy of living\nthymic tissue slices, together with laser microdissection, to isolate functionally relevant regions of tissues.\nWe will then perform single cell analyses of individual cells within these defined regions and use\ncomputational analyses to define cell types and resolve cellular cross-talk. In Aim 3, we will increase the\nvalue of this resource to the scientific community, we will make the data readily accessible to researchers\nvia a user-friendly interface.\n!',
    ]
)
# [{'corpus_id': ..., 'score': ...}, {'corpus_id': ..., 'score': ...}, ...]
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

## Evaluation

### Metrics

#### Cross Encoder Correlation

* Dataset: `disease-relevance`
* Evaluated with [<code>CrossEncoderCorrelationEvaluator</code>](https://sbert.net/docs/package_reference/cross_encoder/evaluation.html#sentence_transformers.cross_encoder.evaluation.CrossEncoderCorrelationEvaluator)

| Metric       | Value      |
|:-------------|:-----------|
| pearson      | 0.735      |
| **spearman** | **0.7172** |

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 438 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 438 samples:
  |         | sentence_0                                                                                    | sentence_1                                                                                         | label                                                          |
  |:--------|:----------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                                        | string                                                                                             | float                                                          |
  | details | <ul><li>min: 3 characters</li><li>mean: 18.28 characters</li><li>max: 37 characters</li></ul> | <ul><li>min: 31 characters</li><li>mean: 2185.45 characters</li><li>max: 5725 characters</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.39</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                  | sentence_1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | label            |
  |:--------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
  | <code>Breast Cancer</code>                  | <code>Cholesterol promotes breast cancer progression: establishing the mechanisms ﻿   <br>DESCRIPTION (provided by applicant): The purpose of this K08 Mentored Clinical Scientist Development Award proposal is to describe the five year training, development and mentorship plan for Dr. Emily Gallagher, in addition to her research plans to understand the link between obesity, Type 2 diabetes and breast cancer, specifically by examining the effect of high circulating cholesterol on breast cancer progression. Dr. Gallagher received her MD with honors from the University College Dublin, Ireland. She trained clinically in Ireland before moving to New York and is Board Certified in Internal Medicine and Endocrinology. As a clinician, Dr. Gallagher recognized the importance of basic science research in advancing clinical medicine. She moved to the United States to develop her career as a clinician-scientist and began her research studying the mechanisms linking obesity and Type 2 diabetes with breast ca...</code>                            | <code>1.0</code> |
  | <code>Progressive supranuclear palsy</code> | <code>Multi-modal magnetic resonance imaging in progressive supranuclear palsy (PSP) PROJECT SUMMARY/ABSTRACT<br>This is an application for a Mentored Patient-Oriented Research Career Development Award (K23). The goal<br>of the proposed project is to provide the candidate with skills necessary to develop an independent research<br>program dedicated to the development of neuroimaging biomarkers in Progressive Supranuclear Palsy (PSP)<br>and other Alzheimer disease-related dementias. To facilitate this long-term career goal the candidate will: 1)<br>identify multimodal (volumetric, structural and functional connectivity) magnetic resonance imaging (MRI)<br>differences among 3 PSP subtypes (PSP-Richardson syndrome (PSP-RS), PSP-Speech/Language Disorder<br>(PSP-SL), and PSP-Corticobasal syndrome (PSP-CBS)) as delineated in the recently revised PSP diagnostic<br>criteria, and 2) examine the associations between these imaging features with cross-sectional characteristics<br>and 1-year clinical change. The candidate proposes...</code>    | <code>1.0</code> |
  | <code>multiple sclerosis </code>            | <code>A novel monobody-drug conjugate to treat mutant Ras multiple myeloma Project Summary: Multiple myeloma is an incurable hematologic malignancy with an expected<br>median survival of 7-8 years. The proteasome inhibitors, bortezomib, carfilzomib and the recently<br>approved ixazomib, are a mainstay of current myeloma treatment. Despite an initial response rate<br>approaching 90% to proteasome inhibitor-containing combinations, all patients relapse and<br>eventually become resistant to any treatments. Approximately 50% of these patients harbor<br>mutant NRas or KRas. We have observed that mutant Ras multiple myeloma cells display high<br>levels of macropinocytosis, a nutrient scavenging process that facilitates the bulk engulfment of<br>extracellular fluid and its solutes. Harnessing this metabolic adaptation, we have created<br>macropinocytosis-targeting monobodies that carry an FDA-approved cytotoxic payload (vc-<br>MMAE). In vitro proliferation assays demonstrate that the monobody-drug conjugates show<br>selectivity...</code> | <code>0.0</code> |
* Loss: [<code>BinaryCrossEntropyLoss</code>](https://sbert.net/docs/package_reference/cross_encoder/losses.html#binarycrossentropyloss) with these parameters:
  ```json
  {
      "activation_fn": "torch.nn.modules.linear.Identity",
      "pos_weight": null
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `eval_strategy`: steps
- `per_device_train_batch_size`: 4
- `per_device_eval_batch_size`: 4
- `num_train_epochs`: 4

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: steps
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 4
- `per_device_eval_batch_size`: 4
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 4
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `project`: huggingface
- `trackio_space_id`: trackio
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `hub_revision`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: no
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: True
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: proportional
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch | Step | disease-relevance_spearman |
|:-----:|:----:|:--------------------------:|
| 0.5   | 55   | 0.3126                     |
| 1.0   | 110  | 0.4074                     |
| 1.5   | 165  | 0.5106                     |
| 2.0   | 220  | 0.5774                     |
| 2.5   | 275  | 0.6670                     |
| 3.0   | 330  | 0.6723                     |
| 3.5   | 385  | 0.7075                     |
| 4.0   | 440  | 0.7172                     |


### Framework Versions
- Python: 3.10.19
- Sentence Transformers: 5.0.0
- Transformers: 4.57.3
- PyTorch: 2.7.1+cu126
- Accelerate: 1.12.0
- Datasets: 4.5.0
- Tokenizers: 0.22.1

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->