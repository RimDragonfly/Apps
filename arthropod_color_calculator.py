#!/usr/bin/env python3
"""
Arthropod Color Calculator
Project Gorgon Genetics Research — Kaskrim & Azizah
Compiled by AI Lumière

Given a CR1 (body) or CR3 (wing) genome, calculates the minimum changes
needed to reach a target color.

Usage:
    python3 arthropod_color_calculator.py

Then follow the prompts.

Notation: o = recessive, x/X/t = mixed, D/d = dominant
All non-recessive positions count as dominant or mixed for hue purposes.
"""

# ============================================================
# GENE MAPS
# ============================================================

# Locked dominant positions — can never be changed through breeding
LOCKED_DOMINANT_CR1 = {"1F2", "1G3", "1I1", "1I2", "1I4"}
LOCKED_DOMINANT_CR3 = {"3F3", "3G3", "3G4", "3I2", "3I3", "3I4"}

# Stat genes on CR1 (coord: (stat_name, point_value))
# Locked dominant stat genes are included for reference but marked
STAT_GENES_CR1 = {
    "1A2": ("Toughness", 2),
    "1B1": ("Friendliness", 3),
    "1B2": ("Ruggedness", 5),
    "1B3": ("Ferocity", 5),
    "1C1": ("Enthusiasm", 4),
    "1C2": ("Virility", 3),
    "1D1": ("Toughness", 3),
    "1D3": ("Friendliness", 0),   # locked recessive — always contributes
    "1E2": ("Intelligence", 3),
    "1E3": ("Enthusiasm", 5),
    "1F1": ("Intelligence", 4),
    "1F3": ("Virility", 2),
    "1F4": ("Ruggedness", 5),
    "1G1": ("Enthusiasm", 5),
    "1G2": ("Toughness", 6),
    "1G3": ("Virility", 0),       # locked dominant — never contributes
    "1H1": ("Friendliness", 5),
    "1H3": ("Ferocity", 3),
    "1H4": ("Ruggedness", 3),
    "1I1": ("Ferocity", 0),       # locked dominant — never contributes
    "1J1": ("Virility", 5),
    "1J2": ("Intelligence", 3),
}

# Stat genes on CR3
STAT_GENES_CR3 = {
    "3A1": ("Virility", 6),
    "3A4": ("Ferocity", 0),       # locked recessive
    "3B3": ("Ferocity", 0),       # locked recessive
    "3B4": ("Toughness", 0),      # locked recessive
    "3C1": ("Ruggedness", 6),
    "3C2": ("Enthusiasm", 1),
    "3D1": ("Friendliness", 0),   # locked recessive
    "3D3": ("Ferocity", 0),       # locked recessive
    "3E1": ("Toughness", 3),
    "3E3": ("Intelligence", 4),
    "3E4": ("Ruggedness", 4),
    "3F2": ("Toughness", 5),
    "3F3": ("Ruggedness", 0),     # locked dominant
    "3G1": ("Ferocity", 2),
    "3G2": ("Virility", 4),
    "3G4": ("Enthusiasm", 0),     # locked dominant
    "3H2": ("Friendliness", 4),
    "3H3": ("Friendliness", 3),
    "3I2": ("Intelligence", 0),   # locked dominant
    "3I4": ("Virility", 0),       # locked dominant
    "3J1": ("Ferocity", 3),
    "3J4": ("Intelligence", 7),
}

# Color ladder: color name -> (min F-J dom/mixed, max F-J dom/mixed)
# F-J has 20 positions total
COLOR_LADDER_CR1 = {
    "red":          (7,  9),
    "yellow-green": (10, 10),
    "green-yellow":  (10, 10),
    "orange":       (11, 13),
    "green-yellow":       (11, 13),
    "green":        (11, 13),
    
    "blue":         (14, 16),
    "blue-violet":  (17, 17),
    "teal":   (17, 19),
    "purple":       (17, 19),
    "violet":       (17, 19),
}

COLOR_LADDER_CR3 = {
    "red":          (10, 10),
    "orange":       (11, 13),
    "green-yellow":       (11, 13),
    "green":        (9,  13),
    
    "blue":         (14, 16),
    "blue-violet":  (15, 17),
    "teal":   (17, 19),
    "purple":       (17, 19),
    "violet":       (17, 19),
}

