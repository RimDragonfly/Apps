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

    changes_needed = []
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

def main():
    print("=" * 55)
    print("  Arthropod Color Calculator")
    print("  Project Gorgon Genetics Research")
    print("  Kaskrim & Azizah — Lumière")
    print("=" * 55)
    print()
    print("!! IMPORTANT: Genetics skill must be uncapped at level 100.")
    print("Do not use this tool with a genome that contains ? marks.")
    print()
    print("Chromosome options:")
    print("  1 = CR1 (body color hue)")
    print("  3 = CR3 (wing color hue)")
    print()

    while True:
        cr_input = input("Chromosome (1 or 3): ").strip()
        if cr_input in ("1", "3"):
            chromosome = int(cr_input)
            break
        print("  Please enter 1 or 3.")

    print()
    print("Enter the 40-position genome string.")
    print("Spaces are fine. o=recessive, x/X/t/D=dominant or mixed.")
    raw = input("Genome: ").strip()

    try:
        positions, groups = parse_genome(raw, chromosome)
    except ValueError as e:
        print(f"\nError: {e}")
        return

    fj = fj_dom_count(positions, chromosome)
    ae = ae_dom_count(positions, chromosome)
    current_color = detect_color(fj, ae, chromosome)

    print(f"\nParsed successfully.")
    print(f"F-J dominant or mixed: {fj}/20")
    print(f"A-E dominant or mixed: {ae}/20")
    print(f"Estimated current color: {current_color}")

    if "below ladder" in current_color.lower() or (fj <= 6):
        print()
        print("NOTE — Low F-J zone (bottom of the wheel):")
        print("The color wheel is circular. Red appears at both ends of the ladder.")
        print("All-recessive on CR 1 is confirmed to produce red by wrapping")
        print("clockwise past violet. What other colors exist in the F-J=0-6")
        print("zone is untested. This app defaults to Red below F-J=7.")
        print("If your bee shows an unusual color at very low F-J, please")
        print("share that data with Kaskrim.")

    print()
    print("Available target colors:")
    ladder = COLOR_LADDER_CR1 if chromosome == 1 else COLOR_LADDER_CR3
    for color, (lo, hi) in sorted(ladder.items(), key=lambda x: x[1][0]):
        rng = f"{lo}" if lo == hi else f"{lo}-{hi}"
        marker = " (current)" if lo <= fj <= hi else ""
        print(f"  {color:<14} (F-J dom/mixed {rng}){marker}")

    print()
    target = input("Target color: ").strip().lower()
    calculate_changes(positions, chromosome, target)

    print()
    another = input("Check visual traits (glow/particles/tail light)? [y/N]: ").strip().lower()
    if another == "y":
        visual_traits_menu()

    print()
    input("Press Enter to exit.")

# ============================================================
# CR5 GLOW + CR9 PARTICLES & TAIL LIGHT
# ============================================================

STAT_GENES_CR5 = {
    "5A2": ("Friendliness", 4),
    "5A4": ("Enthusiasm",   4),
    "5B1": ("Intelligence", 4),
    "5B2": ("Intelligence", 2),
    "5B3": ("Friendliness", 3),
    "5B4": ("Ferocity",     1),
    "5C2": ("Toughness",    7),
}

GLOW_ON_PATTERNS = {
    "oooooXXXXo",
    "oooooXXooo",
    "oooooXXoXo",
    "oooooXoXoo",
}

PARTICLE_LOOKUP = {
    "XXXXXooXXX": "Tail",
    "XXXXXoXoXX": "Tail",
    "XXXXXXooXX": "Tail",
    "XXXXoooXXX": "Tail",
    "XXXoXoXoXo": "Tail",
    "XXXoXooXXX": "Tail",
    "XXXoXoooXX": "Tail",
    "XXXoooooXX": "Tail",
    "XXoXXoooXX": "Tail",
    "XXooXoooоX": "Tail",
    "XoXXXoooXX": "Tail",
    "XooXXXXXXX": "Wing",
    "oXoXXXXXXX": "Wing",
    "ooXXXXXXXX": "Wing",
}

