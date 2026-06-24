# Writer materials — distribution packet

Everything you send to each participating screenwriter lives in this folder.

## What to send each writer

| File | Purpose |
|------|---------|
| `ScriptLens_Writer_Instructions.docx` | **Main brief** — Word document with full instructions |
| `starter_5scene.fountain` | Clean 5-scene script (writers inject 2–3 errors) |
| `starter_10scene.fountain` | Clean 10-scene script (writers inject 4–5 errors) |
| `[Your feature script].fountain` or `.pdf` | **You add** — pre-produced full-length script (8–12 errors) |
| `SCREENWRITER_ERROR_CHEAT_SHEET.pdf` | 1-page quick reference |
| `ERROR_INJECTION_LOG_TEMPLATE.yaml` | Blank answer sheet (one copy per writer) |

Zip the folder (plus your feature script) as e.g. `ScriptLens_Writer_Packet.zip`.

## Regenerate the Word document

```powershell
.\venv\Scripts\python.exe scripts\build_writer_packet.py
```

Output: `docs/writer_materials/ScriptLens_Writer_Instructions.docx`

## Starter scripts

- **5-scene:** `starter_5scene.fountain` — thriller mini-arc, 5 INT/EXT headings, no planted errors
- **10-scene:** `starter_10scene.fountain` — expanded same world, 10 scenes, no planted errors
- **Feature:** not included here — add your pre-produced scripts before sending

Writers edit all three; they do not write from scratch.

## Related docs

- Full markdown brief: `docs/SCREENWRITER_ERROR_INJECTION_GUIDE.md`
- Email draft: `docs/WRITER_OUTREACH_MESSAGE.md`
- Internal type mapping: `docs/internal/CATEGORY_TO_ENGINE_MAPPING.md`
