---
description: Draft a reply for one ticket with the drafter subagent, check it with the reviewer, and save it to drafts/. Never sends anything.
argument-hint: HR-xxxx
---

Draft a reply for ticket `$ARGUMENTS`.

Nothing customer-facing is ever sent. This command saves a local draft in `drafts/` and posts nothing to Slack or Gmail. A human reads, edits and sends.

## Steps

1. Check that `tickets/<ID>.md` exists. If not, stop and say so.
2. If `cases/<ID>.md` does not exist, run the `triage` skill for that ticket first.
3. Call the `drafter` subagent with the ticket ID. Keep its output as `draft_v1`.
4. Call the `reviewer` subagent with the ticket ID and the full draft text.
5. If the verdict is PASS, go to step 7.
6. If the verdict is FAIL, call the `drafter` once more with the ticket ID and the reviewer's issues. Call the `reviewer` again on the new draft. This is the only revision round. Do not loop again.
7. Save the result to `drafts/<ID>.md` with this front matter, then the drafter's text:

   ```
   ---
   id: <ID>
   status: draft, never sent
   customer_reply: <yes or no, from the drafter>
   review: <pass or fail>
   review_rounds: <1 or 2>
   ---
   ```

   If the review still failed after the revision round, keep the draft and add the reviewer's remaining issues under `## Open review issues` at the end of the file.
8. Finish with one line: the ID, whether it is a customer reply or an internal note, the review result, and the file path. If the review failed, say so first.

## Never

- Never send, post or schedule anything. Never use Slack or Gmail tools in this command.
- Never edit files under `policy/`, `cases/` or `tickets/`.
- Never put customer names, emails or addresses in anything except the customer-facing draft text.
