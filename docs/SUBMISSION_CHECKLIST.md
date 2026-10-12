# Round 2 submission checklist

## Project evidence prepared in this workspace

- [x] README describes setup, architecture, leakage, limitations, and real CV results.
- [x] Model registry, four target models, schema, real metrics, demo patients, and validation figures generated.
- [x] Test and QA checklist documented; automated suite passes in the current environment.
- [x] Report draft updated with saved results and PDF-export instructions.
- [x] Six-minute demo script updated to match the trained build.
- [x] Dataset, software, and optional 3D-asset attribution notes added.
- [ ] Choose and add a project-code license (`LICENSE` is not yet present).

## Owner actions before submission

- [ ] Confirm hackathon rules permit the chosen repository visibility; publish the repository with the required access.
- [ ] Install Node.js 20.19+ and Python dependencies on the recording/demo computer; run `.\run_all.bat`.
- [ ] Complete every manual-browser item in `docs/TESTING.md`; fix any failure and update that evidence.
- [ ] Deploy the Render Blueprint and complete the production smoke test in `docs/RENDER_DEPLOYMENT.md`.
- [ ] Capture screenshots of the dashboard, vessel explanation, and metrics tab; replace README placeholders.
- [ ] Export `docs/REPORT.md` to PDF with the command in the report and verify it is at most six pages.
- [ ] Record a 3–10 minute walkthrough using `docs/DEMO_SCRIPT.md`; upload it and add the public link.
- [ ] Check every public link, repository access, data-license obligations, and persistent disclaimer.
- [ ] Submit the repository, report PDF, video URL, and live demo URL through the hackathon portal.

Do not submit the internal cross-validation table as external validation or
describe bootstrap-model spread as a clinical confidence interval.
