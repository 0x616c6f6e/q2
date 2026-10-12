# Q2 workspace development

Read README.md, docs/architecture.md, docs/development.md, docs/configuration.md and ai/README.md.
This is the product integration repository; app/, kernel/ and platform/ are independent Git repositories
registered as submodules. Root commits pin their revisions; implementation commits belong to each child.
Inspect git status in the repository you change. Do not flatten repositories or auto-add gitlinks/remotes.
Use q2.json as the product settings source; q2.py/build.ps1/run.ps1 are product entry points.
Keep generated artifacts in root build/ and dist/. Never reuse CMake caches from before the directory move.
Kernel stays portable C11; platform owns SDKs/input recognition, apps own Lua/UI/business behavior.
Follow the local child AGENTS.md, public API comments, q2_result_t and four-space/110-column style.
Do not modify third_party, physical hardware, CAD or persistent media as part of software organization.
Run relevant builds/tests and kernel/scripts/check_contracts.py; distinguish simulations from real hardware.
