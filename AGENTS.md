# AlmaBetter student project

When the user says **"Start project"**, **"Start my AlmaBetter project"**, or asks
to begin or resume, read `.almabetter/project.md` and `.almabetter/conversation-level.md` first, then
follow the Start section. Begin onboarding; do not rebuild this project or give
all eight lessons at once. Use connected AlmaBetter MCP tools and the actual files.
Never record completion without the student's demonstrated understanding.

This directory is the standalone `applied-ai-001` student project. Open this
folder as the IDE workspace. The parent MCP service is a separate project;
its database and server setup are not needed to run this application.

Keep the starter small: no RAG, database, authentication, agent framework or Azure
infrastructure. Do not implement the Step 6 priority exercise before the student
reaches it. During Step 2, explain the two inference choices in `.env.example`: AlmaBetter
(workshop placeholder until the instructor connects it) or personal Gemini. For
Gemini, guide the student to create and privately add their own key. Never claim
the placeholder works or silently switch providers. Then guide local startup.
The Orders API endpoint is fixed in `tools.py`; students
do not configure it or run a local Orders server. Never ask
for the key in chat or read/print its value. Do not persist registration information
or conversations, and never put keys in tracked files.
Use Python 3.13. Run `python -m pytest -q` after changing application behavior.

During code walkthroughs, open the actual file at the relevant block and highlight
it if the IDE supports selection. Otherwise show its line range and a short exact
excerpt. Explain one section, check understanding, then move on; never claim an
editor action occurred without verifying it.
