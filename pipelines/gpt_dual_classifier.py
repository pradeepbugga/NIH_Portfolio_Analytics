from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
import asyncio
from tqdm import tqdm
import pandas as pd
from openai import APIError, RateLimitError
import random

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=API_KEY)

SEM = asyncio.Semaphore(50)  # Limit to 5 concurrent requests

NUM_WORKERS = 20

PROMPT = """You are classifying NIH research grants using a dual-axis schema.
You must assign:
INTENT = why the project exists (goal)
FUNCTION = what capability the project produces or applies

These are different concepts and must be assigned independently.
 INTENT describes the primary objective
 FUNCTION describes the operational capability produced or applied

A project may have multiple intents and functions, but only if they are central and distinct.

STAGE 1 — SCORE ALL CATEGORIES
Assign a score to every category:
0 = not present
1 = minor / supporting
2 = primary / central

Return:
{   "intent_scores": 
    {       "Mechanistic / Basic Science": 0-2,
            "Therapeutic": 0-2,
            "Clinical / Health Systems": 0-2,
            "Research Infrastructure / Programmatic": 0-2,     
            "Education / Training": 0-2,     
            "Research Tool / Method": 0-2,     
            "Diagnostic / Biomarker": 0-2},
    "function_scores": 
    {        "Research Tool / Method": 0-2,
            "Diagnostic / Biomarker": 0-2,
            "Therapeutic": 0-2,
            "Research Infrastructure / Programmatic": 0-2   } }

Scoring rules
 Score 2 only if primary
 Score 1 if secondary/supporting
 Score 0 if not meaningful

Use project-level goals, not isolated phrases.

Do NOT assign score = 2 based on:
 a single sentence
 speculative future applications
 minor sub-aims

STAGE 2 — SELECT FINAL LABELS

INTENT
 Include categories with score = 2 only
 Maximum: 2 intents (rarely 3)

FUNCTION
 Include categories with score = 2
 Include categories with score = 1 ONLY IF:
 removing it would lose a distinct capability type, AND
 it is clearly emphasized in the project description
 Maximum: 2 functions (rarely 3)

FUNCTION PRIORITY (tie-breaker)
If more than 2 functions qualify, keep:
 Research Infrastructure / Programmatic
 Diagnostic / Biomarker
 Therapeutic
 Research Tool / Method

DEFINITIONS

INTENT
Mechanistic / Basic Science → understand biological mechanisms
Therapeutic → develop or test interventions
Clinical / Health Systems → improve patient outcomes or care
Research Infrastructure / Programmatic → build shared resources (centers, registries, datasets)
Education / Training → train researchers or clinicians
Research Tool / Method → develop a method, assay, or model system
Diagnostic / Biomarker → develop a prediction or detection system (rare as intent)

FUNCTION
Research Tool / Method → method, assay, model, or pipeline (only if primary contribution)
Diagnostic / Biomarker → prediction, classification, or risk stratification capability
Therapeutic → intervention applied or developed (drug, behavioral, public health, etc.)
Research Infrastructure / Programmatic → registry, dataset, center, or shared resource

CRITICAL RULES
Disallowed
 Mechanistic ❌ FUNCTION
 Clinical ❌ FUNCTION
 Education ❌ FUNCTION

Core distinctions

Tool vs Mechanistic
 Method/system output → Tool
 Biological insight → Mechanistic

Diagnostic vs Clinical
 Prediction/risk/classification → Diagnostic
 Outcomes/care/treatment effects → Clinical

Therapeutic
Includes non-drug interventions:
 behavioral
 community
 public health
 vector control

Infrastructure
If project includes:
 centers, cores, registries, shared datasets
→ INTENT = Infrastructure → FUNCTION = Infrastructure

Tool suppression (important)
Do NOT include Research Tool / Method if:
 method is only used internally
 not a primary contribution
 no emphasis on method development or generalization

Therapeutic intent constraint
Assign Therapeutic ONLY if:
the intervention is a primary variable being tested or manipulated in the project

Do NOT assign Therapeutic if:
the intervention is part of a parent study
the intervention is used only for secondary or exploratory analysis
the project does not control or design the intervention

Diagnostic constraint
Include Diagnostic ONLY if:
 prediction or risk stratification is central to the project’s objective

DIAGNOSTIC INTENT GATING RULE
Assign Diagnostic ONLY if:
the output predicts or classifies a disease, clinical outcome, or biological state in an organism

Do NOT assign Diagnostic for:
chemical screening
population structure inference
statistical or computational classification without a disease/clinical target

Speculative statements
 “Potential application” ≠ assign label
 Only assign if actually developed, tested, or applied

EXAMPLES (for calibration)
Example 1 — Mechanistic study
 Goal: understand reaction mechanism → intent: Mechanistic → function: []
Example 2 — Clinical registry
 Goal: improve care + build registry → intent: Clinical + Infrastructure → function: Infrastructure (+ Diagnostic if strong prediction component)
Example 3 — Tool development
 Goal: develop assay/platform → intent: Tool → function: Tool
Example 4 — Diagnostic system
 Goal: predict disease risk → intent: Diagnostic → function: Diagnostic

FINAL TASK
Return:
{   "intent": [],   "function": [],   "reasoning_intent": "",   "reasoning_function": "",   "intent_scores": {},   "function_scores": {} }

OUTPUT REQUIREMENTS
 Follow scoring → then selection strictly
 Final labels must match scores
 Keep reasoning concise (1–3 sentences each)
"""
    

