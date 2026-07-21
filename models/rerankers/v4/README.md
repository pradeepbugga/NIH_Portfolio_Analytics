---
tags:
- sentence-transformers
- cross-encoder
- reranker
- generated_from_trainer
- dataset_size:416
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
      value: 0.6853995781612715
      name: Pearson
    - type: spearman
      value: 0.6833947692120163
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
    ['acute kidney injury', 'PERFUSION MR IMAGING OF RENAL ALLOGRAFT REJECTION Kidney transplantation is the preferred and cost effective treatment            \nfor end-stage renal disease. Following transplantation, allograft               \nrejection remains a frequent complication in spite of immunosuppressive         \ndrugs. Acute rejection (AR) in the immediate post-transplant period is          \nthe leading cause of graft loss contributing to increased morbidity and         \ncost. Early diagnosis of AR is essential for effective treatment.               \nDefinitive diagnosis of rejection provided by biopsy, which is invasive         \nand thus accompanies some risk. Since rejection is manifested earliest          \nin the vascular bed, measurement of true tissue perfusion should be an          \nearly indicator of the rejection process. Perfusion MRI is proposed as          \na non invasive method for diagnosis of acute rejection in renal                 \nallografts.                                                                     \n                                                                                \nThe proposed research will develop perfusion imaging of human kidneys           \nusing the MRI method of magnetic labeling arterial water. With this             \napproach, the regional distribution of perfusion can be measured                \nquantitative without using exogenous tracers. Perfusion MRI will be             \ndeveloped using the echo-planar imaging technique (EPI) as fast data            \nacquisition enables perfusion images through the entire kidney to be            \nacquired in a single study session.                                             \n                                                                                \nAR must be distinguished from other complications of transplantation            \nsuch as acute tubular necrosis and immunosuppressive drug toxicity.             \nThis proposal will test the hypothesis that reduction in tissue                 \nperfusion as measured by MRI will be more prominent during AR than in           \nother complications. Renal transplant recipients will be studied with           \nperfusion MRI during the first three months following the                       \ntransplantation procedure. The significance of the differences in the           \nmeasured perfusion under different medical conditions, as indicated             \nbiopsy and biochemical data, will be determined. Perfusion                      \ncharacteristics of renal allografts measured perfusion MRI offer                \npotential clinical application to diagnosis of AR.'],
    ['chronic kidney disease', 'Effect of Chronic HIV Infection on Progression of Kidney Disease (MSSM) PROJECT SUMMARY: \nWith the widespread use of combination antiretroviral agents, the incidence of HIV-associated \nnephropathy (HIVAN) has dramatically decreased in the recent years. Yet, the prevalence of chronic \nkidney disease (CKD) and end-stage renal disease (ESRD) in HIV sero-positive patients remains \nhigh, suggesting that HIV-positive patients are at increased risk for a variety of acute and chronic \nkidney diseases. Indeed, several lines of evidence from recent epidemiological and animal model \nstudies indicate that concurrent HIV infection and age-related comorbidities, such as diabetes \nmellitus, have a synergistic effect on the incidence of chronic kidney disease, thereby necessitating \nan examination of mechanisms by which HIV infection accelerates the progression of CKD such as \ndiabetic kidney disease (DKD). We have recently shown that the upregulation of local inflammation \ninduced by HIV aggravates the progression of DKD through increased transcriptional activities of NF- \nκB and STAT3, indicating that HIV-induced chronic inflammation may predispose and excerbate the \ncourse of non-HIV related CKD. We have also shown that SIRT1 histone deacetylase is a key \nmodulator of the transcriptional activities of NF-κB and STAT3 in diabetic kidneys, suggesting that \npro-inflammatory responses that drive CKD progression may share a common pathway. We \ntherefore posit that SIRT1 is a central modulator of chronic HIV infection-induced inflammation \nthrough deacetylation of key transcription factors such as NF-κB and STAT3, and that the regulation \nof SIRT1 and NF-κB may be effective therapeutic approaches against HIV-induced CKD. Using small \nmolecule agonist of SIRT1 and antagonist of NF-κB, and novel transgenic mouse models, we \npropose to determine the role of SIRT1 in regulating HIV-mediated cellular injuries in diabetic \nkidneys. Our results will provide a better understanding of the underlying molecular mechanisms by \nwhich chronic HIV infection accelerates the progression of CKD and a proof-of-concept for novel \ntarget treatment for CKD in HIV patients.'],
    ['Breast Cancer', 'ErbB1 and ErbB2 Roles in Invasion and Intravasation The broad, long-term objectives of this project are to determine the contributions of ErbBt (EGFR/HER1)\nand related molecule ErbB2 (HER2/neu) to breast cancer invasiveness, intravasation and metastasis. The\ncontributions of these molecules to tumor cell motility and invasion rather than growth could be significant\nand not addressed by normal clinical trials. There are three specific aims that will evaluate particular aspects\nof the contributions of ErbB1 and ErbB2 to invasion and intravasation. The first aim will examine the\npossible activation of the EGF/CSF1 paracrine loop by other receptor/ligand pairs besides just EGF and\nCSF1 and the involvement of other stromal cells. The second aim will explore in more detail the elements of\nthe ErbB2 molecule that contribute to invasion and metastasis. The third aim will compare the contributions\nof specific molecules to in vivo invasion and intravasation. These objective will be achieved using a variety\nof breast cancer models including breast cancer cell lines, transgenic models of breast cancer, and xenograft\nmodels of patient cancer. In vivo invasion measurements will be made using imposed ligand sources.\nMultiphoton imaging of multiple cell types using fluorescent protein labeling will define the relationships and\nmotion of both tumor and stromal cells in the primary tumor microenvironment. The relevance of this work is\nin improving our understanding of how breast cancer spreads away from the primary tumor. By identifying\nthe mechanisms by which tumor cells can move out from the primary tumor and enter blood vessels, we\nhope to identify new ways in which metastasis can be attacked.'],
    ['leiomyosarcoma', 'Developmental Research Program Developmental Research Program (DRP): Project Summary / Abstract\nThe Developmental Research Program (DRP) will support the efforts of the Genetics and Genomics of\nLeiomyosarcoma (LMS): Improved understanding of cancer biology and new approaches to diagnosis and\ntreatment SPORE. This DRP will complement or enhance the variety and depth of sarcoma translational\nresearch, seeking to ensure continual renewal of high-quality translational scientific investigation. The DRP\nsupports short-range studies to establish the data needed to facilitate hypothesis-driven translational projects.\nAlthough the DRP will fund established investigators, an important goal is to identify and stimulate interest in\nsarcoma research among groups whose current focus may be different but sufficiently and transitionally related.\nIn addition, we seek to attract early and mid- career investigators and especially Black and Latino or Hispanic\ninvestigators. Co-directing this program will be Steven Robinson, Associate Professor of Medicine at Mayo\nSchool of Medicine. Dr. Robinson is a Jamaican born man educated in Jamaica. For the past 4 years he has\nbeen supported by career development grants to Mayo Clinic including the institutional K12 as well as the Robert\nWood Johnson Foundation Amos Medical Faculty Development Program. Dr. Robinson is recent recipient of\nDepartment of Defense IDEA Award. He also leads a ETCTN clinical trial that evaluates the combination of\nTVEC with radiation therapy for localized sarcoma. Dr. Robinson will also participate in this SPORE by co-leading\nour efforts to improve diversity in patients enrolled in clinical trials as well as increasing minority faculty\nparticipation. Dr. Baker is the Co-Director of this DRP. He is the SPORE Principal Investigator. Dr. Baker has\nmade important contributions to the treatment of sarcomas beginning with the initial identification of doxorubicin\nas an effective drug in sarcoma patients; the establishment of neo-adjuvant therapy strategy making\nosteosarcoma and Ewing sarcoma curable diseases. Dr. Baker has an outstanding record of leadership and\ncollaboration within the sarcoma translational research field. Dr. Baker is most proud of his mentorship efforts.\nNow 15 Professors of Medicine claim Dr Baker as their mentor.\nRobinson and Baker are joined by a highly qualified committee of experienced clinician-scientists (DRP\nCommittee) which reviews and evaluates new pilot projects as the basis of providing recommendations to the\nSPORE Executive Committee (Chair, Judy Garber) and the SPORE MPI, who bear the responsibility to select\nDRP projects appropriate for funding. The DRP Committee includes members from major cancer centers who\npossess expertise in key aspects of sarcoma science and therapeutics, including biology and genetics,\ncorrelative science, sarcoma pathology, molecular diagnostics, sarcoma drug resistance, immuno-oncology and\nstatistical design and analysis. The DRP will provide the depth required to maintain innovation in this SPORE.'],
    ['Rheumatoid Arthritis', 'Biomarkers Of Osteoarthritis--Their Epidemiology Osteoarthritis (OA) is a highly prevalent chronic disease leading to       \nsignificant functional limitations in both males and females, but               \nparticularly women. We propose to characterize the natural history of           \nosteoarthritis (of the knee and hand) using radiographs, interviews and         \nmarkers of cartilage and bone turnover as well as joint inflammation with       \nthis longitudinal study. The specific questions are:                            \n       1.Do biochemical markers of osteoarthritis (OA) provide evidence os      \nOA earlier than radiographs.?                                                   \n       2.Can turnover markers be used to define natural history and             \nprogression of arthritis?                                                       \n      3.Are bone mineral density(BMD) loss and development/initiation of        \nOA highly regulated?                                                            \n                                                                                \n    These questions can be addressed efficiently by concatenating               \nhistorical data from two previously generated population-based groups. One      \npopulation(Tecumseh Bone Health Study) of 573 women was 25-45 years at          \ntheir 1992 baseline evaluation (R01-AR-40888--Bone Mineral Density Change       \nand the Climacteric). Hand and knee films were taken two times four years       \napart (1992 and 1996) along with an annual BMD measurement. Annual urine        \nand serum specimens were collected and are available for analysis of OA         \nmarkers. The second group, from the SWAN Study (NR-04061), is a                 \npopulation-based group of 300 African-American and 150 Caucasian pre and        \nperimenopausal women, aged 42-52 years at their 1996 baseline when hand         \nand knee films were characterized and serum and urine collected.                \n                                                                                \n    To the retrospectively available data, we propose to recontract these       \n1,023 women for radiographs (hand and knee) and interviews in 1998 and          \n2000 and add annual blood and urine collection with identification of           \npotential markers of arthritis (including turnover on bone/collagen and         \ninflammation). This would allow the examination of the initiation of            \nosteoarthritis using radiographs, interviews and turnover biomarkers. This      \ninformation about the natural history of osteoarthritis should allow us to      \nconsider more appropriate prevention and intervention strategies and offer      \nthe potential to identify markers prognostic of disease incidence and of        \nprocesses involved in its pathobiology.'],
]
scores = model.predict(pairs)
print(scores.shape)
# (5,)