LABELS = list("ABCDEFGHIJ")

# ============================================================
# PARSING
# ============================================================

def parse_genome(raw, chromosome):
    """Parse a genome string into groups and states."""
    cleaned = raw.replace(" ", "")
    if len(cleaned) != 40:
        raise ValueError(f"Expected 40 positions, got {len(cleaned)}. Check input.")
    groups = [cleaned[i:i+4] for i in range(0, 40, 4)]
    positions = {}
    for i, label in enumerate(LABELS):
        for pos in range(4):
            coord = f"{chromosome}{label}{pos+1}"
            state = cleaned[i*4 + pos]
            positions[coord] = state
    return positions, groups

def is_dominant_or_mixed(state):
    """Returns True if the position counts as dominant or mixed (non-recessive)."""
    return state.lower() not in ("o", "r")

def fj_dom_count(positions, chromosome):
    """Count dominant or mixed positions in groups F-J."""
    count = 0
    for label in "FGHIJ":
        for pos in range(1, 5):
            coord = f"{chromosome}{label}{pos}"
            if coord in positions and is_dominant_or_mixed(positions[coord]):
                count += 1
    return count

def ae_dom_count(positions, chromosome):
    """Count dominant or mixed positions in groups A-E."""
    count = 0
    for label in "ABCDE":
        for pos in range(1, 5):
            coord = f"{chromosome}{label}{pos}"
            if coord in positions and is_dominant_or_mixed(positions[coord]):
                count += 1
    return count

# ============================================================
# COLOR DETECTION
# ============================================================

def detect_color(fj_dom, ae_dom, chromosome):
    """Estimate current color based on F-J and A-E dominant or mixed counts."""
    ladder = COLOR_LADDER_CR1 if chromosome == 1 else COLOR_LADDER_CR3
    matches = []
    for color, (lo, hi) in ladder.items():
        if lo <= fj_dom <= hi:
            matches.append(color)
    if not matches:
        min_fj = min(lo for lo, hi in ladder.values())
        if fj_dom < min_fj:
            return f"below ladder (F-J={fj_dom}) — counterclockwise from red, approaching violet"
        return "unknown"
    if len(matches) == 1:
        return matches[0]
    if fj_dom == 14:
        return "blue"
    if fj_dom == 9:
        if chromosome == 3:
            return "green" if ae_dom <= 4 else "orange"
        else:
            if ae_dom <= 4: return "green"
            elif ae_dom <= 8: return "yellow"
            else: return "orange"
    if fj_dom in (11, 12, 13):
        if ae_dom <= 2:
            return "teal" if fj_dom in (12, 13) else "green"
        elif ae_dom <= 4:
            return "green"
        elif ae_dom <= 8:
            return "green-yellow"
        else:
            return "orange"
    return "/".join(matches)

# ============================================================
# CHANGE CALCULATOR
# ============================================================