TAILLIGHT_LOOKUP = {
    "oXXooXooXo": ["Wave Teal"],
    "oXXooooXoo": ["Poison Green"],
    "XXoooXoooo": ["Poison Green"],
    "ooXoXooooo": ["Poison Green"],
    "ooXXoXoXoo": ["Golden Yellow"],
    "ooXoXXoXoo": ["Golden Yellow"],
    "ooXoXoXXoo": ["Golden Yellow"],
    "ooXooXooXo": ["Golden Yellow"],
    "oXoooooXXo": ["Aqua Blue"],
    "XoXooXoXoo": ["Aqua Blue"],
    "ooXooooXoo": ["Aqua Blue"],
    "XoooXooXXX": ["Aqua Blue"],
    "oooXXooXoo": ["Aqua Blue"],
    "oXooooXXXX": ["Red Orange"],
    "XoXoXXXXXX": ["Red Orange"],
    "oXXoXXXXoX": ["Firey Pink"],
    "XoXoXXXXXo": ["Firey Pink"],
    "XoXoXXXXoX": ["Firey Pink"],
    "ooXoooXXoo": ["Firey Pink"],
    "ooXooXoXoo": ["Firey Pink"],
    "XoXXXooXoo": ["Galaxy Purple"],
    "XoXoooooXo": ["Galaxy Purple"],
    "XoXooooooo": ["Galaxy Purple"],
    "ooXoXXXXXo": ["Galaxy Purple"],
    "ooXoXXXXoX": ["Galaxy Purple"],
    "ooXooXXXoo": ["Galaxy Purple"],
    "ooooooXXXo": ["Galaxy Purple"],
    "oXooooooXo": ["White/Purp/Teal"],
    "ooXooooooo": ["White/Purp/Teal"],
    "XXoooXooXo": ["White/Purp/Teal"],
    "XoXooXoooo": ["White/Purp/Teal"],
    "ooXoXXXXoo": ["White Frosty"],
    "ooXXoooXoo": ["White Noise"],
    "ooXoXooXoo": ["White Noise"],
    "ooXooooooX": ["White Noise"],
    "ooooooooXo": ["none"],
    "oXoooooXXX": ["none"],
    "oXooooXoXo": ["none"],
    "XoXooXoXXo": ["none"],
    "ooXooooXXo": ["none"],
    "ooXooooXoX": ["none"],
}


def normalize_str(raw, expected_len):
    cleaned = raw.replace(" ", "")
    if len(cleaned) != expected_len:
        return None, f"Expected {expected_len} positions, got {len(cleaned)}."
    return "".join("o" if c.lower() in ("o", "r") else "X" for c in cleaned), None


def analyze_cr5(raw):
    norm, err = normalize_str(raw, 10)
    if err:
        return None, err
    labels_sizes = [("A", 4), ("B", 4), ("C", 2)]
    positions = {}
    idx = 0
    for label, size in labels_sizes:
        for pos in range(1, size + 1):
            positions[f"5{label}{pos}"] = norm[idx]
            idx += 1
    glow_on = norm in GLOW_ON_PATTERNS
    stat_totals = {}
    expressing = []
    not_expressing = []
    for coord, state in positions.items():
        if coord in STAT_GENES_CR5:
            stat_name, stat_val = STAT_GENES_CR5[coord]
            if state == "o":
                stat_totals[stat_name] = stat_totals.get(stat_name, 0) + stat_val
                expressing.append((coord, stat_name, stat_val))
            else:
                not_expressing.append((coord, stat_name, stat_val))
    return {"glow": glow_on, "norm": norm, "stat_totals": stat_totals,
            "expressing": expressing, "not_expressing": not_expressing}, None


