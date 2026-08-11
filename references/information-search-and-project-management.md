# Information Search and Project Management

## Contents

- Source hierarchy and claim labels
- Search workflow
- Freshness and conflict handling
- Cycle timeline
- Workspace schema
- Visual dashboard workflow
- Deadline and version control
- Notion mapping
- Audit cadence

## Source hierarchy and claim labels

Use the strongest source available for each claim:

1. official program, graduate-school, faculty, lab, funding, government, or foundation page;
2. official application portal text or direct written answer from the responsible office;
3. peer-reviewed paper or official research artifact for research claims;
4. current student or alumni account for lived experience;
5. community collection or blog for discovery, framing, and historical experience.

Label notes as one of:

- **Verified fact:** directly supported by a current authoritative source.
- **Historical fact:** accurately describes a past cycle or dated experience.
- **Inference:** reasoned from evidence but not stated by the source.
- **Opinion or preference:** depends on the applicant's values.
- **Unknown:** requires verification.

Do not silently upgrade a discovery source into policy.

## Search workflow

### Requirements

Use queries such as:

- `[institution] [program] PhD admissions requirements [cycle]`
- `site:[official-domain] PhD application deadline computer science`
- `site:[official-domain] English proficiency waiver graduate`
- `site:[official-domain] funding guarantee PhD computer science`
- `site:[official-domain] application fee waiver graduate`

Open both the department and graduate-school pages. Capture the exact wording needed to support the tracker field, not just a search snippet.

### Faculty and research

Use queries and citation trails such as:

- `[faculty] lab current research`
- `site:[official-domain] [faculty] students publications`
- `[research question] survey recent paper`
- the faculty member's recent papers, grants, talks, code, and group news.

Confirm current affiliation, advising eligibility, and recency. A publication match does not prove recruiting availability.

### Funding and access

Search the program, central graduate school, and funding organization separately. Check eligibility, covered costs, duration, deadline, nomination rules, and citizenship or residency constraints.

## Freshness and conflict handling

For every changing fact, store:

- `authoritative_url`;
- `last_checked` in ISO format `YYYY-MM-DD`;
- a short evidence note or quoted label, not a long copyrighted passage;
- `verification_status`: `verified`, `conflict`, `needs_confirmation`, or `historical`.

Recheck high-risk facts shortly before action:

- deadlines and time zones;
- faculty-contact or recruiting instructions;
- tests, waivers, and transcript rules;
- fee waivers and fellowship eligibility;
- funding amount, duration, fees, and summer support;
- prompt text and document limits.

If official pages conflict:

1. record both URLs and access dates;
2. prefer the more specific and current page only when that priority is defensible;
3. mark the field `conflict`;
4. draft one concise question to the responsible office;
5. update the record with the answer and date.

## Cycle timeline

Adapt this North American-style example to the actual region and opportunity.

### Spring and early summer

- test whether a PhD fits through real research exposure;
- build the evidence inventory and strengthen research relationships;
- identify research questions and start faculty/program discovery;
- inspect funding, test, transcript, and passport or visa lead times;
- ask potential recommenders what evidence would help them write strongly.

### Late summer

- create the workspace and initial list;
- confirm admission models and multiple plausible advisors;
- draft the research narrative, CV, and reusable statement core;
- schedule tests only when current requirements justify them;
- investigate fee waivers and support programs early.

### Early autumn

- narrow the list based on fit, funding, and constraints;
- request letters with a complete packet;
- tailor documents to exact prompts;
- contact faculty only when appropriate;
- request official clarifications before offices become overloaded.

### Late autumn and submission period

- freeze prompts and requirements into the tracker with dates;
- run program-by-program integrity checks;
- submit before the final hours when possible;
- confirm payment or waiver, document receipt, and letter status;
- save a copy of every submitted version and confirmation.

### Interview and decision period

- prepare layered explanations of projects;
- track conversations, unanswered questions, and follow-ups;
- compare written funding details and speak with current students;
- make the decision using both research and life criteria;
- archive final outcomes without treating them as a talent ranking.

For rolling vacancies, work backward from each deadline rather than forcing an annual calendar.

## Workspace schema

Choose the interface based on the applicant's comfort: use the local visual dashboard when they are comfortable starting a local tool, and use Notion when they want a no-code interface. Do not ask a non-coder to manipulate CSV manually. Both paths use the entities below.

The templates under `assets/workspace/` intentionally separate entities that are often mixed in one spreadsheet.

### `profile.json`

Stores cycle, regions, time zone, research questions, constraints, budget, and optional eligibility notes. Keep sensitive data minimal.

### `data/programs.csv`

One row per degree program or advertised position. Important fields include:

