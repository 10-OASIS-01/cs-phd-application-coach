# CS PhD Application Coach

An open, access-conscious Agent Skill for planning, writing, tracking, and evaluating global CS and AI PhD applications.

The coach treats admission as a noisy matching process—not a ranking of human worth or research potential. It helps applicants make research evidence legible, find programs and advisors by substantive fit, verify current requirements, manage materials and letters, prepare for interviews, compare offers, and protect their wellbeing throughout the cycle.

[Project page](https://10-oasis-01.github.io/cs-phd-application-coach/) · [Full application guide](https://10-oasis-01.github.io/blog/the-hidden-curriculum-of-cs-phd-applications/)

## What is included

- A portable `SKILL.md` compatible with the open Agent Skills format.
- Layered references for global application systems, research readiness, materials, information verification, access, interviews, offers, and wellbeing.
- A local visual dashboard backed by ordinary CSV, JSON, and Markdown files.
- A no-code Notion route using the same conceptual data model.
- Workspace initialization, auditing, and local dashboard scripts with no runtime dependencies beyond Python 3.10+.

## Install

### Codex

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/10-OASIS-01/cs-phd-application-coach.git \
  ~/.agents/skills/cs-phd-application-coach
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/10-OASIS-01/cs-phd-application-coach.git \
  ~/.claude/skills/cs-phd-application-coach
```

Then ask your agent to use `cs-phd-application-coach`. The internal instructions follow the user's language unless another language is requested.

## Choose your application workspace

Coding comfort is not research ability. Use the interface that makes the application easier to manage.

### Local visual dashboard

Recommended for applicants comfortable running a local command:

```bash
python3 scripts/init_application_workspace.py \
  --destination /path/to/phd-applications-2027 \
  --cycle 2027

python3 scripts/serve_application_dashboard.py \
  /path/to/phd-applications-2027
```

The dashboard opens on `127.0.0.1`, stores no analytics, and writes only to the selected application folder. It creates a backup before replacing existing data.

Run the audit after material changes and before deadlines:

```bash
python3 scripts/audit_application_workspace.py \
  /path/to/phd-applications-2027
```

### Notion

Recommended for applicants who prefer a no-code workspace. The Skill can propose Programs, Faculty, Materials, Recommenders, Tasks, Contacts, Interviews, and Offers databases with useful relations and views. It previews the schema first and requires confirmation immediately before any external Notion write.

## Workspace structure

```text
phd-applications-2027/
├── profile.json
├── data/
│   ├── programs.csv
│   ├── faculty.csv
│   ├── materials.csv
│   ├── recommenders.csv
│   ├── tasks.csv
│   ├── contacts.csv
│   ├── interviews.csv
│   └── offers.csv
├── notes/
│   ├── research-narrative.md
│   ├── offer-decision.md
│   └── wellbeing-plan.md
├── materials/
│   ├── shared/
│   └── programs/
├── evidence/
└── archive/
```

Keep this folder private. Do not store passports, financial records, confidential recommendation content, or unnecessary identity information in a public repository.

## Example prompts

- “I am an international undergraduate with limited research access and a small budget. Help me decide what to strengthen and build a realistic global list.”
- “I am moving from industry into research without publications. Audit my evidence and create a six-month application plan.”
- “I have two funded offers. Help me compare advisors, mentoring, lab climate, accessibility, funding, switching options, and unresolved risks.”

## Responsible use

The Skill does not replace current program pages, admissions offices, or the applicant's judgment. It must not invent experiences, research claims, faculty fit, policies, funding, or outcomes. Every time-sensitive fact should be attached to an authoritative URL and a `last_checked` date.

## Development

```bash
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
```

Contributions that improve access, regional accuracy, privacy, or usability are welcome. Avoid adding historical policy as current fact, copyrighted application samples, or resources whose licensing is unclear.

## License

[MIT](LICENSE)