def glow_on_paths(positions, norm):
    coords = [f"5{l}{p}" for l, sz in [("A",4),("B",4),("C",2)] for p in range(1, sz+1)]
    paths = []
    for target_norm in sorted(GLOW_ON_PATTERNS):
        flips = []
        net_stat = {}
        for i, coord in enumerate(coords):
            current, target = norm[i], target_norm[i]
            if current == target:
                continue
            direction = "recessive → dominant" if target == "X" else "dominant → recessive"
            stat_info = STAT_GENES_CR5.get(coord)
            if stat_info and stat_info[1] > 0:
                stat_name, stat_val = stat_info
                delta = stat_val if direction == "dominant → recessive" else -stat_val
                net_stat[stat_name] = net_stat.get(stat_name, 0) + delta
            flips.append({"coord": coord, "direction": direction, "stat": stat_info})
        net_total = sum(net_stat.values())
        paths.append({"target": target_norm, "flips_count": len(flips),
                      "net_total": net_total, "net_stat": net_stat, "flips": flips})
    by_speed = sorted(paths, key=lambda p: (p["flips_count"], -p["net_total"]))
    by_stat  = sorted(paths, key=lambda p: (-p["net_total"], p["flips_count"]))
    return by_speed, by_stat


def lookup_cr9(raw):
    norm, err = normalize_str(raw, 20)
    if err:
        return None, err
    particle_key = norm[:10]
    taillight_key = norm[10:]
    if particle_key in PARTICLE_LOOKUP:
        particle = PARTICLE_LOOKUP[particle_key]
    elif all(c == "X" for c in particle_key[:2]) and particle_key[8:10] == "XX":
        particle = "Tail"
    else:
        particle = "Unknown"
    tl_results = TAILLIGHT_LOOKUP.get(taillight_key, None)
    if tl_results is None:
        taillight = ["Unknown"]
    else:
        taillight = tl_results
    return {"particle": particle, "taillight": taillight}, None


def particle_paths(particle_key):
    """Find fewest flips to reach each particle type from current pattern."""
    by_type = {"Tail": [], "Wing": [], "None": []}
    for pattern, ptype in PARTICLE_LOOKUP.items():
        if ptype in by_type:
            by_type[ptype].append(pattern)
    coords = ["9A1","9A2","9A3","9A4","9B1","9B2","9B3","9B4","9C1","9C2"]
    results = {}
    for target_type, patterns in by_type.items():
        best = None
        for target_pattern in patterns:
            if len(target_pattern) != 10:
                continue
            flips = []
            for i, (c, t) in enumerate(zip(particle_key, target_pattern)):
                if c != t:
                    direction = "recessive → dominant" if t == "X" else "dominant → recessive"
                    flips.append({"coord": coords[i], "direction": direction})
            path = {"target": target_pattern, "flips_count": len(flips), "flips": flips}
            if best is None or len(flips) < best["flips_count"]:
                best = path
        results[target_type] = best
    return results