def calculate_changes(positions, chromosome, target_color):
    """Calculate minimum changes to reach target color."""
    cr = chromosome
    locked = LOCKED_DOMINANT_CR1 if cr == 1 else LOCKED_DOMINANT_CR3
    stat_genes = STAT_GENES_CR1 if cr == 1 else STAT_GENES_CR3
    ladder = COLOR_LADDER_CR1 if cr == 1 else COLOR_LADDER_CR3

    if target_color not in ladder:
        print(f"\nUnknown color '{target_color}'.")
        print(f"Valid colors: {', '.join(sorted(ladder.keys()))}")
        return

    target_lo, target_hi = ladder[target_color]
    current_fj = fj_dom_count(positions, cr)
    current_ae = ae_dom_count(positions, cr)

    print(f"\nCurrent F-J dominant or mixed: {current_fj}/20")
    print(f"Current A-E dominant or mixed: {current_ae}/20")
    print(f"Target color: {target_color} (F-J dom/mixed {target_lo}-{target_hi})")

    # Determine direction
    if target_lo <= current_fj <= target_hi:
        print(f"\nAlready in {target_color} zone by F-J count.")
        print("A-E dominant or mixed may still need adjustment for exact shade.")
        return

    total_stat_cost = {}

    if current_fj < target_lo:
        # Need MORE dominant or mixed in F-J — flip recessive → dominant
        needed = target_lo - current_fj
        direction = "recessive → dominant"
        candidates = []
        for label in "FGHIJ":
            for pos in range(1, 5):
                coord = f"{cr}{label}{pos}"
                if coord in positions and not is_dominant_or_mixed(positions[coord]):
                    if coord not in locked:
                        is_stat = coord in stat_genes and stat_genes[coord][1] > 0
                        stat_name = stat_genes[coord][0] if coord in stat_genes else None
                        stat_val = stat_genes[coord][1] if coord in stat_genes else 0
                        candidates.append((coord, is_stat, stat_name, stat_val))
        # Sort: cosmetic first, then by smallest stat cost
        candidates.sort(key=lambda x: (x[1], x[3]))

    else:
        # Need FEWER dominant or mixed in F-J — flip dominant → recessive
        needed = current_fj - target_hi
        direction = "dominant → recessive"
        candidates = []
        for label in "FGHIJ":
            for pos in range(1, 5):
                coord = f"{cr}{label}{pos}"
                if coord in positions and is_dominant_or_mixed(positions[coord]):
                    if coord not in locked:
                        is_stat = coord in stat_genes and stat_genes[coord][1] > 0
                        stat_name = stat_genes[coord][0] if coord in stat_genes else None
                        stat_val = stat_genes[coord][1] if coord in stat_genes else 0
                        candidates.append((coord, is_stat, stat_name, stat_val))
        # Sort: cosmetic first, then by smallest stat cost
        candidates.sort(key=lambda x: (x[1], x[3]))

    if needed <= 0:
        print("No F-J changes needed.")
        return

    print(f"\nNeed to flip {needed} F-J position(s) {direction}.")

    if len(candidates) < needed:
        print(f"WARNING: Only {len(candidates)} eligible positions available — not enough to reach target.")

    print(f"\nRecommended changes (fewest rolls, smallest stat cost):")
    print("-" * 50)
    for i, (coord, is_stat, stat_name, stat_val) in enumerate(candidates[:needed]):
        if is_stat and stat_val > 0:
            sign = "-" if direction == "dominant → recessive" else "+"
            note = f"costs {sign}{stat_val} {stat_name}"
        else:
            note = "cosmetic — no stat cost"
        print(f"  {i+1}. {coord}: {direction}  [{note}]")
        if is_stat and stat_val > 0:
            if direction == "dominant → recessive":
                total_stat_cost[stat_name] = total_stat_cost.get(stat_name, 0) - stat_val
            else:
                total_stat_cost[stat_name] = total_stat_cost.get(stat_name, 0) + stat_val

    if total_stat_cost:
        print(f"\nTotal stat impact:")
        for stat, delta in sorted(total_stat_cost.items()):
            sign = "+" if delta > 0 else ""
            print(f"  {stat}: {sign}{delta}")
    else:
        print(f"\nNo stat cost.")

    # Show remaining candidates if stat cost is involved
    if any(c[1] for c in candidates[:needed]):
        remaining = candidates[needed:]
        if remaining:
            print(f"\nAlternative positions (higher stat cost or more rolls):")
            for coord, is_stat, stat_name, stat_val in remaining[:5]:
                note = f"{stat_val} {stat_name}" if is_stat and stat_val > 0 else "cosmetic"
                print(f"  {coord}: {note}")

# ============================================================
# MAIN
# ============================================================

# ============================================================
# MAIN
# ============================================================

def show_current_traits(cr1_data, cr3_data, cr5_data, cr9_data):
    """Print a summary of all current visual traits."""
    print()
    print("=" * 55)
    print("  YOUR BEE — CURRENT VISUAL TRAITS")
    print("=" * 55)
    if cr1_data:
        print(f"  Body color  (CR1): {cr1_data['color']}  (F-J={cr1_data['fj']}/20, A-E={cr1_data['ae']}/20)")
    else:
        print("  Body color  (CR1): not parsed")
    if cr3_data:
        print(f"  Wing color  (CR3): {cr3_data['color']}  (F-J={cr3_data['fj']}/20, A-E={cr3_data['ae']}/20)")
    else:
        print("  Wing color  (CR3): not parsed")
    if cr5_data:
        glow_label = "ON" if cr5_data["glow"] else "Off"
        print(f"  Glow        (CR5): {glow_label}")
    else:
        print("  Glow        (CR5): not parsed")
    if cr9_data:
        tl = cr9_data["taillight"]
        tl_label = " or ".join(tl) if cr9_data["taillight_ambiguous"] else (tl[0] if tl != ["Unknown"] else "Unknown")
        print(f"  Particles   (CR9): {cr9_data['particle']}")
        print(f"  Tail light  (CR9): {tl_label}")
    else:
        print("  Particles   (CR9): not parsed")
        print("  Tail light  (CR9): not parsed")
    print("=" * 55)


