# Build log (raw process notes for next week)

Not a polished write-up. Just the prompts, first output, and what changed.

---

## Moment 1 — First prompt

**Prompt (paraphrased from the assignment, pasted into Cursor):**
Help complete this homework: Streamlit MovieLens dashboard with the 4 required questions, interactive controls, deployable on Streamlit Community Cloud, plus a build log.

**What the AI produced first:**
A full `app.py` with Plotly charts, sidebar year + genre filters, a 50–150 rating-floor slider, dark theme, and this log. `requirements.txt` was originally the assignment text, not packages — that got replaced.

**What I kept / changed:**
- Kept unique-movie counts for Q1 (not rating-weighted). The question asks about *movies that were rated*, not how often each genre was rated.
- Kept exploding pipe-separated genres instead of picking a “primary” genre.
- Did **not** use a pie chart for 19 genre slices (assignment warning).
- Used **release year** (`year`) for Q3, not `rating_year`.

---

## Moment 2 — Genre mean: ratings vs movies

**Prompt / follow-up in my head:**
“Highest average rating” — average of ratings, or average of each movie’s average?

**First instinct from the AI:**
Explode at the *rating* row level, then `mean(rating)` per genre. Popular movies pull the average more.

**What I changed and why:**
Dropped `unknown` (2 movies, 10 ratings) from the genre charts so “lowest average” isn’t a missing-data bucket. First run had unknown at 3.20 as the lowest genre; real lowest among named genres is Fantasy (~3.21).

---

## Moment 3 — Top 5 floor 50 vs 150

**Prompt:**
Show top 5 with ≥50 ratings, and what changes at 150.

**What the AI produced:**
One slider (50–150) plus a side-by-side table so you can see both floors without guessing.

**What I changed / didn’t:**
Tied rankings on mean rating break by number of ratings (more ratings win). No Bayesian shrinkage. Early years with few films stay noisy on the time chart on purpose — I didn’t hide them with a rolling average.