# Or rank different texts based on similarity to a single text
ranks = model.rank(
    'acute kidney injury',
    [
        'PERFUSION MR IMAGING OF RENAL ALLOGRAFT REJECTION Kidney transplantation is the preferred and cost effective treatment            \nfor end-stage renal disease. Following transplantation, allograft               \nrejection remains a frequent complication in spite of immunosuppressive         \ndrugs. Acute rejection (AR) in the immediate post-transplant period is          \nthe leading cause of graft loss contributing to increased morbidity and         \ncost. Early diagnosis of AR is essential for effective treatment.               \nDefinitive diagnosis of rejection provided by biopsy, which is invasive         \nand thus accompanies some risk. Since rejection is manifested earliest          \nin the vascular bed, measurement of true tissue perfusion should be an          \nearly indicator of the rejection process. Perfusion MRI is proposed as          \na non invasive method for diagnosis of acute rejection in renal                 \nallografts.                                                                     \n                                                                                \nThe proposed research will develop perfusion imaging of human kidneys           \nusing the MRI method of magnetic labeling arterial water. With this             \napproach, the regional distribution of perfusion can be measured                \nquantitative without using exogenous tracers. Perfusion MRI will be             \ndeveloped using the echo-planar imaging technique (EPI) as fast data            \nacquisition enables perfusion images through the entire kidney to be            \nacquired in a single study session.                                             \n                                                                                \nAR must be distinguished from other complications of transplantation            \nsuch as acute tubular necrosis and immunosuppressive drug toxicity.             \nThis proposal will test the hypothesis that reduction in tissue                 \nperfusion as measured by MRI will be more prominent during AR than in           \nother complications. Renal transplant recipients will be studied with           \nperfusion MRI during the first three months following the                       \ntransplantation procedure. The significance of the differences in the           \nmeasured perfusion under different medical conditions, as indicated             \nbiopsy and biochemical data, will be determined. Perfusion                      \ncharacteristics of renal allografts measured perfusion MRI offer                \npotential clinical application to diagnosis of AR.',
        'Effect of Chronic HIV Infection on Progression of Kidney Disease (MSSM) PROJECT SUMMARY: \nWith the widespread use of combination antiretroviral agents, the incidence of HIV-associated \nnephropathy (HIVAN) has dramatically decreased in the recent years. Yet, the prevalence of chronic \nkidney disease (CKD) and end-stage renal disease (ESRD) in HIV sero-positive patients remains \nhigh, suggesting that HIV-positive patients are at increased risk for a variety of acute and chronic \nkidney diseases. Indeed, several lines of evidence from recent epidemiological and animal model \nstudies indicate that concurrent HIV infection and age-related comorbidities, such as diabetes \nmellitus, have a synergistic effect on the incidence of chronic kidney disease, thereby necessitating \nan examination of mechanisms by which HIV infection accelerates the progression of CKD such as \ndiabetic kidney disease (DKD). We have recently shown that the upregulation of local inflammation \ninduced by HIV aggravates the progression of DKD through increased transcriptional activities of NF- \nκB and STAT3, indicating that HIV-induced chronic inflammation may predispose and excerbate the \ncourse of non-HIV related CKD. We have also shown that SIRT1 histone deacetylase is a key \nmodulator of the transcriptional activities of NF-κB and STAT3 in diabetic kidneys, suggesting that \npro-inflammatory responses that drive CKD progression may share a common pathway. We \ntherefore posit that SIRT1 is a central modulator of chronic HIV infection-induced inflammation \nthrough deacetylation of key transcription factors such as NF-κB and STAT3, and that the regulation \nof SIRT1 and NF-κB may be effective therapeutic approaches against HIV-induced CKD. Using small \nmolecule agonist of SIRT1 and antagonist of NF-κB, and novel transgenic mouse models, we \npropose to determine the role of SIRT1 in regulating HIV-mediated cellular injuries in diabetic \nkidneys. Our results will provide a better understanding of the underlying molecular mechanisms by \nwhich chronic HIV infection accelerates the progression of CKD and a proof-of-concept for novel \ntarget treatment for CKD in HIV patients.',
        'ErbB1 and ErbB2 Roles in Invasion and Intravasation The broad, long-term objectives of this project are to determine the contributions of ErbBt (EGFR/HER1)\nand related molecule ErbB2 (HER2/neu) to breast cancer invasiveness, intravasation and metastasis. The\ncontributions of these molecules to tumor cell motility and invasion rather than growth could be significant\nand not addressed by normal clinical trials. There are three specific aims that will evaluate particular aspects\nof the contributions of ErbB1 and ErbB2 to invasion and intravasation. The first aim will examine the\npossible activation of the EGF/CSF1 paracrine loop by other receptor/ligand pairs besides just EGF and\nCSF1 and the involvement of other stromal cells. The second aim will explore in more detail the elements of\nthe ErbB2 molecule that contribute to invasion and metastasis. The third aim will compare the contributions\nof specific molecules to in vivo invasion and intravasation. These objective will be achieved using a variety\nof breast cancer models including breast cancer cell lines, transgenic models of breast cancer, and xenograft\nmodels of patient cancer. In vivo invasion measurements will be made using imposed ligand sources.\nMultiphoton imaging of multiple cell types using fluorescent protein labeling will define the relationships and\nmotion of both tumor and stromal cells in the primary tumor microenvironment. The relevance of this work is\nin improving our understanding of how breast cancer spreads away from the primary tumor. By identifying\nthe mechanisms by which tumor cells can move out from the primary tumor and enter blood vessels, we\nhope to identify new ways in which metastasis can be attacked.',
        'Developmental Research Program Developmental Research Program (DRP): Project Summary / Abstract\nThe Developmental Research Program (DRP) will support the efforts of the Genetics and Genomics of\nLeiomyosarcoma (LMS): Improved understanding of cancer biology and new approaches to diagnosis and\ntreatment SPORE. This DRP will complement or enhance the variety and depth of sarcoma translational\nresearch, seeking to ensure continual renewal of high-quality translational scientific investigation. The DRP\nsupports short-range studies to establish the data needed to facilitate hypothesis-driven translational projects.\nAlthough the DRP will fund established investigators, an important goal is to identify and stimulate interest in\nsarcoma research among groups whose current focus may be different but sufficiently and transitionally related.\nIn addition, we seek to attract early and mid- career investigators and especially Black and Latino or Hispanic\ninvestigators. Co-directing this program will be Steven Robinson, Associate Professor of Medicine at Mayo\nSchool of Medicine. Dr. Robinson is a Jamaican born man educated in Jamaica. For the past 4 years he has\nbeen supported by career development grants to Mayo Clinic including the institutional K12 as well as the Robert\nWood Johnson Foundation Amos Medical Faculty Development Program. Dr. Robinson is recent recipient of\nDepartment of Defense IDEA Award. He also leads a ETCTN clinical trial that evaluates the combination of\nTVEC with radiation therapy for localized sarcoma. Dr. Robinson will also participate in this SPORE by co-leading\nour efforts to improve diversity in patients enrolled in clinical trials as well as increasing minority faculty\nparticipation. Dr. Baker is the Co-Director of this DRP. He is the SPORE Principal Investigator. Dr. Baker has\nmade important contributions to the treatment of sarcomas beginning with the initial identification of doxorubicin\nas an effective drug in sarcoma patients; the establishment of neo-adjuvant therapy strategy making\nosteosarcoma and Ewing sarcoma curable diseases. Dr. Baker has an outstanding record of leadership and\ncollaboration within the sarcoma translational research field. Dr. Baker is most proud of his mentorship efforts.\nNow 15 Professors of Medicine claim Dr Baker as their mentor.\nRobinson and Baker are joined by a highly qualified committee of experienced clinician-scientists (DRP\nCommittee) which reviews and evaluates new pilot projects as the basis of providing recommendations to the\nSPORE Executive Committee (Chair, Judy Garber) and the SPORE MPI, who bear the responsibility to select\nDRP projects appropriate for funding. The DRP Committee includes members from major cancer centers who\npossess expertise in key aspects of sarcoma science and therapeutics, including biology and genetics,\ncorrelative science, sarcoma pathology, molecular diagnostics, sarcoma drug resistance, immuno-oncology and\nstatistical design and analysis. The DRP will provide the depth required to maintain innovation in this SPORE.',
        'Biomarkers Of Osteoarthritis--Their Epidemiology Osteoarthritis (OA) is a highly prevalent chronic disease leading to       \nsignificant functional limitations in both males and females, but               \nparticularly women. We propose to characterize the natural history of           \nosteoarthritis (of the knee and hand) using radiographs, interviews and         \nmarkers of cartilage and bone turnover as well as joint inflammation with       \nthis longitudinal study. The specific questions are:                            \n       1.Do biochemical markers of osteoarthritis (OA) provide evidence os      \nOA earlier than radiographs.?                                                   \n       2.Can turnover markers be used to define natural history and             \nprogression of arthritis?                                                       \n      3.Are bone mineral density(BMD) loss and development/initiation of        \nOA highly regulated?                                                            \n                                                                                \n    These questions can be addressed efficiently by concatenating               \nhistorical data from two previously generated population-based groups. One      \npopulation(Tecumseh Bone Health Study) of 573 women was 25-45 years at          \ntheir 1992 baseline evaluation (R01-AR-40888--Bone Mineral Density Change       \nand the Climacteric). Hand and knee films were taken two times four years       \napart (1992 and 1996) along with an annual BMD measurement. Annual urine        \nand serum specimens were collected and are available for analysis of OA         \nmarkers. The second group, from the SWAN Study (NR-04061), is a                 \npopulation-based group of 300 African-American and 150 Caucasian pre and        \nperimenopausal women, aged 42-52 years at their 1996 baseline when hand         \nand knee films were characterized and serum and urine collected.                \n                                                                                \n    To the retrospectively available data, we propose to recontract these       \n1,023 women for radiographs (hand and knee) and interviews in 1998 and          \n2000 and add annual blood and urine collection with identification of           \npotential markers of arthritis (including turnover on bone/collagen and         \ninflammation). This would allow the examination of the initiation of            \nosteoarthritis using radiographs, interviews and turnover biomarkers. This      \ninformation about the natural history of osteoarthritis should allow us to      \nconsider more appropriate prevention and intervention strategies and offer      \nthe potential to identify markers prognostic of disease incidence and of        \nprocesses involved in its pathobiology.',
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
| pearson      | 0.6854     |
| **spearman** | **0.6834** |

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

* Size: 416 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 416 samples:
  |         | sentence_0                                                                                    | sentence_1                                                                                         | label                                                          |
  |:--------|:----------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                                        | string                                                                                             | float                                                          |
  | details | <ul><li>min: 3 characters</li><li>mean: 18.15 characters</li><li>max: 37 characters</li></ul> | <ul><li>min: 31 characters</li><li>mean: 2214.24 characters</li><li>max: 5725 characters</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.39</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                          | sentence_1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | label            |
  |:------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
  | <code>acute kidney injury</code>    | <code>PERFUSION MR IMAGING OF RENAL ALLOGRAFT REJECTION Kidney transplantation is the preferred and cost effective treatment            <br>for end-stage renal disease. Following transplantation, allograft               <br>rejection remains a frequent complication in spite of immunosuppressive         <br>drugs. Acute rejection (AR) in the immediate post-transplant period is          <br>the leading cause of graft loss contributing to increased morbidity and         <br>cost. Early diagnosis of AR is essential for effective treatment.               <br>Definitive diagnosis of rejection provided by biopsy, which is invasive         <br>and thus accompanies some risk. Since rejection is manifested earliest          <br>in the vascular bed, measurement of true tissue perfusion should be an          <br>early indicator of the rejection process. Perfusion MRI is proposed as          <br>a non invasive method for diagnosis of acute rejection in renal                 <br>allografts.                                                ...</code> | <code>0.0</code> |
  | <code>chronic kidney disease</code> | <code>Effect of Chronic HIV Infection on Progression of Kidney Disease (MSSM) PROJECT SUMMARY: <br>With the widespread use of combination antiretroviral agents, the incidence of HIV-associated <br>nephropathy (HIVAN) has dramatically decreased in the recent years. Yet, the prevalence of chronic <br>kidney disease (CKD) and end-stage renal disease (ESRD) in HIV sero-positive patients remains <br>high, suggesting that HIV-positive patients are at increased risk for a variety of acute and chronic <br>kidney diseases. Indeed, several lines of evidence from recent epidemiological and animal model <br>studies indicate that concurrent HIV infection and age-related comorbidities, such as diabetes <br>mellitus, have a synergistic effect on the incidence of chronic kidney disease, thereby necessitating <br>an examination of mechanisms by which HIV infection accelerates the progression of CKD such as <br>diabetic kidney disease (DKD). We have recently shown that the upregulation of local inflammation <br>induced by HIV aggravates t...</code>    | <code>1.0</code> |
  | <code>Breast Cancer</code>          | <code>ErbB1 and ErbB2 Roles in Invasion and Intravasation The broad, long-term objectives of this project are to determine the contributions of ErbBt (EGFR/HER1)<br>and related molecule ErbB2 (HER2/neu) to breast cancer invasiveness, intravasation and metastasis. The<br>contributions of these molecules to tumor cell motility and invasion rather than growth could be significant<br>and not addressed by normal clinical trials. There are three specific aims that will evaluate particular aspects<br>of the contributions of ErbB1 and ErbB2 to invasion and intravasation. The first aim will examine the<br>possible activation of the EGF/CSF1 paracrine loop by other receptor/ligand pairs besides just EGF and<br>CSF1 and the involvement of other stromal cells. The second aim will explore in more detail the elements of<br>the ErbB2 molecule that contribute to invasion and metastasis. The third aim will compare the contributions<br>of specific molecules to in vivo invasion and intravasation. These objective will be achieved usin...</code>          | <code>1.0</code> |
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
| 0.5   | 52   | 0.5697                     |
| 1.0   | 104  | 0.5671                     |
| 1.5   | 156  | 0.6030                     |
| 2.0   | 208  | 0.6253                     |
| 2.5   | 260  | 0.6652                     |
| 3.0   | 312  | 0.6745                     |
| 3.5   | 364  | 0.6834                     |


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