def change_body_color(cr1_data):
    """Interactive body color change section."""
    print()
    print("-" * 55)
    print("  CHANGE BODY COLOR (CR1)")
    print("-" * 55)
    ladder = COLOR_LADDER_CR1
    print("Available target colors:")
    fj = cr1_data["fj"]
    ae = cr1_data["ae"]
    for color, (lo, hi) in sorted(ladder.items(), key=lambda x: x[1][0]):
        rng = f"{lo}" if lo == hi else f"{lo}-{hi}"
        marker = " (current)" if lo <= fj <= hi else ""
        print(f"  {color:<14} (F-J {rng}){marker}")
    target = input("\nTarget color (or Enter to skip): ").strip()
    if not target:
        return
    status, paths, _ = calculate_changes(cr1_data["positions"], 1, target)
    if status == "already_there":
        print(f"Already in the {target} zone (F-J={fj}).")
        # A-E guidance
        ae_guidance = None
        if fj >= 17:
            if target == "Purple":      ae_guidance = ("below 4",    "ae_decrease", 4)
            elif target == "Blue-violet": ae_guidance = ("4 to 6",   "ae_range", (4,6))
            elif target == "Teal":       ae_guidance = ("7 or more", "ae_increase", 7)
        elif fj in (14,15,16):
            if target == "Blue": ae_guidance = ("below 5",   "ae_decrease", 5)
            elif target == "Teal": ae_guidance = ("5 or more","ae_increase", 5)
        elif fj in (11,12,13):
            if target == "Green":  ae_guidance = ("3 to 4",    "ae_range", (3,4))
            elif target == "Yellow": ae_guidance = ("5 to 8",   "ae_range", (5,8))
            elif target == "Orange": ae_guidance = ("9 or more","ae_increase", 9)
        elif fj == 9:
            if target == "Green":  ae_guidance = ("4 or below","ae_decrease", 4)
            elif target == "Yellow": ae_guidance = ("5 to 8",   "ae_range", (5,8))
            elif target == "Orange": ae_guidance = ("9 or more","ae_increase", 9)
        if ae_guidance:
            label, direction, threshold = ae_guidance
            if direction == "ae_increase":
                needed = max(0, threshold - ae)
                if needed > 0:
                    print(f"A-E is {ae}/20. To reach {target}, need A-E {label} — flip {needed} more A-E position(s) to dominant.")
                else:
                    print(f"A-E is {ae} — already in the {target} range.")
            elif direction == "ae_decrease":
                needed = max(0, ae - (threshold - 1))
                if needed > 0:
                    print(f"A-E is {ae}/20. To reach {target}, need A-E {label} — flip {needed} A-E position(s) to recessive.")
                else:
                    print(f"A-E is {ae} — already in the {target} range.")
            elif direction == "ae_range":
                lo, hi = threshold
                if ae < lo:
                    print(f"A-E is {ae}/20. To reach {target}, need A-E {label} — flip {lo-ae} more A-E position(s) to dominant.")
                elif ae > hi:
                    print(f"A-E is {ae}/20. To reach {target}, need A-E {label} — flip {ae-hi} A-E position(s) to recessive.")
                else:
                    print(f"A-E is {ae} — already in the {target} range.")
        else:
            print(f"A-E is {ae}/20 — fine-tunes the exact shade within this zone.")
    elif paths:
        def print_path(path, label):
            direction = path["direction"]; needed = path["needed"]
            selected = path["selected"]; cost = path["cost"]; pts = path["pts"]
            if not path["feasible"]:
                print(f"  {label}: Only {len(selected)} eligible positions — not enough.")
                return
            net = sum(cost.values())
            sign = f"+{net}" if net >= 0 else str(net)
            print(f"  {label}: {needed} change(s), net stat {sign}")
            print(f"  Direction: {direction}")
            for i, (coord, is_stat, stat_name, stat_val) in enumerate(selected):
                if is_stat and stat_val > 0:
                    delta = stat_val if direction == "dominant → recessive" else -stat_val
                    s = "+" if delta > 0 else ""
                    print(f"    {i+1}. {coord}: {s}{delta} {stat_name}")
                else:
                    print(f"    {i+1}. {coord}: cosmetic")
            if cost:
                for stat, delta in sorted(cost.items()):
                    s = "+" if delta > 0 else ""
                    print(f"    Total {stat}: {s}{delta}")
        path_a = paths.get("path_a"); path_b = paths.get("path_b")
        print_path(path_a, "Recommended path")
        if path_b:
            print()
            print_path(path_b, "Alternative path")


