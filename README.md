# AI Email Triage

[![CI](https://github.com/Aleksa5000/ai-email-triage/actions/workflows/ci.yml/badge.svg)](https://github.com/Aleksa5000/ai-email-triage/actions/workflows/ci.yml)

**Claude reads your inbox, sorts every email by category and priority, pulls out the key facts, and drafts a reply for you to review. It never sends anything.**

## The problem it solves

A shared support or sales inbox fills up fast. Urgent outages sit between newsletters, an angry customer waits behind a podcast pitch, and a hot sales lead goes cold because nobody saw it for two days. Someone has to read everything just to decide what to read first.

This tool does that first pass automatically. In seconds you get a prioritized table (what is urgent, who is upset, who wants to buy, what is spam) and a ready-to-edit reply draft for each real email, so your team starts the day answering instead of sorting.

## Features

- **Classification**: category (`sales_lead`, `support`, `billing`, `spam`, `other`), priority (`high`/`medium`/`low`) and sentiment.
- **Key-info extraction**: customer name, company, requested action, deadline (empty when the email does not state it, never guessed).
- **Reply drafts** for every non-spam email, saved as `drafts/<id>.txt`.
- **Human in the loop by design**: the tool has no send code at all. Drafts are text files; a person reviews and sends them. An automated reply to the wrong email is far costlier than the minute it takes to read a draft.
- **Inputs**: a folder of `.eml` files, or an IMAP inbox (`--imap`, read-only, unseen mail only, messages are not marked as read).
- **Reliable structured output**: Claude's response is constrained to a schema and validated with pydantic, so the CSV is always clean.
- **`--dry-run`**: keyword-based classifier, no API call, no key needed. Try the whole pipeline in 30 seconds.
- Outputs: `triage.csv` plus a readable console table.

## How it works

1. Load emails (`.eml` via Python's `email` package, or IMAP via `imaplib`).
2. For each email, one call to the Anthropic API (default model `claude-haiku-5-5`, fast and cheap) with a structured-output schema (`Triage` pydantic model).
3. The validated result goes to `triage.csv`, a console table, and `drafts/`.
4. A failure on one email is reported and skipped; the rest of the batch continues.

## Example output

Real output of `python triage.py sample_emails/ --dry-run` (the keyword fallback, included so you can see the format; note it is much cruder than the AI mode, for example it can't extract the requested action):

```
ID                    CATEGORY    PRIORITY  SENTIMENT  SUBJECT
--------------------  ----------  --------  ---------  ----------------------------------------
01_sales_lead         sales_lead  medium    positive   Pricing for 50 seats + demo?
02_support_urgent     support     high      negative   URGENT: dashboard down for our whole tea
03_billing            billing     medium    positive   Charged twice for September invoice
04_spam               spam        low       neutral    You are a WINNER - claim your free gift
05_support_howto      support     medium    neutral    How do I export reports to Excel?
06_other_podcast      other       low       positive   Podcast collaboration idea
07_angry_refund       billing     medium    negative   Still waiting for my refund - third emai
08_sales_integration  sales_lead  medium    positive   Looking for an integration proposal

8 emails triaged -> triage.csv; 7 reply drafts -> drafts/ (nothing was sent)
```

**Illustrative AI-mode result** (not a captured run; shows the kind of output to expect for `07_angry_refund`):

```
category: billing     priority: high     sentiment: negative
customer_name: Luca Moretti   company: Moretti SRL
requested_action: Refund of 480 EUR promised three weeks ago
deadline: October 9
reply_draft: Dear Luca, I am sorry for the delay and for having to chase this a third time.
             I have flagged your 480 EUR refund as urgent and will confirm the payment date
             before October 9. ...
```

## Quickstart

```bash
git clone https://github.com/Aleksa5000/ai-email-triage.git
cd ai-email-triage
python -m pip install -r requirements.txt

# 1. Try it with no API key
python triage.py sample_emails/ --dry-run

# 2. Real AI triage
export ANTHROPIC_API_KEY=your-key      # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key"
python triage.py sample_emails/ -o triage.csv

# 3. Triage unread mail from an IMAP inbox (read-only)
python triage.py --imap
```

Requires Python 3.11+. Copy `.env.example` to `.env` to keep settings in a file.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | AI mode | none | Anthropic API key |
| `CLAUDE_MODEL` | no | `claude-haiku-5-5` | Model used for triage |
| `IMAP_HOST` | `--imap` | none | IMAP server, e.g. `imap.gmail.com` |
| `IMAP_USER` | `--imap` | none | Mailbox login |
| `IMAP_PASSWORD` | `--imap` | none | Password / app password |

CLI: `python triage.py [folder] [--dry-run] [--imap] [-o triage.csv] [--drafts-dir drafts]`

## Running tests

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
```

Tests need no network and no API key (the Claude client is mocked).

## Privacy

In AI mode, the sender, subject and body (first 6000 characters) of each email are sent to the Anthropic API for processing. Nothing else is stored: the only outputs are the local `triage.csv` and `drafts/` files, which are git-ignored. IMAP access is read-only. Use `--dry-run` to keep everything on your machine. Review Anthropic's data-handling terms before processing sensitive mail.

## Tech stack

Python 3.11+, [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) (structured outputs), pydantic, stdlib `email` / `imaplib`, pytest, GitHub Actions.

## Need something similar?

Need a triage, classification or AI-automation workflow tailored to your inbox, CRM or helpdesk? **Contact me on Upwork** (Aleksa Djorovic, Python + AI automation).

## License

MIT
