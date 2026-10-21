# 07 — GitHub, from zero

You've never used git. This gets you from nothing to a public repo with this project in it, in about an hour, and then tells you the four things you do every week after that.

## What git and GitHub actually are

**Git** is a program that keeps a history of a folder. Every time you "commit", it takes a snapshot of every file and labels it with a message you write. You can go back to any snapshot. Two people can work on the same folder and git merges their changes.

**GitHub** is a website that stores a copy of that folder and its history, so both of you can reach it, and so anyone can see it. Your GitHub profile is where a co-op recruiter will look.

You don't need to learn the command line. **GitHub Desktop** is a free app that does everything you need with buttons.

## One-time setup (both of you)

1. **Make an account** at github.com. Use your real name as the username or something close — `tkim-uw`, not `xX_gamer_Xx`. This is a professional page.
2. **Install GitHub Desktop** from desktop.github.com. Sign in with your account.
3. That's it.

## This repo already has a history (read this first)

The folder you downloaded already contains git history (a hidden `.git` folder). Don't create a new repository on top of it.

1. Unzip it somewhere sensible, e.g. `Documents/hand-dynamometer/`.
2. GitHub Desktop: **File → Add local repository** → choose the folder. It recognises the history.
3. Check the author: **Repository → Repository settings → Git config**. Your name and the email on your GitHub account must be there, or your commits won't link to your profile.
4. Click **Publish repository**, name it `hand-dynamometer`, untick "Keep this code private", Publish.

Dates in the history are the real days the work happened. The history up to 2026-10-16 was written down on 2026-10-17 from the build log and the project folder; where an exact date wasn't recorded, the commit message says so.

### Commit your own firmware steps on the day you do them

`docs/11_firmware_tutorial.md` Part 9 has you write the firmware yourself in four steps. Make each one a commit, the day you actually do it, so the history shows your real progress:

| When you finish | Save as | Commit message |
|---|---|---|
| Step 1, print time | `firmware/my_firmware/my_firmware.ino` | `my firmware step 1: print millis() over serial` |
| Step 2, read the raw sensor | same file | `my firmware step 2: read raw HX711 counts` |
| Step 3, zero it | same file | `my firmware step 3: tare at startup` |
| Step 4, full version (CSV, `t` command) | same file | `my firmware step 4: CSV output and tare command` |

If something breaks and you fix it, that's a commit too (`fix: ...`). Those are the commits worth talking about in an interview.

## Creating the repo (only if you are starting from an empty folder)

1. Put this whole project folder somewhere sensible, e.g. `Documents/hand-dynamometer/`.
2. In GitHub Desktop: **File → Add local repository** → choose that folder. It'll say it isn't a git repository yet and offer to **create a repository** here. Click that.
   - Name: `hand-dynamometer`
   - Description: `3D-printed grip strength meter with load cell, Arduino, and a full calibration report`
   - Leave "initialize with README" unchecked (we already have one)
   - Git ignore: none (we already have `.gitignore`)
   - License: none (we already have `LICENSE`)
3. It shows a list of every file as "changes". In the bottom-left, the summary box: type `Initial commit: CAD, firmware, software, docs`. Click **Commit to main**.
4. Click **Publish repository** (top bar). **Uncheck "Keep this code private."** Click Publish.
5. Go to github.com/yourname/hand-dynamometer. It's live. The README renders as the front page.

## Adding your partner

On the GitHub website: repo → **Settings → Collaborators → Add people** → their username. They accept the invite by email. Then in *their* GitHub Desktop: **File → Clone repository** → pick `hand-dynamometer` → choose where to put it. They now have the same folder and can push to it.

## The weekly workflow (this is all you'll actually do)

**Before you start work:** open GitHub Desktop → click **Fetch origin** → if it says "Pull", click it. This gets your partner's changes.

**After you do something:** GitHub Desktop shows the changed files. Type a one-line summary, click **Commit to main**, then click **Push origin**. Now it's on GitHub and your partner can pull it.

That's four clicks: Fetch, Pull, Commit, Push. Do it every time you finish a session. Don't save up a week of changes.

## Writing commit messages

The message is the label on the snapshot. Write what changed, present tense, under 70 characters:

```
Add fit coupon STL and printing notes
Fix carrier bolt clearance: 5.5 -> 5.7 mm
Calibration run 1-3 data and fit results
log: frame printed, 11h 40m, PETG, no lift
```

Bad: `update`, `stuff`, `final`, `final2`, `asdf`. A recruiter reading your history sees these.

## What to commit and what not to

**Commit:** source files (`.py`, `.ino`), STLs and STEPs, CSV data, docs, images, the build log.

**Don't commit:** Python cache folders (`__pycache__`), slicer G-code (huge and printer-specific), `.DS_Store`, session files you don't need. The `.gitignore` file in the repo already excludes these automatically.

## If you both edit the same file

Sometimes git can't merge automatically — usually the build log, because you both added an entry. GitHub Desktop will show a "conflict". Open the file; you'll see both versions marked with `<<<<<<<` and `>>>>>>>`. Delete the markers, keep both entries, save, commit. Takes two minutes. To avoid it: each person adds their log entries under their own name, and pull before you edit.

## Making the repo look good

These are what people see first:

- **The README renders on the front page.** Keep it current. Replace the render with a real photo once you have one.
- **Add topics** (repo page → gear icon next to About): `biomedical-engineering`, `arduino`, `load-cell`, `3d-printing`, `cadquery`, `instrumentation`.
- **Pin it** to your profile: profile page → Customize your pins.
- **Commits with real messages, spread over eight weeks.** A history that shows steady work is worth more than a single dump on the last day.

## What to put on your resume and LinkedIn

Link the repo. Put the link in the header of your resume next to your email. On LinkedIn, add it under Projects with a two-sentence description and the same link.

## If something goes really wrong

You deleted a file, or broke something, and want to go back: GitHub Desktop → **History** tab → right-click any earlier commit → **Revert changes in commit**. Nothing is ever really lost.

You can also just look at the file on github.com at any past commit and copy it back.
