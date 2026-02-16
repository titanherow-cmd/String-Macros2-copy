#!/usr/bin/env python3
"""
string_macros.py - v2.2.0 - Extract Numbers from Folder Names
- FIX: Now scans folder names for numbers (e.g., "part1", "step2", "3-action")
- Extracts and orders by number, not strict digit-only folder names
- ISSUE: v2.1.0 required folders to be exactly "1", "2", "3" (too strict)
"""

import argparse, json, random, re, sys, os, math, shutil, itertools
from pathlib import Path

VERSION = "v2.2.0"

# ============================================================================
# HELPER FUNCTIONS (from merge_macros)
# ============================================================================

def format_ms_precise(ms):
    """Format milliseconds as Xm Ys"""
    total_sec = int(ms / 1000)
    minutes = total_sec // 60
    seconds = total_sec % 60
    return f"{minutes}m {seconds}s"

def format_ms_precise(ms):
    """Format milliseconds as Xm Ys"""
    total_sec = int(ms / 1000)
    minutes   = total_sec // 60
    seconds   = total_sec % 60
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
    Removes: HOME(36), END(35), PAGE_UP(33), PAGE_DOWN(34), ESC(27), PAUSE(19), PRINT_SCREEN(44)
    """
    problematic_codes = {27, 19, 33, 34, 35, 36, 44}
    filtered = []
    
    for event in events:
        keycode = event.get('KeyCode')
        if keycode in problematic_codes:
            continue
        filtered.append(event)
    
    return filtered

def generate_human_path(start_x, start_y, end_x, end_y, duration_ms, rng):
    """
    Generate a human-like mouse path with variable speed and wobbles.
    Returns: List of (time_ms, x, y) tuples.
    """
    if duration_ms < 100:
        return [(0, end_x, end_y)]
    
    path = []
    dx = end_x - start_x
    dy = end_y - start_y
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance < 5:
        return [(0, end_x, end_y)]
    
    speed_profile = rng.choice(['fast_start', 'slow_start', 'medium', 'hesitant'])
    num_steps = max(3, min(int(distance / 15), int(duration_ms / 50)))
    
    # Add control points for curved path
    num_control = rng.randint(1, 3)
    control_points = []
    for _ in range(num_control):
        offset = rng.uniform(-0.3, 0.3) * distance
        t = rng.uniform(0.2, 0.8)
        ctrl_x = start_x + dx * t + (-dy / (distance + 1)) * offset
        ctrl_y = start_y + dy * t + (dx / (distance + 1)) * offset
        control_points.append((ctrl_x, ctrl_y, t))
    
    control_points.sort(key=lambda p: p[2])
    current_time = 0
    
    for step in range(num_steps + 1):
        t_raw = step / num_steps
        
        # Apply speed profile
        if speed_profile == 'fast_start':
            t = 1 - (1 - t_raw) ** 2
        elif speed_profile == 'slow_start':
            t = t_raw ** 2
        elif speed_profile == 'hesitant':
            t = 0.5 * (1 - math.cos(t_raw * math.pi))
        else:
            t = 0.5 * (1 - math.cos(t_raw * math.pi))
        
        # Calculate position
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
        
        # Add wobble
        wobble = rng.uniform(1, 5) if step > 0 and step < num_steps else 0
        x += rng.uniform(-wobble, wobble)
        y += rng.uniform(-wobble, wobble)
        
        # Bounds
        x = max(100, min(1800, int(x)))
        y = max(100, min(1000, int(y)))
        
        step_time = int(t * duration_ms)
        current_time = max(current_time, step_time)
        path.append((current_time, x, y))
    
    return path

# ============================================================================
# COMBINATION TRACKER
# ============================================================================

class CombinationTracker:
    """
    Tracks which combinations of files have been used from numbered subfolders.
    Ensures all possible combinations are used before repeating any.
    """
    def __init__(self, subfolder_files, rng):
        self.subfolder_files = subfolder_files
        self.rng = rng
        
        folder_numbers = sorted(subfolder_files.keys())
        file_lists = [subfolder_files[num] for num in folder_numbers]
        
        self.all_combinations = list(itertools.product(*file_lists))
        self.rng.shuffle(self.all_combinations)
        
        self.used_combinations = set()
        self.current_pool = list(self.all_combinations)
        
        print(f"  📊 Combination tracker initialized:")
        print(f"     Total possible combinations: {len(self.all_combinations)}")
        for num in folder_numbers:
            print(f"     Folder {num}: {len(subfolder_files[num])} files")
    
    def get_next_combination(self):
        if not self.current_pool:
            print(f"  🔄 All {len(self.all_combinations)} combinations used, reshuffling...")
            self.current_pool = list(self.all_combinations)
            self.rng.shuffle(self.current_pool)
            self.used_combinations.clear()
        
        combo = self.current_pool.pop(0)
        self.used_combinations.add(combo)
        
        return combo

# ============================================================================
# STRING INDIVIDUAL FILES FROM SUBFOLDERS
# ============================================================================

def string_files_from_subfolders(subfolder_files, tracker, rng):
    """
    Gets next combination and strings files in order (1→2→3).
    Adds smooth cursor transitions between subfolders.
    Applies problematic key filtering.
    Returns stringed events and file names.
    """
    combination = tracker.get_next_combination()
    
    stringed_events = []
    timeline = 0
    
    for idx, file_path in enumerate(combination):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                events = json.load(f)
        except Exception as e:
            print(f"    ⚠️ Error loading {file_path.name}: {e}")
            continue
        
        if not events:
            continue
        
        # CRITICAL: Filter problematic keys
        events = filter_problematic_keys(events)
        
        if not events:
            continue
        
        # Normalize timing to start at 0
        base_time = min(e.get('Time', 0) for e in events)
        
        # CURSOR TRANSITION: Add smooth movement between subfolders
        if idx > 0 and stringed_events:
            # Get last cursor position from previous subfolder
            last_cursor_event = None
            for e in reversed(stringed_events):
                if 'X' in e and 'Y' in e:
                    last_cursor_event = e
                    break
            
            # Get first cursor position from current subfolder
            first_cursor_event = None
            for e in events:
                if 'X' in e and 'Y' in e:
                    first_cursor_event = e
                    break
            
            # Add transition if positions differ
            if last_cursor_event and first_cursor_event:
                last_x, last_y = last_cursor_event['X'], last_cursor_event['Y']
                first_x, first_y = first_cursor_event['X'], first_cursor_event['Y']
                
                if (last_x != first_x) or (last_y != first_y):
                    # Calculate transition duration (50-150ms)
                    transition_duration = int(rng.uniform(50, 150))
                    
                    # Generate smooth path
                    transition_path = generate_human_path(
                        last_x, last_y,
                        first_x, first_y,
                        transition_duration,
                        rng
                    )
                    
                    # Insert transition events
                    for rel_time, x, y in transition_path[:-1]:  # Skip last (will be first event of next file)
                        stringed_events.append({
                            'Type': 'MouseMove',
                            'Time': timeline + rel_time,
                            'X': x,
                            'Y': y
                        })
                    
                    timeline += transition_duration
        
        # Add events from current subfolder
        for event in events:
            new_event = {**event}
            new_event['Time'] = event['Time'] - base_time + timeline
            stringed_events.append(new_event)
        
        # Update timeline (after this subfolder)
        if stringed_events:
            timeline = stringed_events[-1]['Time']
    
    return stringed_events, [f.name for f in combination]

# ============================================================================
# SCAN FOLDERS
# ============================================================================

def scan_for_numbered_subfolders(base_path):
    """
    Scans folder for subfolders with numbers in their names.
    Accepts: "1", "part1", "step2", "3-action", etc.
    Returns dict: {extracted_number: [list of .json files]}
    """
    base = Path(base_path)
    numbered_folders = {}
    
    for item in base.iterdir():
        if not item.is_dir():
            continue
        
        # Extract number from folder name using regex
        match = re.search(r'\d+', item.name)
        if match:
            folder_num = int(match.group())
            json_files = sorted(item.glob("*.json"))
            if json_files:
                numbered_folders[folder_num] = json_files
    
    return numbered_folders

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="String Macros v2.0.0")
    parser.add_argument("input_root", type=str)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--versions", type=int, default=6)
    parser.add_argument("--target-minutes", type=int, default=35)
    parser.add_argument("--bundle-id", type=int, required=True)
    parser.add_argument("--no-chat", action="store_true", help="Disable chat inserts")
    args = parser.parse_args()
    
    print("="*70)
    print(f"STRING MACROS v{VERSION}")
    print("="*70)
    print(f"Bundle ID: {args.bundle_id}")
    print(f"Target: {args.target_minutes} minutes per file")
    print(f"Versions: {args.versions}")
    print(f"Chat: {'DISABLED' if args.no_chat else 'ENABLED'}")
    print("="*70)
    
    # Setup
    search_base = Path(args.input_root).resolve()
    if not search_base.exists():
        print(f"❌ Input root not found: {search_base}")
        return
    
    output_root = Path(args.output_root).resolve()
    bundle_dir = output_root / f"stringed_bundle_{args.bundle_id}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    # Load chat files (optional)
    chat_files = []
    if not args.no_chat:
        chat_dir = Path(args.input_root).parent / "chat inserts"
        if chat_dir.exists() and chat_dir.is_dir():
            chat_files = list(chat_dir.glob("*.json"))
            if chat_files:
                print(f"✓ Found {len(chat_files)} chat insert files")
            else:
                print(f"⚠️ Chat inserts folder empty")
        else:
            print(f"⚠️ No chat inserts folder found")
    else:
        print(f"🔕 Chat inserts DISABLED")
    
    print()
    
    # Scan folders
    main_folders = []
    for folder in search_base.iterdir():
        if not folder.is_dir():
            continue
        
        numbered_subfolders = scan_for_numbered_subfolders(folder)
        
        if numbered_subfolders:
            main_folders.append({
                'path': folder,
                'name': folder.name,
                'subfolders': numbered_subfolders
            })
            print(f"✓ Found: {folder.name}")
            print(f"  Subfolders: {sorted(numbered_subfolders.keys())}")
    
    if not main_folders:
        print("❌ No folders with numbered subfolders found!")
        return
    
    print(f"\n📁 Total folders to process: {len(main_folders)}")
    print("="*70)
    
    # Initialize global chat queue (persists across all folders)
    rng = random.Random(args.bundle_id * 42)
    global_chat_queue = list(chat_files) if chat_files else []
    if global_chat_queue:
        rng.shuffle(global_chat_queue)
        print(f"🔄 Initialized global chat queue with {len(global_chat_queue)} files")
        print()
    
    # Process each folder
    for folder_data in main_folders:
        folder_name = folder_data['name']
        subfolder_files = folder_data['subfolders']
        
        # Extract folder number for version code (e.g. "47- Canifis" → 47)
        folder_num_match = re.search(r'\d+', folder_name)
        folder_number = int(folder_num_match.group()) if folder_num_match else 0
        
        print(f"\n🔨 Processing: {folder_name}")
        
        tracker = CombinationTracker(subfolder_files, rng)
        
        out_folder = bundle_dir / folder_name
        out_folder.mkdir(parents=True, exist_ok=True)
        
        target_ms = args.target_minutes * 60000
        
        # Calculate total original files and duration for manifest header
        total_original_files = sum(len(files) for files in subfolder_files.values())
        # Estimate single stringed file duration using average combination
        sample_combo = list(tracker.all_combinations[0]) if tracker.all_combinations else []
        total_original_ms = sum(get_file_duration_ms(f) for f in sample_combo) * len(tracker.all_combinations)
        
        manifest_lines = [
            f"MANIFEST FOR FOLDER: {folder_name}",
            "=" * 40,
            f"Script Version: {VERSION}",
            f"Stringed Bundle: stringed_bundle_{args.bundle_id}",
            f"Total Subfolders: {len(subfolder_files)}",
            f"Total Combinations: {len(tracker.all_combinations)}",
            " "
        ]
        
        # Generate versions
        for v_idx in range(1, args.versions + 1):
            v_letter = chr(64 + v_idx)
            v_code   = f"{folder_number}_{v_letter}"
            print(f"\n  Creating version {v_idx}/{args.versions} ({v_code})...")
            
            merged       = []
            timeline     = 0
            gap_total    = 0
            combo_log    = []   # [(folder_num, filename), ...]
            
            # Keep stringing combinations until we reach target duration
            while timeline < target_ms:
                stringed_events, combo_files_names = string_files_from_subfolders(
                    subfolder_files, tracker, rng
                )
                if not stringed_events:
                    break
                
                # Get the ordered folder numbers for this combination
                folder_keys = sorted(subfolder_files.keys())
                for fi, fname_part in enumerate(combo_files_names):
                    combo_log.append((folder_keys[fi], fname_part))
                
                # Inter-string gap (500-3000ms) between each stringed block
                if merged:
                    gap = int(rng.uniform(500.123, 2999.987))
                    
                    # Cursor transition during gap
                    last_cursor = next((e for e in reversed(merged) if 'X' in e and 'Y' in e), None)
                    first_cursor = next((e for e in stringed_events if 'X' in e and 'Y' in e), None)
                    if last_cursor and first_cursor:
                        lx, ly = last_cursor['X'], last_cursor['Y']
                        fx, fy = first_cursor['X'], first_cursor['Y']
                        if (lx != fx) or (ly != fy):
                            for rel_t, x, y in generate_human_path(lx, ly, fx, fy, gap, rng):
                                if rel_t < gap:
                                    merged.append({'Type': 'MouseMove', 'Time': timeline + rel_t, 'X': x, 'Y': y})
                    
                    timeline += gap
                    gap_total += gap
                
                base_t = min(e['Time'] for e in stringed_events)
                for e in stringed_events:
                    ne = {**e}
                    ne['Time'] = e['Time'] - base_t + timeline
                    merged.append(ne)
                
                if merged:
                    timeline = merged[-1]['Time']
                
                # Check if within 4 minutes of target - stop if adding more would overshoot
                remaining = target_ms - timeline
                next_combo = tracker.all_combinations[0] if tracker.current_pool else tracker.all_combinations[0]
                next_dur   = sum(get_file_duration_ms(f) for f in next_combo)
                if timeline >= target_ms - (4 * 60000) and next_dur > remaining + (4 * 60000):
                    break
            
            if not merged:
                print(f"    ⚠️ No events created, skipping...")
                continue
            
            timeline = merged[-1]['Time']
            total_minutes = int(timeline / 60000)
            total_seconds = int((timeline % 60000) / 1000)
            
            filename = f"{folder_number}_{v_letter}_{total_minutes}m{total_seconds}s.json"
            output_path = out_folder / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=2)
            
            print(f"    💾 Saved: {filename} ({total_minutes}m {total_seconds}s, {len(combo_log)} parts)")
            
            # Manifest entry
            manifest_lines += [
                "=" * 40,
                " ",
                f"Version {folder_number}_{v_letter}_{total_minutes}m{total_seconds}s:",
                f"FILE TYPE: Normal",
                f"  Between strings pause: {format_ms_precise(gap_total)}",
                ""
            ]
            for folder_num_log, file_name_log in combo_log:
                manifest_lines.append(f"  F{folder_num_log}* {file_name_log}")
            manifest_lines.append("")
        
        # Write manifest
        manifest_path = out_folder / f"!_MANIFEST_{folder_number}_!.txt"
        manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")
        print(f"\n  📋 Manifest written: {manifest_path.name}")
    
    print("\n" + "="*70)
    print(f"✅ STRING MACROS COMPLETE - Bundle {args.bundle_id}")
    print(f"📦 Output: {bundle_dir}")
    print("="*70)

if __name__ == "__main__":
    main()
