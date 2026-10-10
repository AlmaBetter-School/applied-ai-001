# Where is my order?

**AlmaBetter guided workshop · applied-ai-001**

Imagine your headphones have not arrived and your next online class is tomorrow.
A friendly reply helps, but you also need someone to check what happened and explain
what you can do. In this project, Python looks up an order and DeepSeek helps choose
an appropriate response using the shop's rules.

You will run an existing app, explore how its parts work together, and follow the
instructor as they package it with Docker and demonstrate running it on Azure.
No previous AI, API, or cloud experience is assumed.

## Start here

1. **Open VS Code.** This is where you will open the project and chat with your guide.
2. **Fork the workshop repository.** Open the GitHub link shared by the instructor
   ([applied-ai-001](https://github.com/AlmaBetter-School/applied-ai-001)), sign in,
   and choose **Fork**. This creates your own copy on GitHub.
3. **Clone your fork to Desktop.** Copy the HTTPS URL from your fork's **Code**
   button. In VS Code, use **Clone Repository**, paste that URL, and select
   **Desktop** as the destination. Cloning downloads the files onto your computer.
4. **Open the cloned folder and start.** Open `Desktop/applied-ai-001` in VS Code.
   In the coding assistant's chat, say **“Start project.”** This is a chat message,
   not a terminal command. The guide asks for your name, then collects the remaining
   registration details one at a time.

Next comes skill familiarity, the customer problem, and the six learning steps
below. If the folder is already open, start from step 4; do not fork or clone again.

The workshop connection is included in `.vscode/mcp.json`; students do not add an
MCP endpoint before starting. If VS Code shows a workspace or tool permission
prompt, handle it with the instructor when it appears. If registration cannot be
saved, the guide helps restore that connection and resumes the same activity.
You do not need to study the guide files, add the DeepSeek key, or install the app
before registration. Local app setup comes in learning Step 2.

| Step | What you do |
|---|---|
| 1 | Meet the customer and understand what useful help looks like |
| 2 | Run the app on your computer and try a conversation |
| 3 | Explore the files, one small section at a time |
| 4 | Follow one question through the whole app |
| 5 | Understand how RAG helps an assistant find useful help documents |
| 6 | Understand Docker and watch the instructor's Azure demonstration |

Every step follows the same simple rhythm: understand why the step matters, do
one small activity, explain what you noticed, and then move to the next step.
The tutor will pause at a practical checkpoint instead of giving a long quiz.
Treat each activity like a small support mystery: notice the customer problem,
inspect one part of the app, make a prediction, and test it in the browser.

The RAG activity is a short, guided example: find the relevant help passage, give
it to the AI, then explain the answer. It adds no code or packages; the app still
uses one order lookup and its small policy file.

## Four files tell the story

| File | Its job |
|---|---|
| `app.py` | The screen: messages, answers, and order details |
| `tools.py` | The lookup: find the order in the shop's records |
| `policy.md` | The rules: what help the shop allows |
| `agent.py` | The coordinator: connect the message, records, rules, and DeepSeek |

`requirements.txt` lists the packages to install. `.env` holds your private key.
`Dockerfile` describes the package used in the final demonstration. The small
`AGENTS.md` points the coding assistant to `.almabetter/project.md`; students
follow the conversation, not those internal instructions. `tests/` is for maintainers.

## Local setup reference

Your guide first asks whether you use macOS/Linux or Windows, then explains each
matching command before you run it. Use Python 3.13.

**macOS / Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

**Windows PowerShell**

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` using the file explorer only if `.env` does not already
exist. Paste the workshop-provided DeepSeek key into that private file:

```dotenv
DEEPSEEK_API_KEY=your_key_here
```

If you need your own key, sign in to the [DeepSeek platform](https://platform.deepseek.com/),
open API keys, and create one. API access needs an available balance. Do not share
your key in chat, screenshots, GitHub, or the Docker image. Restart after changing it.
There is only one AI provider setting: `DEEPSEEK_API_KEY`.

Start the app:

```sh
# macOS / Linux
.venv/bin/python app.py
```

```powershell
# Windows PowerShell
.venv\Scripts\python.exe app.py
```

Open the local address printed in the terminal, usually `http://localhost:7860`.
Ask “Where is order ee64d42b8cf066f35eac1cf57de1aa85?” and then “I need it for class.
What should I do now?” Use **New chat** to clear the chat.

## What this small app can do

Python finds the newest complete order number supplied by the customer and fetches
that order. DeepSeek receives the last six exchanges, the selected record, and the
shop's rules. It returns two short labels: tone and next step. Python checks those
labels and builds an answer with recorded facts. That means one AI request per
successful order lookup, with a 150-token output limit and thinking disabled.
The model is `deepseek-flash`; the HTTPS endpoint is fixed in `agent.py`.
The request follows [DeepSeek’s JSON output format](https://api-docs.deepseek.com/guides/json_mode/).

The [Orders API](http://4.186.26.27:8787/ecommerce?dataset=orders) is fixed in
`tools.py`. It contains historical records, not live tracking. The app cannot
change orders or issue refunds. It uses prepared answer sentences, so this is a
focused support example, not a general-purpose chatbot. Replies appear once ready.
Chat history stays in the current Gradio browser session, not on disk.

## Instructor: Docker and Azure

Explain the Dockerfile before running these commands from the project folder:

```sh
docker build --platform linux/amd64 -t order-support .
docker run --rm -p 7860:7860 --env-file .env order-support
```

Open `http://localhost:7860`. Stop any earlier local app using port 7860 first.
`.dockerignore` keeps the key out of the build; `--env-file` supplies it at runtime.

For Azure Container Apps, the instructor pushes the image to a container registry,
creates a container app using that image, supplies `DEEPSEEK_API_KEY` through an
Azure secret reference, enables HTTP ingress with target port 7860, and tests the
public link. Use the instructor's subscription and configured registry access.
The image contains our app; DeepSeek and the order records remain external services.
Students explain what changed between local and online; they need not provision Azure.
The instructor can use the [Azure portal guide](https://learn.microsoft.com/en-us/azure/container-apps/quickstart-portal)
and [secret configuration guide](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets).

## Maintainer checks

```sh
.venv/bin/python -m pip install pytest==9.1.1
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

Tests simulate the external services and need no key. A live request is a separate
check requiring network access and a working DeepSeek key.
