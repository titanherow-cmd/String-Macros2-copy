Absolutely! Here's the complete updated `string_macros.py` file. Copy and paste this entire thing:Absolutely! Here's the **complete fixed `string_macros.py`** with all three critical sticky-click fixes integrated. You can copy-paste this entire file:

```python
#!/usr/bin/env python3
"""
STRING MACROS - FEATURE LIST
===========================================================================

  Current version: v3.18.80
  File ratio (default 12): 2 Raw - 3 Inef - 7 Normal  (2:3:7)
  Time-sensitive ratio:    6 Raw - 0 Inef - 6 Normal  (1:1)

===========================================================================
                    GROUP 1: PAUSE BREAKS
===========================================================================

1. WITHIN-FILE PAUSES
   Files: Normal + Inef (Raw = 0%)
   Value: random % drawn fresh per file (decimal, never rounded):
     Normal: rng.uniform(2%, 5%)  e.g. 2.14%, 3.87%
     Inef:   rng.uniform(10%, 15%)  e.g. 11.6%, 13.2%
   e.g. 20s Normal file at 3.4% -> 0.68s pause
   One pause per file in middle 80%. Skips drags, rapid-clicks, pre-DragStart.

2. PRE-PLAY BUFFER
   Files: ALL (including between cycles in the outer loop)
   Value: rng.uniform(500, 800) ms * mult — applied before every file and
   between every cycle boundary (end of cycle N -> start of cycle N+1).
   Between-cycle buffer was added in v3.18.45 to prevent 0ms gap between
   the last DragEnd of one cycle and the cursor transition of the next,
   which caused drag-click at wrong position.

2b. PER-VERSION TARGET DURATION VARIANCE
    Each version gets a random target duration of base +/- 5 minutes.
    e.g. --target-minutes 60 produces versions targeting 55-65 min each.
    Drawn as rng.uniform(-300000, +300000) ms float per version.
    The effective target (used by the build loop) uses this per-version value.
    Inef massive pause budget is also pre-sampled against the per-version target.
    Shown in print output: "Target: 62m 14s (base 60m +2.2m)"

3. INEF BEFORE-FILE PAUSE
   Files: Inef only, only if current cycle >= 25s
   Value: rng.uniform(10000, 30000) ms flat (no mult)
   Added between each full cycle (F1->...->FN loop).
   Cursor drifts during this pause toward next file start position.

4. INEFFICIENT MASSIVE PAUSE
   Files: Inef only
   Value: rng.uniform(240000, 420000) ms flat (no mult) = 4-7 min
   One pause inserted at a safe random point after all cycles complete.
   Loop pre-samples pause so total file stays near target duration.
   Safe: no drag, no rapid-click, not pre-DragStart, not first/last 10%.

5. MULTIPLIER SYSTEM
   Continuous random range, 4 decimal places (never rounded):
     Raw:    rng.uniform(1.1, 1.2)  e.g. 1.13, 1.17
     Normal: rng.uniform(1.5, 1.7)  e.g. 1.53, 1.67
     Inef:   rng.uniform(2.0, 3.0)  e.g. 2.14, 2.87
   Multiplied (baked in at generation time):
     - Pre-play buffer: rng.uniform(500, 800) * mult
     - Cursor transition: rng.uniform(200, 400) * mult
     - Within-file % pause: file_duration * pct (pct not multiplied; the pause
       duration grows with larger files naturally)
     - Mid-event random pause (50% chance/cycle): rng.uniform(200, 800) * mult
   NOT multiplied (flat): inef before-file pause, massive pause, distraction files

===========================================================================
                    GROUP 2: PATTERN BREAKING
===========================================================================

6. CURSOR TRANSITION TO START POINT
   Files: ALL (SKIPPED for click-sensitive)
   Value: rng.uniform(200, 400) ms * mult — human path between files.
   Skipped entirely for click-sensitive folders.

7. IDLE CURSOR WANDERING
   Files: ALL (SKIPPED for click-sensitive)
   Fills existing recording gaps > 2000ms with cursor arcs/drifts.
   Does NOT add time — movements fit inside the existing gap.
   Not shown in manifest (zero time impact on total).

8. MOUSE JITTER
   Files: ALL (SKIPPED for click-sensitive)
   Value: 9-21% of mouse moves get +/-1-3px random offsets.
   Excluded near drags, rapid-click sequences, first/last 10% of file.

9. VIRTUAL QUEUE - SUBFOLDER FILES
   Each subfolder has its own shuffled queue. No file repeats until all
   others used. Boundary guard prevents same file at queue wrap.
   Same mechanism applies to distraction files (Feature 32).

===========================================================================
                    GROUP 3: SMOOTH OPERATION
===========================================================================

10. RAPID CLICK PROTECTION
    3+ clicks within 1500ms detected. Jitter exclusion extended to 1500ms.

11. DRAG OPERATION PROTECTION
    Hold+Move+Release detected. No jitter during entire drag sequence.

12. EVENT TIMING INTEGRITY
    No modifications inside drags, pre-DragStart, rapid-clicks, or first/
    last 10%. Prevents click-hold clamping (unintended long drags).

13. COMBINATION HISTORY
    Tracks used file combos per subfolder across cycles.
    Avoids repeating same combination. Persists via uploaded .txt files.

14. MANUAL HISTORY UPLOAD
    Upload COMBINATION_HISTORY_XX.txt to input_macros/combination_history/
    All .txt files read; those combos avoided in future runs.

15. ALPHABETICAL FILE NAMING
    Raw: ^XX_A  Inef: XX_C (not-sign prefix)  Normal: XX_E (no prefix)
    Output folder: (bundle_id) folder_name

16. FOLDER-NUMBER STRUCTURE
    F1, F2, F3.5 etc. F<N> prefix preferred; other numbers in name ignored.
    e.g. "F3- press 1 to bank" -> num=3, the "1" in name is ignored.

17. OPTIONAL TAG
    Default chance: rng.uniform(24%, 33%) per bundle (decimal, never rounded).
    Custom number: used as CENTRE of +/-2% random range (never rounded).
      e.g. "optional23" -> rng.uniform(21%, 25%)
           "optional50" -> rng.uniform(48%, 52%)
           "optional50.5" -> rng.uniform(48.5%, 52.5%)
    This adds variety so the same folder never hits the exact same threshold.
    Range clamped so it never goes below 1% or above 99%.
    Max-files/loops: "optional58-6-" = 58% centre, pick 1-6 files/loops.
    No optional: "F1-4-" = always included, pick 1-4 files.
    always_first/last wraps the entire picked group once (not per file).
    For nested folders: -N- means max N complete sub-cycles (loops), not files.

18. END TAG
    Uses word-boundary match (end) — "tend" does NOT match.
    Loop stops after this folder. Always included if reached.

19. OPTIONAL+END COMBO TAG
    Chosen = loop stops here. Skipped = loop continues.
    Renamed from "optional/end" in v3.18.42.

20. TIME SENSITIVE TAG
    Ratio: 1:1 (half raw, half normal, zero inef).
    Main folder tag propagates to ALL subfolders.

21. CLICK SENSITIVE TAG
    Disables ALL coordinate-changing features:
    cursor path, mouse jitter, idle wandering, distraction insertion.
    Main folder tag propagates to ALL subfolders.
    Accepted: "click sensitive" / "click/time sensitive" / "click+time sensitive"

22. CLICK/TIME SENSITIVE COMBO TAG
    Both tag rules active: 1:1 ratio + no cursor/jitter/idle/distraction.

23. DONT USE FEATURES ON ME TAG
    Exact folder name (case-insensitive). Files inserted completely unmodified.
    Marked [UNMODIFIED] in manifest.

24. ALWAYS FIRST / LAST FILES
    Tag in FILENAME (not folder name). Three modes:
    A) Root-level (next to F1/F2/F3 subfolders): fires ONCE per strung file,
       before all cycles start and after all cycles end.
    B) Inside a specific subfolder (e.g. F0): wraps ONLY that subfolder's files.
       Pattern: [AF] -> F0 files -> [AL] -> F1 -> F2 -> ...
    C) Flat/single-subfolder folder: fires ONCE at very start and very end.
    For nested folders (Feature 39): AF/AL wrap all loops together, not per loop.

25. COMPREHENSIVE MANIFEST
    !_MANIFEST_XX_!.txt in output folder. Shows per-version:
    - File type, multiplier, total pause added
    - Breakdown (x = mult applied, - = flat): PRE-Play Buffer, Within File Pauses,
      CURSOR to Start Point, POST-SNAP GAP, DISTRACTION File Pause,
      INEFFICIENT Before File Pause, INEFFICIENT MASSIVE PAUSE
    - Full file list with cumulative end times

26. SPECIFIC FOLDERS FILTERING
    --specific-folders <file>: process only folders (and optionally subfolders)
    listed in the file. Matching is case-insensitive, whitespace-stripped.

    File format (one entry per line):
      FolderName                   -> include folder, ALL its subfolders
      FolderName: F1, F3, F4       -> include folder, ONLY subfolders F1 F3 F4
      FolderName: F1, F3-F5        -> include folder, F1 and range F3 through F5

    Examples:
      22- Craft Dia- edge- lamp bank Z- S
      22- Craft Dia- edge- lamp bank Z- S: F1, F2, F4
      58- Smth R2H only: F1-F3

    - Subfolder numbers are case-insensitive (F1 = f1 = 1)
    - Decimal subfolders supported: F3.5
    - If a requested subfolder doesn't exist, it is skipped with a warning
    - Output folder: (bundle_id) folder_name

27. CHAT INSERTS
    --no-chat disables. One chat file spliced into one non-raw version
    per folder batch at a random point in the middle third.

28. PRE-PLAY BUFFER GUARANTEE
    files_added int counter (not list truthiness) ensures buffer fires before
    every file including always_first/last. Avoids Python nonlocal edge case.

29. FAIL-FAST ERROR HANDLING
    Fatal errors call sys.exit(1) so GitHub Actions fails at the right step.

30. FLAT FOLDER SUPPORT
    JSON files directly in main folder (no numbered subfolders) = single pool.
    All tags (always_first/last, time_sensitive, click_sensitive) still work.

31. DISTRACTION FILE GENERATION + INSERTION
    Trigger: DISTRACTIONS/ folder in input_macros/
    Generates 50 temp files (30s-2min), each using 3 of 6 features:
    wander, pause, right-click, typing, key-spam, shapes.
    Chance: Normal 3.5-5%, Inef 3.5-7%, Raw 0%, Click-sensitive 0%.
    NOT multiplied — flat pre-built durations. Shown in manifest.

32. VIRTUAL QUEUE - DISTRACTION FILES
    All 50 distraction files rotate before any repeat.
    Boundary guard prevents consecutive repeat at queue wrap.

33. 2:3:7 FILE RATIO DISTRIBUTION
    raw=round(v x 2/12), inef=round(v x 3/12), normal=remainder.
    12->2:3:7, 24->4:6:14, 20->3:5:12.
    Time-sensitive override: 1:1 raw:normal, zero inef.

34. FILE TRANSITION START GAP PROTECTION
    80-150ms gap (POST-SNAP GAP) between snap MouseMove and first event of
    next file. Prevents zero-gap DragStart = cursor clamp at transition.
    Tracked in manifest as flat (no mult).

35. INTRA-FILE ZERO-GAP PROTECTION
    On load: two checks, both shift all events from the click forward.
    Part A — MouseMove->DragStart/Click gap < 15ms shifted to 20ms.
    Prevents recording-tool artifacts causing button clamp.
    Part B — DragEnd->DragStart gap < 150ms shifted to 200ms.
    Prevents too-fast re-press sequences where the macro player cannot
    distinguish a genuine release+re-click from a single held drag.
    Applied before any other features, to raw events only.

36. ORIGINAL FILES DEDUPLICATION
    Counts each unique filename once across all subfolders.
    Copied subfolders shown as "(N copied folder(s))" in manifest.

37. MAX-FILES TAG
    "-N-" in folder name = pick 1-N files (or loops for nested folders).
    "F3 optional58-6-" = 58% chance, 1-6 files.
    "F1-4-" = always included, 1-4 files.

38. PROBLEMATIC KEY FILTERING
    On load (before any features): strips keys that break macro playback.
    Filtered: HOME(36), END(35), PAGE_UP(33), PAGE_DOWN(34), PAUSE(19),
              PRINT_SCREEN(44)
    Kept: ESC(27) — valid in-game action (closing menus, cancelling dialogs).
    IMPORTANT: base_time captured BEFORE filtering so files whose only early
    event is a filtered key (e.g. END at t=90ms) keep their full duration.
    Without this, the 90ms anchor is lost and the file collapses to near-zero.

39. NESTED SUBFOLDER SUPPORT
    A numbered subfolder (e.g. F5) can contain its own F1/F2/F3/F4 instead
    of direct JSON files. Detected automatically during scanning.
    -N- on the outer folder = max N complete inner loops (not N files).
    always_first/last at F5's root level fire ONCE before all loops and
    ONCE after all loops (not per loop).
    Internal subfolders support all tags: optional, end, time/click sensitive.
    Separate ManualHistoryTracker maintained for nested folder's combos.

40. LOGOUT SEQUENCE FOLDER (Feature 40)
    Trigger: folder named 'LOGOUT, wait, in' (case-insensitive) at the root
    level of input_macros/.
    Contents: exactly 3 .json files identified by keyword in filename:
      - File containing 'proper'  → slot 1: actual logout actions
      - File containing 'nothing' → slot 2: idle wait period
      - File containing 'relogin' → slot 3: re-login actions
    Stringing order: slot1 → 500-800ms buffer → slot2 → RANDOM WAIT →
                     500-800ms buffer → slot3
    Random wait: rng.uniform(60000, 10800000) ms (1 minute to 3 hours).
                 Float value, never rounded — full millisecond precision.
    Features: NO anti-detection features applied (files inserted raw).
              filter_problematic_keys() is applied on load.
    Output: written to output_root/- logout.json, then copied to each
            bundle folder as "@ N LOGOUT.JSON" (same as static logout file).
    Priority: takes precedence over the legacy '- logout.json' static file.
    Fallback: if the folder is missing, the old static file search still runs.
    The folder is excluded from the main macro scan (not treated as a macro folder).
    Dedicated rng seeded from bundle_id + 31337 — does not affect main rng state.

===========================================================================

CHANGELOG (recent):
- v3.18.80: CRITICAL FIX — Sticky left-click bug eliminating false drag clamps.
            ROOT CAUSE: Three interconnected timing issues:
            1. LeftUp events in fix_click_events() used random timing (10-20ms),
               causing collisions with next-event timestamps.
            2. After sorting events by Time, identical timestamps could result
               in unstable order: LeftUp and MouseMove sharing t=1000 could
               be reordered, making game read "moved while held" → drag clamp.
            3. POST-SNAP-GAP was truncated to int(), losing float precision.
            FIXES:
            1. LeftUp now uses deterministic 15ms (imperceptible but safe).
            2. New enforce_monotonic_timestamps() scans after sort and ensures
               no two events share identical Time values (shifts colliders +1ms).
            3. post_snap_gap now uses float: rng.uniform(80.0, 150.0).
            IMPACT: Clicks maintain their integrity from source JSON files;
            no more random left-button clamps on strung output.
            TEST: Verify LeftUp is always exactly 15ms after LeftDown in output;
            verify no two events have identical Time after enforce_monotonic_timestamps().
- v3.18.79: Extended intra-file zero-gap fix (Feature 25) with Part B:
            DragEnd -> DragStart pairs with a gap under 150ms are now shifted
            to enforce a 200ms minimum separation.
- v3.18.78: Fixed click-sensitive flag silently falling through as False.
- v3.18.77: Two bug fixes in inter-cycle transition block and logout wait time.
- v3.18.76: New Feature 40 — LOGOUT sequence folder.
- v3.18.75: Fixed two inter-cycle cursor transition bugs causing teleports.
===========================================================================
"""

import argparse, json, random, re, sys, os, math, shutil, itertools
from pathlib import Path

VERSION = "v3.18.80"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_ms_precise(ms):
    """Format milliseconds as Xm Ys"""
    total_sec = int(ms / 1000)
    minutes = total_sec // 60
    seconds = total_sec % 60
    return f"{minutes}m {seconds}s"

def get_file_duration_ms(filepath):
    """Get file duration in milliseconds"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            events = json.load(f)
        if not events:
            return 0
        times = [e.get('Time', 0) for e in events]
        return max(times) - min(times)
    except:
        return 0

def filter_problematic_keys(events: list) -> list:
    """
    CRITICAL: Filter out keys that could stop macro playback.
    Removes: HOME(36), END(35), PAGE_UP(33), PAGE_DOWN(34), PAUSE(19), PRINT_SCREEN(44)
    NOTE: ESC(27) kept - it is a valid in-game key (e.g. closing menus).
    """
    problematic_codes = {19, 33, 34, 35, 36, 44}
    filtered = []
    
    for event in events:
        keycode = event.get('KeyCode')
        if keycode in problematic_codes:
            continue
        filtered.append(event)
    
    return filtered

def parse_optional_chance(folder_name: str) -> float:
    """
    Parse the inclusion probability from an 'optional'-tagged folder name.
    """
    import re
    match = re.search(r'optional[^-\d]*?(\d+(?:\.\d+)?)', folder_name, re.IGNORECASE)
    if match:
        centre = float(match.group(1))
        lo = max(1.0, centre - 2.0)
        hi = min(99.0, centre + 2.0)
        return random.uniform(lo, hi) / 100.0
    return random.uniform(0.24, 0.33)


def parse_max_files(folder_name: str) -> int:
    """
    Parse max-files count from folder name.
    """
    import re
    name = folder_name.strip('/').strip()
    name = re.sub(r'^[Ff]?\d+(?:\.\d+)?\s*', '', name)
    name = re.sub(r'optional\s*\d+(?:\.\d+)?', 'optional', name, flags=re.IGNORECASE)
    matches = re.findall(r'-(\d+)-', name)
    if matches:
        try:
            return max(1, int(matches[-1]))
        except ValueError:
            pass
    return 1


def enforce_monotonic_timestamps(events: list) -> list:
    """
    ============================================================================
    FIX #2: MONOTONIC TIMESTAMP ENFORCEMENT (v3.18.80)
    ============================================================================
    Ensure no two events share the same timestamp.
    
    PROBLEM: After sorting events by Time, identical timestamps could exist.
    If LeftUp and MouseMove both have Time=1000, the sort order is undefined.
    The game reads "simultaneous move+still-held-button" as a drag.
    
    SOLUTION: Scan after sort; if event[i]['Time'] <= event[i-1]['Time'],
    shift event[i] forward by 1ms. Repeat until all are strictly increasing.
    """
    if not events:
        return events
    
    for i in range(1, len(events)):
        if events[i]['Time'] <= events[i - 1]['Time']:
            events[i]['Time'] = events[i - 1]['Time'] + 1
    
    return events


def fix_click_events(events: list) -> list:
    """
    ============================================================================
    FIX #1: DETERMINISTIC LEFTUP TIMING (v3.18.80)
    ============================================================================
    Convert 'Click' events to LeftDown+LeftUp pairs.
    This prevents the mouse from clamping down and dragging.
    
    PROBLEM: LeftUp was created with random timing (10-20ms).
    This caused collisions where LeftUp could happen at the same timestamp
    as the next MouseMove or DragStart.
    
    SOLUTION: LeftUp now uses deterministic 15ms.
    - 15ms is imperceptible to human players (~150ms+ typical reaction time)
    - Fixed separation prevents timestamp collisions
    - Predictable, reproducible behavior across all strung files
    """
    fixed = []
    for event in events:
        if event.get('Type') == 'Click':
            time = event.get('Time', 0)
            x = event.get('X')
            y = event.get('Y')
            
            left_down = {
                'Type': 'LeftDown',
                'Time': time,
            }
            if x is not None:
                left_down['X'] = x
            if y is not None:
                left_down['Y'] = y
            
            # ============================================================
            # FIX #1: Changed from random.randint(10, 20) to fixed 15ms
            # ============================================================
            left_up = {
                'Type': 'LeftUp',
                'Time': time + 15,  # DETERMINISTIC, NOT random
            }
            if x is not None:
                left_up['X'] = x
            if y is not None:
                left_up['Y'] = y
            
            fixed.append(left_down)
            fixed.append(left_up)
        else:
            fixed.append(event)
    
    return fixed

def generate_human_path(start_x, start_y, end_x, end_y, duration_ms, rng):
    """
    Generate a human-like mouse path with variable speed, path styles, and wobbles.
    """
    if duration_ms < 100:
        return [(0, end_x, end_y)]
    
    path = []
    dx = end_x - start_x
    dy = end_y - start_y
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance < 5:
        return [(0, end_x, end_y)]
    
    path_style = rng.choice(['efficient', 'meandering', 'hesitant', 'swift'])
    
    if path_style == 'efficient':
        num_steps = max(3, min(int(distance / 20), int(duration_ms / 60)))
    elif path_style == 'swift':
        num_steps = max(2, min(int(distance / 25), int(duration_ms / 80)))
    elif path_style == 'meandering':
        num_steps = max(5, min(int(distance / 10), int(duration_ms / 40)))
    else:
        num_steps = max(4, min(int(distance / 15), int(duration_ms / 50)))
    
    if path_style == 'efficient':
        num_control = rng.choice([0, 1])
        offset_range = 0.15
    elif path_style == 'swift':
        num_control = 0
        offset_range = 0.0
    elif path_style == 'meandering':
        num_control = rng.randint(2, 4)
        offset_range = 0.4
    else:
        num_control = rng.randint(1, 2)
        offset_range = 0.25
    
    control_points = []
    for _ in range(num_control):
        offset = rng.uniform(-offset_range, offset_range) * distance
        t = rng.uniform(0.2, 0.8)
        ctrl_x = start_x + dx * t + (-dy / (distance + 1)) * offset
        ctrl_y = start_y + dy * t + (dx / (distance + 1)) * offset
        control_points.append((ctrl_x, ctrl_y, t))
    
    control_points.sort(key=lambda p: p[2])
    current_time = 0
    
    for step in range(num_steps + 1):
        t_raw = step / num_steps
        
        if path_style == 'efficient':
            t = 1 - (1 - t_raw) ** 1.8
        elif path_style == 'swift':
            t = t_raw
        elif path_style == 'meandering':
            t = 0.5 * (1 - math.cos(t_raw * math.pi))
        else:
            t = 0.5 * (1 - math.cos(t_raw * math.pi))
        
        if not control_points:
            x = start_x + dx * t
            y = start_y + dy * t
        else:
            x, y = start_x, start_y
            for i, (ctrl_x, ctrl_y, ctrl_t) in enumerate(control_points):
                if t <= ctrl_t:
                    segment_t = t / ctrl_t if ctrl_t > 0 else 0
                    x = start_x + (ctrl_x - start_x) * segment_t
                    y = start_y + (ctrl_y - start_y) * segment_t
                    break
                else:
                    if i == len(control_points) - 1:
                        segment_t = (t - ctrl_t) / (1 - ctrl_t) if (1 - ctrl_t) > 0 else 0
                        x = ctrl_x + (end_x - ctrl_x) * segment_t
                        y = ctrl_y + (end_y - ctrl_y) * segment_t
                    else:
                        start_x, start_y = ctrl_x, ctrl_y
        
        if path_style == 'swift':
            wobble = rng.uniform(0, 2) if step > 0 and step < num_steps else 0
        elif path_style == 'meandering':
            wobble = rng.uniform(1, 7) if step > 0 and step < num_steps else 0
        else:
            wobble = rng.uniform(1, 5) if step > 0 and step < num_steps else 0
        
        x += rng.uniform(-wobble, wobble)
        y += rng.uniform(-wobble, wobble)
        
        x = max(100, min(1800, int(x)))
        y = max(100, min(1000, int(y)))
        
        step_time = int(t * duration_ms)
        current_time = max(current_time, step_time)
        path.append((current_time, x, y))
    
    return path

# ============================================================================
# COMBINATION TRACKER
# ============================================================================


def is_in_drag_sequence(events, index, drag_indices=None):
    """
    Check if the given index is inside a drag sequence (between DragStart and DragEnd).
    """
    if drag_indices is not None:
        return index in drag_indices

    drag_started = False
    for j in range(index, -1, -1):
        event_type = events[j].get("Type", "")
        if event_type == "DragEnd":
            return False
        elif event_type == "DragStart":
            drag_started = True
            break
    
    if not drag_started:
        return False
    
    for j in range(index + 1, len(events)):
        event_type = events[j].get("Type", "")
        if event_type == "DragEnd":
            return True
        elif event_type == "DragStart":
            return False
    
    return False


def build_drag_index_set(events) -> set:
    """
    Return the set of all event indices that are inside a drag sequence.
    O(n) single pass.
    """
    drag_indices = set()
    in_drag = False
    for i, e in enumerate(events):
        t = e.get("Type", "")
        if t == "DragStart":
            in_drag = True
        elif t == "DragEnd":
            in_drag = False
        if in_drag:
            drag_indices.add(i)
    return drag_indices

def detect_rapid_click_sequences(events):
    """
    Detect sequences of rapid clicks at similar coordinates.
    """
    if not events or len(events) < 2:
        return []
    
    protected_ranges = []
    
    i = 0
    while i < len(events):
        event = events[i]
        
        event_type = event.get("Type")
        if event_type not in ("Click", "DragStart"):
            i += 1
            continue
        
        click_sequence = [i]
        first_time = event.get("Time", 0)
        first_x = event.get("X")
        first_y = event.get("Y")
        
        if first_x is None or first_y is None:
            i += 1
            continue
        
        j = i + 1
        while j < len(events):
            next_event = events[j]
            next_time = next_event.get("Time", 0)
            
            if next_time - first_time > 2000:
                break
            
            next_type = next_event.get("Type")
            if next_type in ("Click", "DragStart"):
                next_x = next_event.get("X")
                next_y = next_event.get("Y")
                
                if next_x is not None and next_y is not None:
                    dist = ((next_x - first_x) ** 2 + (next_y - first_y) ** 2) ** 0.5
                    
                    if dist <= 10:
                        click_sequence.append(j)
            
            j += 1
        
        if len(click_sequence) >= 2:
            start_idx = click_sequence[0]
            end_idx = click_sequence[-1]
            protected_ranges.append((start_idx, end_idx))
            i = end_idx + 1
        else:
            i += 1
    
    return protected_ranges


def is_in_protected_range(index, protected_ranges):
    """Check if an index is within any protected range."""
    for start, end in protected_ranges:
        if start <= index <= end:
            return True
    return False


def add_pre_click_jitter(events: list, rng: random.Random) -> tuple:
    """
    SMART JITTER SYSTEM v3.9.0
    Add realistic micro-movements to 9-21% of TOTAL file movements.
    """
    if not events or len(events) < 2:
        return events, 0, 0, 0.0
    
    click_types = {'Click', 'LeftDown', 'RightDown', 'DragStart'}
    click_times_sorted = sorted(
        event.get('Time', 0) for event in events if event.get('Type') in click_types
    )

    import bisect
    exclusion_ms = 1000

    safe_movements = []
    total_moves = 0

    for i, event in enumerate(events):
        if event.get('Type') == 'MouseMove':
            total_moves += 1
            event_time = event.get('Time', 0)

            pos = bisect.bisect_left(click_times_sorted, event_time)
            is_safe = True
            if pos > 0 and event_time - click_times_sorted[pos - 1] <= exclusion_ms:
                is_safe = False
            if is_safe and pos < len(click_times_sorted) and click_times_sorted[pos] - event_time <= exclusion_ms:
                is_safe = False

            if is_safe:
                safe_movements.append((i, event))
    
    jitter_percentage = rng.uniform(0.09, 0.21)
    target_jitters = int(total_moves * jitter_percentage)
    target_jitters = min(target_jitters, len(safe_movements))
    
    if target_jitters == 0:
        return events, 0, total_moves, jitter_percentage
    
    movements_to_jitter = rng.sample(safe_movements, target_jitters)
    movements_to_jitter.sort(key=lambda x: x[0], reverse=True)
    
    jitter_count = 0
    
    for idx, event in movements_to_jitter:
        move_x = event.get('X')
        move_y = event.get('Y')
        move_time = event.get('Time')
        
        if move_x is None or move_y is None or move_time is None:
            continue
        
        num_jitters = rng.randint(2, 3)
        jitter_events = []
        
        time_budget = rng.randint(100, 200)
        time_per_jitter = time_budget // (num_jitters + 1)
        
        if move_time - time_budget < 0:
            time_budget = max(0, int(move_time) - 1)
        if time_budget == 0:
            continue
        current_time = move_time - time_budget
        
        for j in range(num_jitters):
            offset_x = rng.randint(-3, 3)
            offset_y = rng.randint(-3, 3)
            
            jitter_x = int(move_x) + offset_x
            jitter_y = int(move_y) + offset_y
            
            jitter_x = max(100, min(1800, jitter_x))
            jitter_y = max(100, min(1000, jitter_y))
            
            jitter_events.append({
                'Type': 'MouseMove',
                'Time': current_time,
                'X': jitter_x,
                'Y': jitter_y
            })
            
            current_time += time_per_jitter
        
        jitter_events.append({
            'Type': 'MouseMove',
            'Time': current_time,
            'X': int(move_x),
            'Y': int(move_y)
        })
        
        for jitter_idx, jitter_event in enumerate(jitter_events):
            events.insert(idx + jitter_idx, jitter_event)
        
        jitter_count += 1
    
    return events, jitter_count, total_moves, jitter_percentage

def insert_intra_file_pauses(events: list, rng: random.Random,
                              protected_ranges: list = None,
                              file_type: str = 'normal') -> tuple:
    """
    Insert a single within-file pause.
    """
    if not events or len(events) < 5:
        return events, 0

    if file_type == 'raw':
        return events, 0
    elif file_type == 'inef':
        pct = rng.uniform(0.10, 0.15)
    else:
        pct = rng.uniform(0.02, 0.05)

    if protected_ranges is None:
        protected_ranges = []

    file_duration_ms = events[-1].get('Time', 0) - events[0].get('Time', 0)
    if file_duration_ms <= 0:
        return events, 0

    pause_duration = file_duration_ms * pct

    protected_set = set()
    for s, e in protected_ranges:
        for k in range(s, e + 1):
            protected_set.add(k)

    drag_indices = build_drag_index_set(events)

    first_safe = max(1, int(len(events) * 0.10))
    last_safe  = min(len(events) - 1, int(len(events) * 0.90))
    valid = [
        idx for idx in range(first_safe, last_safe)
        if idx not in protected_set
        and idx not in drag_indices
        and events[idx].get('Type') != 'DragStart'
        and (idx + 1 >= len(events) or events[idx + 1].get('Type') != 'DragStart')
    ]

    if not valid:
        return events, 0

    pause_idx = rng.choice(valid)
    for j in range(pause_idx, len(events)):
        events[j]['Time'] = events[j].get('Time', 0) + pause_duration

    return events, pause_duration
def insert_idle_mouse_movements(events, rng, movement_percentage):
    """
    Insert realistic human-like mouse movements during idle periods.
    """
    if not events or len(events) < 2:
        return events, 0

    drag_indices = build_drag_index_set(events)

    click_proximity = set()
    click_window = 3000
    click_types = {"Click", "LeftDown", "LeftUp", "RightDown", "RightUp"}
    for i, e in enumerate(events):
        if e.get("Type") in click_types:
            t_click = e.get("Time", 0)
            for j in range(i - 1, -1, -1):
                if events[j].get("Time", 0) < t_click - click_window:
                    break
                click_proximity.add(j)

    result = []
    total_idle_time = 0

    for i in range(len(events)):
        result.append(events[i])

        if i < len(events) - 1:
            current_time = int(events[i].get("Time", 0))
            next_time    = int(events[i + 1].get("Time", 0))
            gap = next_time - current_time

            if gap >= 2000:
                if i in drag_indices:
                    continue
                if i in click_proximity:
                    continue
                
                active_duration = int(gap * movement_percentage)
                buffer_start = (gap - active_duration) // 2
                movement_start = current_time + buffer_start
                
                start_x, start_y = 500, 500
                for j in range(i, -1, -1):
                    x_val = events[j].get("X")
                    y_val = events[j].get("Y")
                    if x_val is not None and y_val is not None:
                        start_x = int(x_val)
                        start_y = int(y_val)
                        break
                
                next_x, next_y = start_x, start_y
                for j in range(i + 1, min(i + 20, len(events))):
                    x_val = events[j].get("X")
                    y_val = events[j].get("Y")
                    if x_val is not None and y_val is not None:
                        next_x = int(x_val)
                        next_y = int(y_val)
                        break
                
                transition_duration = int(active_duration * 0.25)
                pattern_duration = active_duration - transition_duration
                
                behavior = rng.choice([
                    'wander', 'check_edge', 'fidget', 'explore', 'drift', 'scan'
                ])
                
                pattern_end_x, pattern_end_y = start_x, start_y
                pattern_time_used = 0
                
                if behavior == 'wander':
                    num_moves = rng.randint(3, 6)
                    move_duration = pattern_duration // num_moves
                    current_x, current_y = start_x, start_y
                    
                    for move_idx in range(num_moves):
                        target_x = current_x + rng.randint(-150, 150)
                        target_y = current_y + rng.randint(-100, 100)
                        target_x = max(100, min(1800, target_x))
                        target_y = max(100, min(1000, target_y))
                        
                        path = generate_human_path(current_x, current_y, target_x, target_y, move_duration, rng)
                        
                        for path_time, px, py in path:
                            abs_time = movement_start + pattern_time_used + path_time
                            result.append({
                                "Time": abs_time,
                                "Type": "MouseMove",
                                "X": px,
                                "Y": py
                            })
                        
                        current_x, current_y = path[-1][1], path[-1][2]
                        pattern_time_used += move_duration
                    
                    pattern_end_x, pattern_end_y = current_x, current_y
                
                elif behavior == 'check_edge':
                    edges = [
                        (150, start_y), (1750, start_y),
                        (start_x, 150), (start_x, 950),
                    ]
                    edge_x, edge_y = rng.choice(edges)
                    edge_duration = int(pattern_duration * 0.6)
                    path_to_edge = generate_human_path(start_x, start_y, edge_x, edge_y, edge_duration, rng)
                    
                    for path_time, px, py in path_to_edge:
                        abs_time = movement_start + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    return_duration = pattern_duration - edge_duration
                    return_x = start_x + rng.randint(-40, 40)
                    return_y = start_y + rng.randint(-40, 40)
                    return_x = max(100, min(1800, return_x))
                    return_y = max(100, min(1000, return_y))
                    
                    path_return = generate_human_path(edge_x, edge_y, return_x, return_y, return_duration, rng)
                    
                    for path_time, px, py in path_return:
                        abs_time = movement_start + edge_duration + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    pattern_end_x, pattern_end_y = path_return[-1][1], path_return[-1][2]
                    pattern_time_used = pattern_duration
                
                elif behavior == 'fidget':
                    num_fidgets = rng.randint(5, 10)
                    fidget_duration = pattern_duration // num_fidgets
                    current_x, current_y = start_x, start_y
                    
                    for fidget_idx in range(num_fidgets):
                        target_x = current_x + rng.randint(-30, 30)
                        target_y = current_y + rng.randint(-30, 30)
                        target_x = max(100, min(1800, target_x))
                        target_y = max(100, min(1000, target_y))
                        
                        path = generate_human_path(current_x, current_y, target_x, target_y, fidget_duration, rng)
                        
                        for path_time, px, py in path:
                            abs_time = movement_start + pattern_time_used + path_time
                            result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                        
                        current_x, current_y = path[-1][1], path[-1][2]
                        pattern_time_used += fidget_duration
                    
                    pattern_end_x, pattern_end_y = current_x, current_y
                
                elif behavior == 'explore':
                    away_x = start_x + rng.randint(-400, 400)
                    away_y = start_y + rng.randint(-300, 300)
                    away_x = max(100, min(1800, away_x))
                    away_y = max(100, min(1000, away_y))
                    
                    away_duration = int(pattern_duration * 0.65)
                    path_away = generate_human_path(start_x, start_y, away_x, away_y, away_duration, rng)
                    
                    for path_time, px, py in path_away:
                        abs_time = movement_start + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    return_duration = pattern_duration - away_duration
                    return_x = start_x + rng.randint(-15, 15)
                    return_y = start_y + rng.randint(-15, 15)
                    return_x = max(100, min(1800, return_x))
                    return_y = max(100, min(1000, return_y))
                    
                    path_return = generate_human_path(away_x, away_y, return_x, return_y, return_duration, rng)
                    
                    for path_time, px, py in path_return:
                        abs_time = movement_start + away_duration + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    pattern_end_x, pattern_end_y = path_return[-1][1], path_return[-1][2]
                    pattern_time_used = pattern_duration
                
                elif behavior == 'drift':
                    target_x = start_x + rng.randint(-200, 200)
                    target_y = start_y + rng.randint(-150, 150)
                    target_x = max(100, min(1800, target_x))
                    target_y = max(100, min(1000, target_y))
                    
                    path = generate_human_path(start_x, start_y, target_x, target_y, pattern_duration, rng)
                    
                    for path_time, px, py in path:
                        abs_time = movement_start + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    pattern_end_x, pattern_end_y = path[-1][1], path[-1][2]
                    pattern_time_used = pattern_duration
                
                elif behavior == 'scan':
                    scan_distance = rng.randint(300, 600)
                    direction = rng.choice(['horizontal', 'vertical', 'diagonal'])
                    
                    if direction == 'horizontal':
                        target_x = start_x + (scan_distance if rng.random() < 0.5 else -scan_distance)
                        target_y = start_y + rng.randint(-50, 50)
                    elif direction == 'vertical':
                        target_x = start_x + rng.randint(-50, 50)
                        target_y = start_y + (scan_distance if rng.random() < 0.5 else -scan_distance)
                    else:
                        target_x = start_x + (scan_distance if rng.random() < 0.5 else -scan_distance)
                        target_y = start_y + (scan_distance if rng.random() < 0.5 else -scan_distance)
                    
                    target_x = max(100, min(1800, target_x))
                    target_y = max(100, min(1000, target_y))
                    
                    path = generate_human_path(start_x, start_y, target_x, target_y, pattern_duration, rng)
                    
                    for path_time, px, py in path:
                        abs_time = movement_start + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    pattern_end_x, pattern_end_y = path[-1][1], path[-1][2]
                    pattern_time_used = pattern_duration
                
                transition_path = generate_human_path(
                    pattern_end_x, pattern_end_y,
                    next_x, next_y,
                    transition_duration,
                    rng
                )
                
                for path_time, px, py in transition_path:
                    abs_time = movement_start + pattern_duration + path_time
                    result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                
                total_idle_time += active_duration
    
    return result, total_idle_time

class QueueFileSelector:
    def __init__(self, rng, all_files, durations_cache):
        self.rng = rng
        self.durations = durations_cache
        self.efficient = [f for f in all_files if "??" not in f.name]
        self.inefficient = [f for f in all_files if "??" in f.name]
        self.eff_pool = list(self.efficient)
        self.ineff_pool = list(self.inefficient)
        self.rng.shuffle(self.eff_pool)
        self.rng.shuffle(self.ineff_pool)

    def get_sequence(self, target_minutes, force_inef=False, is_time_sensitive=False):
        seq, cur_ms = [], 0.0
        target_ms = target_minutes * 60000
        margin = int(target_ms * 0.05)
        target_min = target_ms - margin
        target_max = target_ms + margin
        actual_force = force_inef if not is_time_sensitive else False
        
        while cur_ms < target_max:
            if actual_force and self.ineff_pool: pick = self.ineff_pool.pop(0)
            elif self.eff_pool: pick = self.eff_pool.pop(0)
            elif self.efficient:
                self.eff_pool = list(self.efficient); self.rng.shuffle(self.eff_pool)
                pick = self.eff_pool.pop(0)
            elif self.ineff_pool and not is_time_sensitive: pick = self.ineff_pool.pop(0)
            else: break
            
            file_duration = self.durations.get(pick, 500)
            
            if is_time_sensitive:
                estimated_time = file_duration * 1.05
            else:
                estimated_time = file_duration * 1.35
            
            potential_total = cur_ms + estimated_time
            overshoot = potential_total - target_ms
            
            if overshoot > margin:
                if cur_ms >= (target_ms - (4 * 60000)):
                    break
                else:
                    seq.append(pick)
                    cur_ms += estimated_time
            else:
                seq.append(pick)
                cur_ms += estimated_time
            
            if len(seq) > 800: break
            if cur_ms > target_ms * 3: break
        
        return seq


def insert_massive_pause(events: list, rng: random.Random, mult: float = 1.0) -> tuple:
    """
    Insert one massive pause (4-7 min flat, no multiplier).
    For INEFFICIENT files only.
    """
    if not events or len(events) < 10:
        return events, 0, 0
    
    pause_duration = int(rng.uniform(240000.0, 420000.0))
    
    protected_ranges = detect_rapid_click_sequences(events)
    drag_indices = build_drag_index_set(events)

    safe_indices = []
    first_safe = int(len(events) * 0.1)
    last_safe = int(len(events) * 0.9)
    
    for i in range(first_safe, last_safe):
        if i in drag_indices:
            continue
        if is_in_protected_range(i, protected_ranges):
            continue
        if i + 1 < len(events) and events[i + 1].get("Type") == "DragStart":
            continue
        if i + 1 < len(events) and (i + 1) in drag_indices:
            continue
        safe_indices.append(i)
    
    if not safe_indices:
        return events, 0, 0
    
    split_index = rng.choice(safe_indices)
    
    for i in range(split_index + 1, len(events)):
        events[i]["Time"] += pause_duration
    
    return events, pause_duration, split_index

# ============================================================================
# STRING PARTS WITH ANTI-DETECTION
# ============================================================================

def _pick_af_al(pool, rng):
    """Pick one always_first/last file randomly from a list/pool."""
    if not pool:
        return None
    if not isinstance(pool, list):
        return pool
    return rng.choice(pool)

def string_cycle(subfolder_files, combination, rng, dmwm_file_set=set(),
                 distraction_files=None, distraction_chance=0.0,
                 is_click_sensitive=False,
                 play_always_first=True, play_always_last=True,
                 mult=1.0):
    """
    String one complete cycle (F1 -> F2 -> F3 -> ...) into a single unit.
    Returns raw events WITHOUT anti-detection features.
    """
    
    def add_file_to_cycle(file_path, folder_num, is_dmwm, file_label):
        """Helper to add a file to the cycle"""
        nonlocal timeline, cycle_events, file_info_list, has_dmwm, total_pre_pause, total_transition_time, total_snap_gap_time, files_added
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                events = json.load(f)
        except Exception:
            return
        
        if not events:
            return
        
        base_time_pre_filter = min(e.get('Time', 0) for e in events)

        events = filter_problematic_keys(events)
        if not events:
            return

        _CLICK_TYPES = {'DragStart', 'LeftDown', 'RightDown', 'Click'}

        _ZERO_GAP_THRESHOLD = 15
        _ZERO_GAP_TARGET    = 20
        for _zi in range(1, len(events)):
            if (events[_zi].get('Type') in _CLICK_TYPES
                    and events[_zi - 1].get('Type') == 'MouseMove'):
                _gap = events[_zi].get('Time', 0) - events[_zi - 1].get('Time', 0)
                if 0 <= _gap < _ZERO_GAP_THRESHOLD:
                    _shift = _ZERO_GAP_TARGET - _gap
                    for _j in range(_zi, len(events)):
                        events[_j]['Time'] = events[_j].get('Time', 0) + _shift

        _DRAG_REPRESS_THRESHOLD = 150
        _DRAG_REPRESS_TARGET    = 200
        for _zi in range(1, len(events)):
            if (events[_zi].get('Type') == 'DragStart'
                    and events[_zi - 1].get('Type') == 'DragEnd'):
                _gap = events[_zi].get('Time', 0) - events[_zi - 1].get('Time', 0)
                if 0 <= _gap < _DRAG_REPRESS_THRESHOLD:
                    _shift = _DRAG_REPRESS_TARGET - _gap
                    for _j in range(_zi, len(events)):
                        events[_j]['Time'] = events[_j].get('Time', 0) + _shift

        if is_dmwm:
            has_dmwm = True
        
        base_time = base_time_pre_filter
        
        if cycle_events:
            pre_file_pause = rng.uniform(500.0, 800.0) * mult
            timeline += pre_file_pause

            total_pre_pause += pre_file_pause
            
            last_x, last_y = None, None
            for e in reversed(cycle_events):
                if e.get('X') is not None and e.get('Y') is not None:
                    last_x, last_y = int(e['X']), int(e['Y'])
                    break
            
            first_x, first_y = None, None
            for e in events:
                if e.get('X') is not None and e.get('Y') is not None:
                    first_x, first_y = int(e['X']), int(e['Y'])
                    break
            
            if not is_click_sensitive:
                transition_duration = rng.uniform(200.0, 400.0) * mult
                if last_x is not None and first_x is not None and (last_x != first_x or last_y != first_y):
                    transition_path = generate_human_path(
                        last_x, last_y, first_x, first_y,
                        int(transition_duration), rng
                    )
                    for rel_time, x, y in transition_path:
                        cycle_events.append({
                            'Type': 'MouseMove',
                            'Time': timeline + rel_time,
                            'X': x,
                            'Y': y
                        })
                    timeline += transition_duration
                    total_transition_time += int(transition_duration)
                    cycle_events.append({
                        'Type': 'MouseMove',
                        'Time': timeline,
                        'X': first_x,
                        'Y': first_y
                    })
                    # ================================================================
                    # FIX #3: POST-SNAP-GAP USES FLOAT PRECISION (v3.18.80)
                    # ================================================================
                    # Previously: post_snap_gap = int(rng.uniform(80, 150))
                    # Problem: Truncating to int() loses float precision.
                    # Solution: Use float, advance timeline with float, accumulate float.
                    # ================================================================
                    post_snap_gap = rng.uniform(80.0, 150.0)
                    timeline += post_snap_gap
                    total_snap_gap_time += post_snap_gap
        
        for event in events:
            new_event = {**event}
            new_event['Time'] = event['Time'] - base_time + timeline
            cycle_events.append(new_event)
        
        if cycle_events:
            timeline = cycle_events[-1]['Time']
            file_info_list.append((folder_num, file_label, is_dmwm, timeline))
        files_added += 1
    
    cycle_events = []
    file_info_list = []
    timeline = 0
    has_dmwm = False
    
    files_added = 0
    total_pre_pause = 0
    total_transition_time = 0
    total_snap_gap_time = 0
    total_distraction_pause = 0
    
    single_subfolder = len(subfolder_files) == 1
    if single_subfolder:
        only_folder_num = next(iter(subfolder_files))
        only_folder_data = subfolder_files[only_folder_num]
        single_always_first = _pick_af_al(only_folder_data.get('always_first', []), rng)
        single_always_last  = _pick_af_al(only_folder_data.get('always_last',  []), rng)
        if single_always_first and play_always_first:
            is_dmwm = single_always_first in dmwm_file_set
            add_file_to_cycle(single_always_first, only_folder_num, is_dmwm,
                              f"[ALWAYS FIRST] {single_always_first.name}")
    
    def _maybe_insert_distraction(cur_folder_num):
        """Roll the chance and insert one distraction file at the current timeline."""
        nonlocal total_distraction_pause
        if not distraction_files or distraction_chance <= 0.0:
            return
        if rng.random() < distraction_chance:
            dist