- stable `program_id`;
- institution, program, country, degree, and admission model;
- official, requirements, and funding URLs;
- deadline with time zone;
- funding, fees, waivers, tests, essays, and letter count;
- application status, verification status, last checked, and notes.

### `data/faculty.csv`

One row per faculty-program relationship. Track recent research, question and method fit, advising eligibility, recruiting/contact policy, source, last checked, and outreach state.

### `data/materials.csv`

One row per required artifact. Keep prompt, limit, source URL, version, local file, reviewer, status, and deadline separate. A program may require both an SOP and a research proposal; never merge them into one selector.

### `data/recommenders.csv`

Track whether a strong letter is confirmed, evidence themes, packet and reminder dates, submission mechanism, and status. Do not store confidential letter content.

### Other files

- `data/tasks.csv`: owner, due date/time zone, dependencies, and status.
- `data/contacts.csv`: faculty or admissions outreach, purpose, dates, and response.
- `data/interviews.csv`: participants, preparation, questions, follow-up, and evidence learned.
- `data/offers.csv`: funding, mentoring, climate, accessibility, costs, risks, and unknowns.
- `notes/research-narrative.md`: project evidence and future-question development.
- `notes/offer-decision.md`: must-haves, veto conditions, title-removal test, evidence, and consciously accepted uncertainty.
- `notes/wellbeing-plan.md`: boundaries, support, routines, and escalation options.
- `materials/`: shared drafts and program-specific submitted versions.
- `evidence/`: private project notes or artifact pointers; never publish confidential data.
- `archive/`: automatic dashboard backups and final-cycle snapshots.

## Visual dashboard workflow

For users comfortable with local developer tools:

1. Initialize the cycle folder with `init_application_workspace.py`.
2. Start `serve_application_dashboard.py` from the skill directory.
3. Use the browser dashboard to add, filter, edit, and review records; do not require manual CSV work.
4. Let Codex or Claude Code inspect and update the same folder when the user requests coaching or bulk changes.
5. Run the audit script after material changes and before deadlines.
6. Keep the folder private; use private version control only if the user understands what is being stored.

The server must bind to `127.0.0.1` by default, avoid analytics or external storage, validate table names and fields, and create a backup before replacing data. Explain that anyone with access to the local account and folder can read the data.

## Deadline and version control

- Store deadline and IANA time zone separately; never assume local midnight.
- Convert deadlines into the applicant's time zone for planning while preserving the official time.
- Create internal deadlines with buffers for recommenders, uploads, payment, and technical failure.
- Use stable filenames such as `institution-document-v03-2026-11-18.pdf`.
- Preserve the exact submitted file and portal confirmation.
- Track facts and prose separately: a shared research narrative can feed several documents, but each prompt gets its own final artifact.
- Do not place confidential, identity-sensitive, or financial documents in a public repository.

## Notion mapping

Use Notion as the primary no-code interface for applicants who prefer it. Keep the portable schema as the shared conceptual model so exports remain intelligible to other tools.

Recommended databases:

| Notion database | Local source | Key relations |
| --- | --- | --- |
| Programs | `data/programs.csv` | Faculty, Materials, Tasks, Interviews, Offers |
| Faculty | `data/faculty.csv` | Programs, Contacts |
| Materials | `data/materials.csv` | Programs, Tasks |
| Recommenders | `data/recommenders.csv` | Programs or deadline views |
| Tasks | `data/tasks.csv` | Programs, Materials |
| Contacts | `data/contacts.csv` | Faculty, Programs |
| Interviews | `data/interviews.csv` | Programs, Faculty |
| Offers | `data/offers.csv` | Programs |

Keep authoritative URLs and freshness fields on the records they support. Add a separate Sources database only when the applicant genuinely needs claim-level provenance; do not create extra database complexity by default.

When adapting an existing PhD Application OS:

- preserve faculty outreach, deadlines, document versions, and application status;
- split combined `RP/SOP` into separate material records;
- remove recruitment leftovers such as “company,” “recruiter,” or “hiring manager” unless applying to a salaried vacancy where they are accurate;
- add authoritative source URL, `last_checked`, and verification status;
- distinguish region and admission model;
- keep recommenders and confidential notes permission-restricted.

Before any Notion write:

1. inspect the current schema and permissions;
2. produce a preview of databases, properties, relations, and rows to change;
3. state whether the operation creates, updates, or archives anything;
4. obtain explicit confirmation for that operation;
5. write the smallest verified batch;
6. read back the changed records and report discrepancies.

## Audit cadence

Run `scripts/audit_application_workspace.py`:

- after importing or creating the workspace;
- weekly while researching programs;
- before requesting letters;
- two weeks and two days before each deadline;
- before submitting;
- when comparing offers.

Treat the audit as a prompt for human verification, not proof that an application is correct.