def change_wing_color(cr3_data):
    """Interactive wing color change section."""
    print()
    print("-" * 55)
    print("  CHANGE WING COLOR (CR3)")
    print("-" * 55)
    ladder = COLOR_LADDER_CR3
    fj = cr3_data["fj"]; ae = cr3_data["ae"]
    print("Available target colors:")
    for color, (lo, hi) in sorted(ladder.items(), key=lambda x: x[1][0]):
        rng = f"{lo}" if lo == hi else f"{lo}-{hi}"
        marker = " (current)" if lo <= fj <= hi else ""
        print(f"  {color:<14} (F-J {rng}){marker}")
    target = input("\nTarget color (or Enter to skip): ").strip()
    if not target:
        return
    status, paths, _ = calculate_changes(cr3_data["positions"], 3, target)
    if status == "already_there":
        print(f"Already in the {target} zone (F-J={fj}).")
        ae_guidance = None
        if fj in (9,10,11,12,13):
            if target == "Green":  ae_guidance = ("4 or below","ae_decrease", 4)
            elif target == "Orange": ae_guidance = ("5 or more","ae_increase", 5)
        if ae_guidance:
            label, direction, threshold = ae_guidance
            if direction == "ae_increase":
                needed = max(0, threshold - ae)
                if needed > 0: print(f"A-E is {ae}/20. Need A-E {label} — flip {needed} more A-E to dominant.")
                else: print(f"A-E is {ae} — in the {target} range.")
            elif direction == "ae_decrease":
                needed = max(0, ae - (threshold - 1))
                if needed > 0: print(f"A-E is {ae}/20. Need A-E {label} — flip {needed} A-E to recessive.")
                else: print(f"A-E is {ae} — in the {target} range.")
        else:
            print(f"A-E is {ae}/20 — fine-tunes exact shade.")
    elif paths:
        path_a = paths.get("path_a"); path_b = paths.get("path_b")
        def print_path_cr3(path, label):
            direction = path["direction"]; needed = path["needed"]
            selected = path["selected"]; cost = path["cost"]
            if not path["feasible"]:
                print(f"  {label}: Not enough eligible positions."); return
            net = sum(cost.values()); sign = f"+{net}" if net >= 0 else str(net)
            print(f"  {label}: {needed} change(s), net stat {sign}")
            for i, (coord, is_stat, stat_name, stat_val) in enumerate(selected):
                if is_stat and stat_val > 0:
                    delta = stat_val if direction == "dominant → recessive" else -stat_val
                    s = "+" if delta > 0 else ""
                    print(f"    {i+1}. {coord}: {s}{delta} {stat_name}")
                else:
                    print(f"    {i+1}. {coord}: cosmetic")
            if cost:
                for stat, delta in sorted(cost.items()):
                    s = "+" if delta > 0 else ""; print(f"    Total {stat}: {s}{delta}")
        print_path_cr3(path_a, "Recommended")
        if path_b:
            print(); print_path_cr3(path_b, "Alternative")


