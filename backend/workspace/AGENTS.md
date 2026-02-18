# AGENTS

## Mandatory Skill Protocol

1. Decide whether an available skill applies based on SKILLS_SNAPSHOT.
2. If a skill applies, the first tool call MUST be `read_file(location)` using the location from snapshot.
3. Do not guess skill steps or parameters before reading the skill file.
4. Execute the skill by following its written steps with core tools only:
   - `terminal`
   - `python_repl`
   - `fetch_url`
   - `read_file`
   - `search_knowledge_base`
5. Report tool usage and important outputs transparently.
