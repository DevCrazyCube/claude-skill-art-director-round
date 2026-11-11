---
name: art-director-round
description: Before a final render or export of a video, animation or motion piece, have a separate critic agent judge stills of every shot, at full size and at phone width, against a fixed checklist (composition, dead space, the set, props, acting, finish) and return PASS or FAIL with numbered fixes. Use before any final render, when a piece "passes all the checks" but still looks unpolished, and when someone says a video looks cheap, empty, pasted-on or unfinished.
---

# The art-director round

Measurements cannot see design. A film can hit every number for pacing, loudness and motion and still look
unfinished: a head cropped by the frame, a third of the picture empty, a prop that floats, a caption over a face.
Those are found by looking, and the one who made the shot is the worst person to look, because they know what it
was meant to be.

So before a final render, a **separate** critic looks at stills and says PASS or FAIL. Render only on a PASS.

## How to run it

1. **Make the stills.** One per shot at least, and one per second for long shots, each at full size and at
   390 px wide (a phone). The script does both and builds contact sheets:

   ```bash
   python3 scripts/stills.py film.mp4 --out review/            # one still a second
   python3 scripts/stills.py film.mp4 --out review/ --at 0.4,3.1,6.0,8.2   # or the shots' own times
   ```

   For work that is not rendered yet, export the stills from your own tool and use the same folder layout.
2. **Collect the references.** Two or three pieces the owner has approved, as stills, and any reference sheets
   for the style you are aiming at. Without references the critic judges against its own taste; say so in the report.
3. **Start a fresh critic agent.** It has not seen the script, the brief or your notes. Give it
   `critic-brief.md` filled in: where the stills are, where the references are, and the checklist. Tell it to
   read every still at both sizes.
4. **It returns PASS or FAIL** and, on a FAIL, a numbered list of fixes, each naming the shot and time.
5. **Fix every number and run it again with a new critic.** At most three rounds. If round three still fails,
   stop and take the list to the owner instead of rendering.
6. **If you cannot start an agent,** do the round yourself, in writing, shot by shot: open each still, answer
   each checklist line for it, and write the answer down. Reading your own stills without writing is not a round.

The critic judges; it does not fix. The one who fixes does not judge their own fix.

## The checklist

One fail on any line is a FAIL for the piece.

**Composition**
- The subject sits on a third or is deliberately centred; never drifting in between.
- Headroom is consistent from shot to shot. No head, foot or hand is cut by the frame unless the crop is the point.
- Shot sizes are a small, deliberate set (wide, medium, close). No two neighbouring shots are nearly the same size.
- Eyelines point at what matters, and match across a cut.

**Dead space**
- No area larger than about a quarter of the frame is empty without a purpose. Purpose means: room for a caption
  that is actually there, room the character is about to move into, or a deliberate lonely frame.

**The set**
- Where we are reads within half a second.
- There is depth: something in front of, level with, and behind the subject.
- One key light, from one side, the same in every shot of the scene.
- The subject separates from the background in value, not only in colour. Check the still in greyscale.

**Props**
- Things are held by their edges or handles, at a believable scale, and never pass through a hand or a body.
- Everything that stands on something has a contact shadow.
- Text on a prop is fully in frame and readable at phone width, or it is not text the viewer is meant to read.

**Acting**
- Each pose reads as a silhouette. No two characters hold the same pose.
- Expressions are big enough to read at phone width.
- The first frame is an unmistakable pose: someone already doing something.

**Finish**
- Nothing floats, clips through something, or looks pasted on top of the picture.
- Captions never cover a face, a hand or the prop the shot is about.
- Words and key action stay out of the top 12 % and the bottom 20 % of a vertical frame, where an app's own
  interface sits.
- A graphic that cannot be read at phone width is made readable or cut.

## What the critic returns

```text
VERDICT: FAIL (round 1 of 3)

1. Shot 2, 3.1 s — the mug floats 6 px above the table; no contact shadow. Props.
2. Shot 3, 6.0 s — the caption covers the left character's eyes at phone width. Finish.
3. Shots 1 and 2 — both are medium shots a few percent apart; the cut reads as a jump. Composition.

Passed: dead space, the set, acting.
Judged against: 2 approved references (ref/a, ref/b). No style sheets were given.
```

Each fix names a shot, a time, what is wrong in one sentence, and the checklist section. "Feels off" is not a fix.

## Rules

- **The critic is never the maker**, and never an agent that has seen an earlier round.
- **Both sizes, always.** Most fails only show at 390 px: small expressions, small text, a caption on a face.
- **Do not argue with a fix in the next brief.** If you believe a fix is wrong, the owner decides, not a second
  critic that was told what to think.
- **A PASS is not praise.** It means nothing on the list failed. Whether the idea is good is a different question,
  asked much earlier.
- **Report the round to the owner** with the contact sheet, the round count and the final verdict, including the
  fixes that were made.