def change_glow(cr5_data):
    """Interactive glow change section."""
    print()
    print("-" * 55)
    print("  CHANGE GLOW (CR5)")
    print("-" * 55)
    glow_on = cr5_data["glow"]
    current_norm = cr5_data["norm"]
    coords5 = [f"5{l}{p}" for l, sz in [("A",4),("B",4),("C",2)] for p in range(1, sz+1)]
    print(f"Current glow: {'ON' if glow_on else 'Off'}")
    print()
    print("Current CR5 stat contributions:")
    if cr5_data["expressing"]:
        for coord, stat_name, stat_val in sorted(cr5_data["expressing"]):
            print(f"  {coord}: +{stat_val} {stat_name}")
        for stat, total in sorted(cr5_data["stat_totals"].items()):
            print(f"  Total {stat}: +{total}")
    else:
        print("  None expressing.")
    print()
    choice = input("I want glow (on/off, or Enter to skip): ").strip().lower()
    if choice not in ("on", "off"):
        return

    FEROCITY_PATTERN     = "oooooXoXoo"
    FRIENDLINESS_PATTERN = "oooooXXoXo"
    WORST_GLOW_PATTERN   = "oooooXXXXo"

    if choice == "on":
        if glow_on:
            # Check for better-stat patterns
            is_worst = current_norm == WORST_GLOW_PATTERN
            if is_worst:
                print("WARNING: Current pattern has lowest stats — costs both Ferocity and Friendliness.")
            current_total = sum(STAT_GENES_CR5[c][1] for i,c in enumerate(coords5)
                                if current_norm[i]=="o" and c in STAT_GENES_CR5 and STAT_GENES_CR5[c][1]>0)
            better = []
            for t in GLOW_ON_PATTERNS:
                if t == current_norm: continue
                tt = sum(STAT_GENES_CR5[c][1] for i,c in enumerate(coords5)
                         if t[i]=="o" and c in STAT_GENES_CR5 and STAT_GENES_CR5[c][1]>0)
                if tt > current_total:
                    flips, net = [], {}
                    for i,c in enumerate(coords5):
                        if current_norm[i] != t[i]:
                            d = "recessive → dominant" if t[i]=="X" else "dominant → recessive"
                            si = STAT_GENES_CR5.get(c)
                            if si and si[1]>0:
                                delta = si[1] if "dominant → recessive" in d else -si[1]
                                net[si[0]] = net.get(si[0],0)+delta
                            flips.append({"coord":c,"direction":d,"stat":si})
                    better.append({"target":t,"flips":flips,"flips_count":len(flips),"net_stat":net,"net_total":sum(net.values())})
            if better:
                best = max(better, key=lambda p: p["net_total"])
                print(f"Glow ON — better-stat pattern available (+{best['net_total']} net):")
                show_glow_path_text(best, f"Better option ({best['flips_count']} flip(s))")
            else:
                print("Glow ON — current pattern already has the best stats.")
        else:
            paths_speed, _ = glow_on_paths(cr5_data["positions"], current_norm)
            fastest  = paths_speed[0]
            fe_path  = next((p for p in paths_speed if p["target"]==FEROCITY_PATTERN), None)
            fr_path  = next((p for p in paths_speed if p["target"]==FRIENDLINESS_PATTERN), None)
            print("--- Shortest path to glow on ---")
            show_glow_path_text(fastest, "Shortest")
            print("\n--- Path to -1 Ferocity glow ---")
            if fe_path and fe_path["flips_count"]==0: print("  Already on this pattern.")
            elif fe_path: show_glow_path_text(fe_path, f"{fe_path['flips_count']} flip(s)")
            else: print("  No path available.")
            print("\n--- Path to -3 Friendliness glow ---")
            if fr_path and fr_path["flips_count"]==0: print("  Already on this pattern.")
            elif fr_path: show_glow_path_text(fr_path, f"{fr_path['flips_count']} flip(s)")
            else: print("  No path available.")
    else:  # off
        off_flips, off_net = [], {}
        target_list = list(current_norm)
        for i,coord in enumerate(coords5):
            if current_norm[i]=="X" and coord in STAT_GENES_CR5:
                target_list[i]="o"
                si = STAT_GENES_CR5[coord]
                if si[1]>0: off_net[si[0]]=off_net.get(si[0],0)+si[1]
                off_flips.append({"coord":coord,"direction":"dominant → recessive","stat":si})
        off_target = "".join(target_list)
        if not glow_on and not off_flips:
            print("Glow already off — all stat genes expressing.")
        elif not glow_on:
            print("Glow off — but stat improvement possible:")
            off_path = {"target":off_target,"flips":off_flips,"flips_count":len(off_flips),"net_stat":off_net,"net_total":sum(off_net.values())}
            show_glow_path_text(off_path, f"Max stats ({len(off_flips)} flip(s))")
        elif off_target in GLOW_ON_PATTERNS:
            print("WARNING: Flipping stat genes alone still results in a glow-on pattern. Additional cosmetic flip needed.")
        elif not off_flips:
            print("All stat genes already recessive — glow effectively off.")
        else:
            off_path = {"target":off_target,"flips":off_flips,"flips_count":len(off_flips),"net_stat":off_net,"net_total":sum(off_net.values())}
            show_glow_path_text(off_path, f"Turn glow off — max stats ({len(off_flips)} flip(s))")


