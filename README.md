# AI Support Resolution Agent

**AlmaBetter Guided Workshop · Applied AI Developer · Starter**
Project ID: `applied-ai-001`

Build your understanding of a working AI application by using it, exploring its
code, and making a small change—with your AI coding assistant as a guide.

## The problem you will solve

> “My order #1003 hasn't arrived. What can you do?”

A useful support assistant needs more than a convincing answer. It must identify
the order, check its actual status, and recommend a next step that follows company
policy. A language model alone cannot know where a customer's parcel is.

In this workshop, you will explore an assistant that combines **Gemini + structured
output + an Orders API + company policy** to answer delivery questions in a simple
chat interface. It shows the order details alongside the response so the customer
can see the information behind the answer.

This pattern is useful wherever AI needs business facts before it responds—for
example, checking a booking, explaining a service request, or answering an inventory
question. The skill you practise is connecting language understanding to a reliable
data source and clear rules.

## How the workshop works

You start with a working application, not a blank folder. Your coding assistant
helps you run it, asks questions, and guides you through one step at a time. You
inspect the real files and make the changes yourself, with hints when needed.

By the end, you should be able to:

- Explain which parts of an answer come from the model, the API, and company policy.
- Use structured output to turn a customer message into fields software can use.
- Trace a request through a tool/API call and back to the UI.
- Add a small feature and check that existing requests still work.
- Explain how Docker packages the application and how it reaches the cloud.

Progress depends on demonstrating understanding and completing the activities.
The guide adjusts explanation depth to your experience.

## Start your guided project

Have Python 3.13, your AI coding IDE, and a Google account available. Open this
project folder and connect the instructor's AlmaBetter MCP service for onboarding
and progress recording. Then tell your coding assistant:

> **Start my AlmaBetter project**

The guide will collect your registration and concept familiarity, then begin:

| Step | Your activity |
|---|---|
| 1 | Understand the customer-support problem |
| 2 | Create your own Gemini API key and run the app locally |
| 3 | Trace how a request moves through the application |
| 4 | Explore the five core files |
| 5 | Understand structured output, tools, context, and when RAG is useful |
| 6 | Add a `priority` field for urgent requests |
| 7 | Follow the instructor's Docker and Azure deployment demonstration |
| 8 | Solve a final support scenario and explain the system |

**You do not need to complete setup alone.** Step 2 guides you through creating
your own key, saving it locally, and testing the application. Students do not
configure Azure; deployment is an instructor demonstration.

## What the application does

```text
Customer message → Understand the request → Fetch order facts
                 → Apply company policy → Explain the next step
```

Try “Where is order ee64d42b8cf066f35eac1cf57de1aa85?”
The app reads historical order records from the hosted workshop API and makes real Gemini
calls using your key. The model selects a tone and next step; Python inserts verified
order facts into the answer. It cannot issue refunds, change orders, or create tickets.
Include one order number per message; displayed chat history is not sent to Gemini.

## Five files to explore

| File | What you will learn from it |
|---|---|
| `app.py` | How customer input and order details appear in the UI |
| `agent.py` | How the AI workflow connects understanding, facts, and policy |
| `models.py` | How structured data makes model output usable by code |
| `tools.py` | How the application looks up an order in the hosted dataset |
| `policy.md` | How company rules shape the next step |

The remaining files support setup, testing, and deployment. `AGENTS.md` and
`.almabetter/` give the coding assistant its teaching instructions. You do not need
to study every file before starting. There is no RAG implementation in this project.

## Local setup reference

Use these commands with your guide, from this folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` only if it does not already exist. Create your own key
in [Google AI Studio](https://aistudio.google.com/apikey) and personally paste it into
`GEMINI_API_KEY` in `.env`. Never share the key in chat or commit it to GitHub.
The app loads `.env` automatically. API quotas and possible charges depend on your
account and model.

The [Orders API](http://4.186.26.27:8787/ecommerce?dataset=orders) is already hosted
and its URL is fixed in `tools.py`. Students only configure `GEMINI_API_KEY`.
Start the application with one command:

```sh
.venv/bin/python -m streamlit run app.py
```

On Windows, create the environment with `py -3.13 -m venv .venv` and replace
`.venv/bin/python` with `.\.venv\Scripts\python.exe` in subsequent commands.
Open http://localhost:8501—no Deploy button is needed.

Example IDs: `ee64d42b8cf066f35eac1cf57de1aa85` (shipped),
`15bed8e2fec7fdbadb186b57c46c92f2` (processing), and
`e481f51cbdc54678b7cc49136f2d6af7` (delivered), as recorded in the dataset.
These are historical records, not live tracking; use the API's returned status
and dates. The opening story's short order numbers are illustrative only.
The endpoint returns the full dataset, so lookup may take a few seconds.
If a request fails, check internet access, API availability and your Gemini key/quota.
Restart Streamlit after editing `.env`; exported variables take precedence.

<details>
<summary>Instructor and maintainer reference</summary>

`tools.py` requests the fixed dataset URL, selects the exact order ID, and maps
`order_status` and delivery dates into `models.Order`. It never creates a current
tracking update or falls back to made-up records. The full dataset remains in the
lookup process; only the selected order's support fields are sent to Gemini.

Build with `docker build -t applied-ai-001 .`. The image runs Streamlit on port 8501.
For Azure Container Apps, configure ingress on that port and a Gemini key secret.
The app calls the existing Orders API; no second service or API URL setting is needed.

Run checks from this folder:

```sh
.venv/bin/python -m pip install pytest==9.1.1
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

Tests mock the hosted HTTP response and Gemini replies. Live Gemini checks need a key.
Keep status-specific checks in `agent.py` aligned with changes to `policy.md`.

</details>
