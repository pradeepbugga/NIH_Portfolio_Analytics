from openai import OpenAI
from dotenv import load_dotenv
from core.db.connection import get_db_connection
import os
import json

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=API_KEY)

PROMPT = f"""You are a scientific grant abstract classifier.

Classify the following NIH-style project title + abstract into exactly ONE of the categories listed below.
Return ONLY valid JSON in this format:
{{
 "category": "<one category from the list>" 
}}

Do not include explanations or extra text.

Categories
1. Mechanistic / Basic Science
 Molecular, cellular, biochemical, or genetic mechanism studies
 Animal model pathogenesis research
 Synthetic chemistry
 Structural biology
 Fundamental biology without testing a clinical intervention
2. Therapeutic (Drug/Biologic Testing)
 Preclinical therapeutic testing
 Drug efficacy studies
 Pharmacology studies
 Randomized clinical trials of a therapeutic
 Prevention or treatment strategy trials
Primary focus: testing whether an intervention improves outcomes.
3. Therapeutic Platform
 Development of a new therapeutic modality or platform technology
 Gene therapy platforms
 Cell therapy engineering systems
 Drug delivery systems
 Novel therapeutic scaffolds
 Platform technologies enabling multiple therapies
Primary focus: building a reusable therapeutic engine, not testing one specific drug alone.
4. Medical Device
 Development or testing of a physical device
 Surgical devices
 Wearables used as devices
 Hardware-based treatment or monitoring systems
Primary focus: device engineering or validation.
5. Diagnostic / Biomarker Development
 Diagnostic assay development
 Biomarker validation
 Risk stratification tools
 Imaging-based diagnostic tool validation
 Clinical outcome assessment (COA) development
Primary focus: measuring or detecting disease.
6. Clinical Outcomes / Effectiveness
 Observational clinical comparative studies
 Outcomes research
 Non-randomized comparative effectiveness
 Patient-centered outcomes
 Real-world evidence studies
Primary focus: evaluating clinical results, not introducing a new therapy.
7. Clinical Infrastructure / Care Delivery
 Health services research
 Care coordination
 Telemedicine
 Workflow redesign
 EHR optimization
 Patient safety systems
Primary focus: improving how care is delivered.
8. Observational Epidemiology
 Cohort studies
 Environmental exposure studies
 Population risk factor analysis
 Natural history studies
 Genetic epidemiology
Primary focus: identifying associations at population level.
9. Implementation Science
 Adoption of evidence-based practices
 Fidelity monitoring
 Dissemination strategies
 Organizational change interventions
 Sustainment studies
Primary focus: implementing known interventions in real-world settings.
10. Research Tool
 Model organism development
 Laboratory tool development
 Assay development for research use
 Data analysis pipelines for scientific discovery
 Technology intended primarily for research use
Primary focus: enabling scientific research.
11. Translational Infrastructure
 Registries
 Multi-site clinical trial networks
 Data harmonization initiatives
 Natural history databases
 Shared data platforms
Primary focus: enabling large-scale clinical research collaboration.
12. Other
 Administrative cores
 Training grants
 Career development awards primarily focused on training
 Projects not fitting the above
 """
    

def classify_grant(title,abstract):
    response = client.responses.create(
        model="gpt-5-nano",
        reasoning={"effort": "high"},
        input=[{"role": "system", "content": PROMPT}, 
               {"role": "user", "content": f"Title: {title}\nAbstract: {abstract}"}]
    )

    content = response.output_text

    try:
        extracted = json.loads(content)
        category = extracted.get("category", "Unknown")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON response: {content}")

    return category

if __name__ == "__main__":
    title = "Role of Complement Proteins in E. coli Meningitis"
    abstract = """DESCRIPTION (provided by applicant): Neonatal E. coli K1 meningitis is the most common serious infection of the central nervous system with unchanged rates of mortality and morbidity. Survivors of this disease suffer a number of complications including mental retardation and speech impairment. Limited knowledge about the pathogenesis and pathophysiology of this disease hampered the efforts to develop new therapeutic strategies for the prevention. For example, most cases of E. coli K1 meningitis occur via hematogenous spread, but it is unclear how the circulating E. coli evades the host-defense mechanisms. The investigator's studies have shown that outer membrane protein A (OmpA) of E. coli contributes to resistance to serum bactericidal activity. In addition, OmpA interacts with a brain specific 95 kDa receptor for E. coli invasion of the blood-brain barrier (BBB). The E. coli invasion of the BBB was significantly reduced in the presence of adult human serum (AHS) when compared to cord blood serum (CBS) using the investigator's in vitro model of the BBB, the cultured brain microvascular endothelial cells (BMEC). His data further showed that OmpA binds to C4-binding protein, a complement fluid phase regulator, in significant quantities from AHS when compared to CBS. A compelling observation is that the binding of C4-binding protein to OmpA blocked the E. coli invasion of BMEC, suggesting that it is competing with the OmpA-receptor. The investigator hypothesized that binding of C4BP to OmpA blokcs the E. coli invasion of BMEC and that low levlels of C4BP may contribute to the susceptibility of neonates to E. coli meningitis. He will pursue this hypothesis by study of the following specific aims. 1. To determine the binding site of C4BP on OmpA that blocks E. coli invasion of BMEC, and 2. To assess the effect of anti-OmpA antibody, OmpA-peptides, and C4BP-peptides on E. coli invasion of BMEC in the newborn rat model of hematogenous meningitis."""

    category = classify_grant(title, abstract)
    print(f"Predicted category: {category}")