# BINUSMAYA test console

## Test plans (Bahasa Indonesia)

- [Rencana pengujian jadwal kelas](docs/RENCANA_UJI_JADWAL_KELAS.md)
- [Rencana pengujian materi pembelajaran](docs/RENCANA_UJI_MATERI_PEMBELAJARAN.md)

A local FastAPI dashboard for two Selenium checks against your own Maya account. It does not submit work or change account settings:

- **Class schedule:** enter LMS through the home dashboard launcher (which opens a new tab), click its Schedule menu, and verify the My Schedule heading, calendar, and at least one fully loaded class card (not a loading placeholder).
- **Learning materials:** click a visible class/session card from that schedule, locate the first item immediately below **Video Conference**, and click its main article area (not its Download or Report control). Wait 10 seconds, then capture a screenshot. This step passes only when the click and evidence capture succeed. The configured class is preferred when present; otherwise, the first populated card is used. A different class without that item fails this check.

It displays live step status, durations, counts, sanitized UI-label excerpts, and screenshots for both test steps. It waits for loaded schedule content, pauses two seconds before schedule evidence, and waits 10 seconds after clicking the article before materials evidence. Failed steps wait two seconds before capturing an available page. It does not click attendance, Download, Report, submission, or forum controls.

## Run on Windows (Git Bash)

```bash
cd /c/Code/binus-maya-test-dashboard
uv venv .venv --python 3.11
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -m uvicorn maya_dashboard.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` **yourself**, then click **Start tests**. Selenium opens a dedicated Chrome window using `data/chrome-profile` and **assumes that profile is already logged in**. It does not wait for or automate login: if the LMS launcher is absent, the run fails promptly. The runner clicks that launcher, switches to the new LMS tab, and follows the Schedule menu. A login in your regular Chrome profile is not shared with this dedicated profile. The profile persists between runs; never point it at your regular Chrome profile. Chrome and an available ChromeDriver (normally resolved by Selenium Manager) are required. Close other Chrome windows using this dedicated profile before starting a run.

The preferred course/session is initially set to the supplied Automation Testing lecture, Session 2. If its card is absent from the visible schedule, the runner opens the first fully loaded class card instead. To change the preference, set `MAYA_COURSE_TITLE` to its visible course heading, `MAYA_SECTION` to the card's section, and `MAYA_SESSION` to the card's session label before starting the server. Maya can change its course URL, so the runner trusts the opened Maya course heading rather than requiring the old exact path. `MAYA_COURSE_PATH` is retained for compatibility but is not used to choose or open a card. For example:

```bash
export MAYA_COURSE_TITLE='My course title'
export MAYA_SECTION='LA83 - LEC'
export MAYA_SESSION='Session 2'
```

`MAYA_DATA_DIR` optionally moves the profile and run history. The dashboard binds to localhost only. It does not store your password. Screenshots can contain names, class details, or other private data; keep the `data/` folder private. Each run stays under `data/runs/<run-id>/` until **you** remove it manually. Screenshot capture checks for known schedule/course UI (or a Maya course-session route) and skips pages with password inputs; an unrecognized external material page will fail evidence capture rather than being marked successful. The text excerpt contains only allowlisted UI labels, never full page HTML.

## Verify without opening a browser

```bash
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

The tests exercise selectors, the Selenium click-and-wait flow with a fake WebDriver, concurrency, persistence, API, and evidence access. **They do not establish that the live Maya site currently passes**; run the dashboard yourself to validate the actual authenticated pages. If Maya changes its UI, update the selectors in `maya_dashboard/runner.py` and `maya_dashboard/checks.py`.