def _print_cr9_path(path, label):
    """Print a CR9 flip path with stat notes."""
    net = path["net_total"]; sign = f"+{net}" if net>=0 else str(net)
    print(f"  {label}: {path['flips_count']} flip(s), net stat {sign}")
    print(f"    Target: {path['target']}")
    for f in path["flips"]:
        si = STAT_GENES_CR9.get(f["coord"])
        if si and si[1]>0:
            delta = si[1] if "dominant → recessive" in f["direction"] else -si[1]
            s = "+" if delta>0 else ""
            print(f"    {f['coord']}: {f['direction']} -> {s}{delta} {si[0]}")
        else:
            print(f"    {f['coord']}: {f['direction']} -> cosmetic")
    for stat, delta in sorted(path["net_stat"].items()):
        s = "+" if delta>0 else ""; print(f"    Total {stat}: {s}{delta}")


def change_particles_taillight(cr9_data, cr9_raw):
    """Interactive particles and tail light change section."""
    print()
    print("-" * 55)
    print("  CHANGE PARTICLES & TAIL LIGHT (CR9)")
    print("-" * 55)
    norm_cr9, err = normalize_str(cr9_raw, 20)
    if err:
        print(f"Error: {err}"); return
    particle_key  = norm_cr9[:10]
    taillight_key = norm_cr9[10:]
    p = cr9_data["particle"]
    tl = cr9_data["taillight"]
    ambiguous = cr9_data["taillight_ambiguous"]
    tl_label = " or ".join(tl) if ambiguous else (tl[0] if tl != ["Unknown"] else "Unknown")
    print(f"Current particles: {p}")
    print(f"Current tail light: {tl_label}")
    if ambiguous:
        print("  (Ambiguous — needs more data. Share confirmed color with Kaskrim.)")

    # Particles
    print()
    print("Particle location options: Tail / Wing / None")
    target_p = input("Target particle location (or Enter to skip): ").strip().capitalize()
    if target_p in ("Tail", "Wing", "None"):
        if target_p == p:
            paths = particle_paths(particle_key)
            p_result = paths.get(target_p)
            best_stat = p_result["best_stat"] if p_result else None
            if best_stat and best_stat["flips_count"] > 0 and best_stat["net_total"] > 0:
                print(f"Already {target_p} — but better-stat pattern exists:")
                _print_cr9_path(best_stat, "Better stat option")
            else:
                print(f"Already {target_p} — optimal stats.")
        elif target_p == "None":
            print("No-particle states achievable but not yet documented in research data.")
        else:
            paths = particle_paths(particle_key)
            p_result = paths.get(target_p)
            fastest = p_result["fastest"] if p_result else None
            best_stat = p_result["best_stat"] if p_result else None
            if fastest:
                print("--- Fewest flips ---")
                print_cr9(fastest, "Fastest")
                if best_stat and best_stat["target"] != fastest["target"]:
                    print("--- Best stat ---")
                    print_cr9(best_stat, "Best stat")
                else:
                    print("  (Fastest is also best stat.)")
            else:
                print(f"No known pattern for {target_p}.")

    # Tail light
    all_colors = sorted(set(c for colors in TAILLIGHT_LOOKUP.values() for c in colors))
    print()
    print(f"Available tail light colors: {', '.join(all_colors)}")
    target_tl = input("Target tail light color (or Enter to skip): ").strip()
    if target_tl in all_colors:
        current_tl = tl[0] if tl and tl != ["Unknown"] and not ambiguous else None
        if current_tl and target_tl == current_tl:
            print(f"Already {target_tl} — no flips needed.")
        else:
            tl_paths = taillight_paths(taillight_key)
            tl_result = tl_paths.get(target_tl)
            tl_fastest = tl_result["fastest"] if tl_result else None
            tl_best    = tl_result["best_stat"] if tl_result else None
            if tl_fastest:
                print("--- Fewest flips ---")
                _print_cr9_path(tl_fastest, "Fastest")
                if tl_best and tl_best["target"] != tl_fastest["target"]:
                    print("--- Best stat ---")
                    _print_cr9_path(tl_best, "Best stat")
                else:
                    print("  (Fastest is also best stat.)")
            else:
                print(f"No known pattern for {target_tl} in research data.")


