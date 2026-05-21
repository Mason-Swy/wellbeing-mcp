# wellbeing-mcp

A Model Context Protocol server for personal health tracking and AI-assisted wellbeing analysis.

## Why

In May 2026, I got the flu.

At first I thought it was just a cold — several colleagues in my office were coughing. On May 1st, I went to the pharmacy and self-medicated with some common cold meds. The next afternoon, things got worse instead of better: body aches, fatigue, severe coughing. I asked an AI assistant — it told me to see a doctor immediately. The diagnosis was flu. Five days of prescription medication later, I finally recovered.

That experience taught me something — **I didn't need another health app. I needed an assistant that could continuously track how I was doing, and flag the moments when things were going wrong.**

If I had a tool like this back then, recording symptoms from the first day I started coughing, the AI might have told me on day one: "This symptom combo doesn't look like a common cold. Consider seeing a doctor sooner." I could have saved myself three miserable days.

That's the origin of wellbeing-mcp.

It's designed to do three things:
- **Recorder**: You describe your day in natural language, it structures the data into your health log.
- **Advisor**: Based on historical data, it surfaces anomalies and risk signals.
- **Medical secretary**: When you visit a doctor, it can hand them a clear symptom timeline.

But it **does not diagnose**. Diagnosis is always a doctor's job.

---

A note of honesty: this project is also my learning vehicle for MCP and GitHub. I've noticed that personal health tracking MCP servers are nearly absent on GitHub — if you're thinking about similar problems, let's talk.

## Features

- **Talk, don't type.** Describe your day in natural language — meals, sleep, mood, symptoms, exercise. The AI structures it into your health log.

- **Smart follow-ups.** Only asked when needed: low mood scores get a "what happened?", high ones don't. Ongoing symptoms get linked automatically — "Is this the same back pain from last week?"

- **Weekly insights.** Get a summary every week, with anomaly alerts when something looks off.

- **100% local.** Your data lives in a SQLite file on your machine. No cloud, no account, no upload.

- **Not a doctor.** wellbeing-mcp organizes information and surfaces patterns — it never diagnoses. That's for your doctor, with this data in hand.

## Architecture

```
You (natural language)
        │
        ▼
  openclaw (your AI agent, powered by MiniMax/DeepSeek)
        │  understands, splits, asks follow-ups
        ▼
  wellbeing-mcp ← (this project)
        │  save / query / summarize
        ▼
  SQLite (local file on your machine)
```

**Five tables**: meals, sleeps, moods, symptoms, exercises.
**Eight tools**: 5 save tools, 2 query tools, 1 weekly summary.

The AI does the thinking. wellbeing-mcp does the structured storage and retrieval. SQLite is the source of truth — owned by you, never leaves your machine.

## Installation

Not ready yet — implementation in progress. Star/watch this repo to be notified when v0.1 ships.

## Usage

Coming with v0.1. The intended interaction looks like:

```
You: "Had porridge and two eggs for breakfast, back is still a bit sore."

openclaw: [calls save_meal and save_symptom]
"Logged. The back soreness — is it the same one from Monday?"

You: "Yes."

openclaw: [calls save_symptom with related_id, updates duration_status]
"Got it, marked as ongoing. It's been 4 days now."
```

## License

MIT © 2026 Mason