async def with_retry(coro_fn, *args, **kwargs):
    for i in range(5):
        try:
            # We execute the function HERE, so we can catch the error
            return await coro_fn(*args, **kwargs)
        except (RateLimitError, APIError) as e:
            wait = (2 ** i) + random.random()
            await asyncio.sleep(wait)
    raise Exception("Max retries exceeded")

async def classify_grant(grant_id,title,abstract):
    async with SEM:
        try:
            response = await with_retry(
                client.responses.create,
                model="gpt-5.4",
                reasoning={"effort": "medium"},
                input=[{"role": "system", "content": PROMPT}, 
                    {"role": "user", "content": f"Title: {title}\nAbstract: {abstract}"}]
            )

            if not response.output_text:
                return grant_id,"NoOutput"

            content = response.output_text

            # print usage for debugging
            print(f"Usage for grant {grant_id}: {response.usage}")

            try:
                extracted = json.loads(content)
                return {
                    "grant_id": grant_id,
                    "intent": extracted.get("intent", []),
                    "function": extracted.get("function", []),
                    "reasoning_intent": extracted.get("reasoning_intent", ""),
                    "reasoning_function": extracted.get("reasoning_function", ""),
                    "intent_scores": extracted.get("intent_scores", {}),
                    "function_scores": extracted.get("function_scores", {})
                }

            except:
                return grant_id,"ParsingError"
        except Exception as e:
            print(f"Error classifying grant: {e}")
            return grant_id,"Error"

async def producer(queue, grants):
    for grant in grants:
        await queue.put(grant)
    
    # signal shutdown
    for _ in range(NUM_WORKERS):
        await queue.put(None)

async def worker(queue, results_file, pbar):
    while True:
        item = await queue.get()

        if item is None:
            queue.task_done()
            break

        grant_id, title, abstract = item

        result = await classify_grant(grant_id, title, abstract)

        # write immediately (no memory accumulation)
        results_file.write(json.dumps(result) + "\n")

        pbar.update(1)

        queue.task_done()

async def main():
    # 1. Load from csv
    df = pd.read_csv("./grant_gpt_labels_cumul_domain_fixed_3.csv")
 
    
    
    # 2. Create list of tuples
    grants = list(zip(df["grant_id"], df["title"], df["abstract"]))
   
    # pick a random sample of 100 grants for testing
    #grant_sample = random.sample(grants, 10)

    sample_grant_ids = ["5R01GM062163-06", "5R01DK123549-05", "3R01CA077106-02S1", "5R01ES010804-05", "1R03AG056752-01", "1T32LM012415-01", "5R01DK126903-04", 
                             "4R37AI029168-35", "5R01ES009650-04", "3P01GM045344-14S1"]
    grant_sample = [grant for grant in grants if grant[0] in sample_grant_ids]

    
    # 3. Define total for the progress bar
    total_grants = len(grant_sample)
    pbar = tqdm(total=total_grants, desc="Processing grants")

    queue = asyncio.Queue(maxsize=500)

    # Use 'a' (append) or 'w' (write) mode
    with open("gpt_dual_results.jsonl", "w") as f:
        # Start workers
        workers = [asyncio.create_task(worker(queue, f, pbar)) for _ in range(NUM_WORKERS)]

        # Start producer - Changed 'cur' to 'grants'
        producer_task = asyncio.create_task(producer(queue, grant_sample))

        # Wait for producer to finish putting items in queue
        await producer_task
        
        # Wait for all items in queue to be processed
        await queue.join() 

        # Clean up worker tasks
        for w in workers:
            await w

    pbar.close()
    print("All tasks completed.")
    


if __name__ == "__main__":
    asyncio.run(main())