def main():
    print("=" * 55)
    print("  Arthropod Visual Trait Calculator")
    print("  Project Gorgon Genetics Research")
    print("  Kaskrim & Azizah — Lumière")
    print("=" * 55)
    print()
    print("Genetics skill must be uncapped at level 100.")
    print("Do not use with genomes containing ? marks.")
    print()
    print("Paste a full genome export, or press Enter to enter chromosomes individually.")
    export_raw = input("Full export (or Enter to skip): ").strip()

    parsed_export = None
    cr1_raw = cr3_raw = cr5_raw = cr9_raw = ""

    if export_raw:
        parsed_export = parse_full_export(export_raw)
        if parsed_export:
            cr1_raw = parsed_export.get(1, "")
            cr3_raw = parsed_export.get(3, "")
            cr5_raw = parsed_export.get(5, "")
            cr9_raw = parsed_export.get(9, "")
            print(f"Parsed — found: {', '.join(f'CR{k}' for k in sorted(parsed_export.keys()))}")
        else:
            print("Doesn't look like a full export. Enter chromosomes individually.")

    if not cr1_raw:
        cr1_raw = input("CR1 — Body color (40 positions, or Enter to skip): ").strip()
    if not cr3_raw:
        cr3_raw = input("CR3 — Wing color (40 positions, or Enter to skip): ").strip()
    if not cr5_raw:
        cr5_raw = input("CR5 — Glow (10 positions, or Enter to skip): ").strip()
    if not cr9_raw:
        cr9_raw = input("CR9 — Particles & Tail Light (20 positions, or Enter to skip): ").strip()

    # Parse all inputs
    cr1_data = cr3_data = cr5_data = cr9_data = None

    if cr1_raw:
        pos, err = parse_genome(cr1_raw, 1)
        if err: print(f"CR1 error: {err}")
        else:
            fj = fj_dom_count(pos, 1); ae = ae_dom_count(pos, 1)
            cr1_data = {"positions": pos, "fj": fj, "ae": ae, "color": detect_color(fj, ae, 1)}

    if cr3_raw:
        pos, err = parse_genome(cr3_raw, 3)
        if err: print(f"CR3 error: {err}")
        else:
            fj = fj_dom_count(pos, 3); ae = ae_dom_count(pos, 3)
            cr3_data = {"positions": pos, "fj": fj, "ae": ae, "color": detect_color(fj, ae, 3)}

    if cr5_raw:
        res, err = analyze_cr5(cr5_raw)
        if err: print(f"CR5 error: {err}")
        else: cr5_data = res

    if cr9_raw:
        res, err = lookup_cr9(cr9_raw)
        if err: print(f"CR9 error: {err}")
        else: cr9_data = res

    # Show current traits
    show_current_traits(cr1_data, cr3_data, cr5_data, cr9_data)

    # Change menu
    while True:
        print()
        print("What would you like to change?")
        options = []
        if cr1_data: options.append(("1", "Body color (CR1)"))
        if cr3_data: options.append(("3", "Wing color (CR3)"))
        if cr5_data: options.append(("5", "Glow (CR5)"))
        if cr9_data: options.append(("9", "Particles & Tail Light (CR9)"))
        options.append(("q", "Quit"))
        for key, label in options:
            print(f"  {key} = {label}")
        choice = input("Choice: ").strip().lower()
        if choice == "q":
            break
        elif choice == "1" and cr1_data:
            change_body_color(cr1_data)
        elif choice == "3" and cr3_data:
            change_wing_color(cr3_data)
        elif choice == "5" and cr5_data:
            change_glow(cr5_data)
        elif choice == "9" and cr9_data:
            change_particles_taillight(cr9_data, cr9_raw)
        else:
            print("Invalid choice.")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