def visual_traits_menu():
    print()
    print("=" * 55)
    print("  Visual Traits — CR5 & CR9")
    print("=" * 55)
    print()
    print("CR5 — Glow (10 positions)")
    print("Enter genome string (spaces OK, o/R=recessive, else dominant):")
    cr5_raw = input("CR5 genome: ").strip()
    if cr5_raw:
        result, err = analyze_cr5(cr5_raw)
        if err:
            print(f"Error: {err}")
        else:
            print()
            print(f"Glow: {'ON' if result['glow'] else 'Off'}")
            print()
            print("CR5 stat contributions (recessive positions):")
            if result["expressing"]:
                for coord, stat_name, stat_val in sorted(result["expressing"]):
                    print(f"  {coord}: +{stat_val} {stat_name}")
                print("Totals from CR5:")
                for stat, total in sorted(result["stat_totals"].items()):
                    print(f"  {stat}: +{total}")
            else:
                print("  No stat genes expressing on CR5.")
            if result["not_expressing"]:
                print("Not expressing (dominant):")
                for coord, stat_name, stat_val in sorted(result["not_expressing"]):
                    print(f"  {coord}: {stat_val} {stat_name} (off)")

            if not result["glow"]:
                print()
                print("-" * 40)
                print("Paths to turn glow on:")
                by_speed, by_stat = glow_on_paths(result.get("positions", {}), result["norm"])

                def print_path(p, label):
                    flips = p["flips"]
                    net_total = p["net_total"]
                    sign = f"+{net_total}" if net_total >= 0 else str(net_total)
                    print(f"  {label}: {p['flips_count']} flip(s), net stat {sign}")
                    print(f"    Target: {p['target']}")
                    for f in flips:
                        coord = f["coord"]
                        direction = f["direction"]
                        stat_info = f["stat"]
                        if stat_info and stat_info[1] > 0:
                            stat_name, stat_val = stat_info
                            delta = stat_val if "dominant → recessive" in direction else -stat_val
                            sign2 = "+" if delta > 0 else ""
                            print(f"    {coord}: {direction} -> {sign2}{delta} {stat_name}")
                        else:
                            print(f"    {coord}: {direction} -> cosmetic")
                    if p["net_stat"]:
                        for stat, delta in sorted(p["net_stat"].items()):
                            sign2 = "+" if delta > 0 else ""
                            print(f"    Total {stat}: {sign2}{delta}")

                fastest = by_speed[0]
                best = by_stat[0]
                print()
                print("  --- Fewest flips ---")
                print_path(fastest, "Fastest")
                if best["target"] != fastest["target"]:
                    print()
                    print("  --- Best stat outcome ---")
                    print_path(best, "Best stat")
                else:
                    print("  (Fastest path is also the best stat outcome)")
                remaining = [p for p in by_speed[1:] if p["target"] != best["target"]]
                if remaining:
                    print()
                    print("  --- Other options ---")
                    for p in remaining:
                        print_path(p, f"Pattern {p['target']}")

    print()
    print("-" * 55)
    print("CR9 — Particles & Tail Light (20 positions)")
    print("Enter genome string (spaces OK):")
    cr9_raw = input("CR9 genome: ").strip()
    if cr9_raw:
        result, err = lookup_cr9(cr9_raw)
        if err:
            print(f"Error: {err}")
        else:
            print()
            p = result["particle"]
            print(f"Particles: {p}")
            tl = result["taillight"]
            if tl == ["Unknown"]:
                print("Tail light: Unknown")
                print("  Pattern not in research data. Share with Kaskrim if confirmed.")
            elif len(tl) > 1:
                print(f"Tail light: AMBIGUOUS — {' or '.join(tl)}")
                print("  Needs more data. If you can confirm the color, share with Kaskrim.")
            else:
                print(f"Tail light: {tl[0]}")

            # Particle path recommendations
            norm_cr9, _ = normalize_str(cr9_raw, 20)
            if norm_cr9:
                particle_key = norm_cr9[:10]
                print()
                print("Target particle type (Tail / Wing / None, or Enter to skip):")
                target_p = input("Target: ").strip().capitalize()
                if target_p in ("Tail", "Wing", "None"):
                    if target_p == p:
                        print(f"Already {target_p} particles — no flips needed.")
                    else:
                        paths = particle_paths(particle_key)
                        best = paths.get(target_p)
                        if best is None or not best["flips"]:
                            if target_p == "None":
                                print("No-particle states are achievable but the research data in this app doesn't yet include documented patterns to aim for.")
                            else:
                                print(f"No known pattern for {target_p} in research data.")
                        else:
                            print(f"Fewest flips to {target_p}: {best['flips_count']} flip(s)")
                            print(f"  Target pattern: {best['target']}")
                            for f in best["flips"]:
                                print(f"  {f['coord']}: {f['direction']}")
    print()
    input("Press Enter to return.")

if __name__ == "__main__":
    main()
