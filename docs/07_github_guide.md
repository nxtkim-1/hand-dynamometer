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

## Creating the repo (one person does this)

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
