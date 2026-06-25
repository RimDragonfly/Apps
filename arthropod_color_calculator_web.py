"""
Arthropod Color Calculator — Streamlit Web Version
Project Gorgon Genetics Research — Kaskrim & Azizah
Compiled by AI Lumière

Run locally:  streamlit run arthropod_color_calculator_web.py
Host on:      Streamlit Community Cloud (streamlit.io)
"""

import streamlit as st

# ============================================================
# GENE MAPS
# ============================================================

LOCKED_DOMINANT_CR1 = {"1F2", "1G3", "1I1", "1I2", "1I4"}
LOCKED_DOMINANT_CR3 = {"3F3", "3G3", "3G4", "3I2", "3I3", "3I4"}

STAT_GENES_CR1 = {
    "1A2": ("Toughness", 2),
    "1B1": ("Friendliness", 3),
    "1B2": ("Ruggedness", 5),
    "1B3": ("Ferocity", 5),
    "1C1": ("Enthusiasm", 4),
    "1C2": ("Virility", 3),
    "1D1": ("Toughness", 3),
    "1E2": ("Intelligence", 3),
    "1E3": ("Enthusiasm", 5),
    "1F1": ("Intelligence", 4),
    "1F3": ("Virility", 2),
    "1F4": ("Ruggedness", 5),
    "1G1": ("Enthusiasm", 5),
    "1G2": ("Toughness", 6),
    "1H1": ("Friendliness", 5),
    "1H3": ("Ferocity", 3),
    "1H4": ("Ruggedness", 3),
    "1J1": ("Virility", 5),
    "1J2": ("Intelligence", 3),
}

STAT_GENES_CR3 = {
    "3C1": ("Ruggedness", 6),
    "3C2": ("Enthusiasm", 1),
    "3E1": ("Toughness", 3),
    "3E3": ("Intelligence", 4),
    "3E4": ("Ruggedness", 4),
    "3F2": ("Toughness", 5),
    "3G1": ("Ferocity", 2),
    "3G2": ("Virility", 4),
    "3H2": ("Friendliness", 4),
    "3H3": ("Friendliness", 3),
    "3J1": ("Ferocity", 3),
    "3J4": ("Intelligence", 7),
}

COLOR_LADDER_CR1 = {
    "Red":         (7,  9),
    "Yellow-green": (10, 10),
    "Green-yellow":  (10, 10),
    "Orange":      (11, 13),
    "Orange":        (11, 13),
    "Green":       (11, 13),
    
    "Blue":        (14, 16),
    "Blue-violet": (17, 17),
    "Teal":  (17, 19),
    "Purple":      (17, 19),
}

COLOR_LADDER_CR3 = {
    "Red":         (10, 10),
    "Orange":      (11, 13),
    "Orange":        (11, 13),
    "Green":       (9,  13),
    
    "Blue":        (14, 16),
    "Blue-violet": (15, 17),
    "Purple":      (17, 19),
}

LABELS = list("ABCDEFGHIJ")

# ============================================================
# CORE LOGIC
# ============================================================

def parse_genome(raw, chromosome):
    cleaned = raw.replace(" ", "")
    if len(cleaned) != 40:
        return None, f"Expected 40 positions, got {len(cleaned)}. Check input."
    unknown = sum(1 for c in cleaned if c == "?")
    if unknown > 0:
        return None, (f"Genome contains {unknown} unknown position(s) marked as '?'. "
                      f"This tool requires Genetics skill uncapped at level 100 so all "
                      f"positions are visible. Unknown genes cannot be read correctly.")
    positions = {}
    for i, label in enumerate(LABELS):
        for pos in range(4):
            coord = f"{chromosome}{label}{pos+1}"
            state = cleaned[i*4 + pos]
            positions[coord] = state
    return positions, None

def is_dom(state):
    return state.lower() not in ("o", "r")

def fj_dom_count(positions, cr):
    return sum(1 for label in "FGHIJ" for pos in range(1,5)
               if is_dom(positions.get(f"{cr}{label}{pos}", "o")))

def ae_dom_count(positions, cr):
    return sum(1 for label in "ABCDE" for pos in range(1,5)
               if is_dom(positions.get(f"{cr}{label}{pos}", "o")))

def detect_color(fj, ae, cr):
    if fj >= 17:
        if ae >= 7: return "Teal"
        elif ae >= 4: return "Blue-violet"
        else: return "Purple"
    if fj in (14, 15, 16):
        return "Teal" if ae >= 5 else "Blue"
    if fj == 10:
        return "Green-yellow" if ae >= 4 else "Yellow-green"
    if fj == 9:
        if cr == 3:
            return "Green" if ae <= 4 else "Orange"
        else:  # CR1
            if ae <= 4: return "Green"
            elif ae <= 8: return "Yellow"
            else: return "Orange"
    if fj in (11, 12, 13):
        if ae <= 2:
            return "Teal" if fj in (12, 13) else "Green"
        elif ae <= 4:
            return "Green"
        elif ae <= 8:
            return "Yellow"
        else:
            return "Orange"
    if fj <= 8:
        return "Red"
    ladder = COLOR_LADDER_CR1 if cr == 1 else COLOR_LADDER_CR3
    min_fj = min(lo for lo, hi in ladder.values())
    if fj < min_fj:
        return "Below ladder — possible counterclockwise approach to violet/purple"
    return "Unknown"

def get_candidates(positions, cr, direction):
    """Get eligible F-J positions for flipping in a given direction."""
    locked = LOCKED_DOMINANT_CR1 if cr == 1 else LOCKED_DOMINANT_CR3
    stat_genes = STAT_GENES_CR1 if cr == 1 else STAT_GENES_CR3
    candidates = []
    for label in "FGHIJ":
        for pos in range(1, 5):
            coord = f"{cr}{label}{pos}"
            if coord not in positions: continue
            if coord in locked: continue
            state = positions[coord]
            if direction == "recessive → dominant" and is_dom(state): continue
            if direction == "dominant → recessive" and not is_dom(state): continue
            is_stat = coord in stat_genes
            stat_name = stat_genes[coord][0] if is_stat else None
            stat_val = stat_genes[coord][1] if is_stat else 0
            candidates.append((coord, is_stat, stat_name, stat_val))
    candidates.sort(key=lambda x: (x[1], x[3]))
    return candidates

def calc_cost(selected, direction):
    """Calculate total stat cost for a set of changes.
    For arthropods: stats express at recessive (o).
    recessive → dominant = stat turns OFF = loss (negative)
    dominant → recessive = stat turns ON = gain (positive)
    """
    cost = {}
    for coord, is_stat, stat_name, stat_val in selected:
        if is_stat and stat_val > 0:
            delta = stat_val if direction == "dominant → recessive" else -stat_val
            cost[stat_name] = cost.get(stat_name, 0) + delta
    return cost

def calculate_changes(positions, cr, target_color):
    ladder = COLOR_LADDER_CR1 if cr == 1 else COLOR_LADDER_CR3
    target_lo, target_hi = ladder[target_color]
    current_fj = fj_dom_count(positions, cr)

    if target_lo <= current_fj <= target_hi:
        return "already_there", None, None

    results = {}

    # --- Path A: direct (counterclockwise if going down, clockwise if going up) ---
    if current_fj < target_lo:
        dir_a = "recessive → dominant"
        needed_a = target_lo - current_fj
    else:
        dir_a = "dominant → recessive"
        needed_a = current_fj - target_hi

    cands_a = get_candidates(positions, cr, dir_a)
    selected_a = cands_a[:needed_a]
    cost_a = calc_cost(selected_a, dir_a)
    pts_a = sum(abs(v) for v in cost_a.values())
    results["path_a"] = {
        "label": "Direct path",
        "direction": dir_a,
        "needed": needed_a,
        "selected": selected_a,
        "cost": cost_a,
        "pts": pts_a,
        "feasible": len(selected_a) >= needed_a,
    }

    # --- Path B: clockwise wrap to red (only when target is Red and current_fj is high) ---
    if target_color == "Red" and current_fj > target_hi:
        dir_b = "recessive → dominant"
        # Flip all remaining recessive F-J positions to dominant — wraps around to red
        cands_b = get_candidates(positions, cr, dir_b)
        needed_b = len(cands_b)  # flip everything recessive in F-J
        selected_b = cands_b
        cost_b = calc_cost(selected_b, dir_b)
        pts_b = sum(abs(v) for v in cost_b.values())
        results["path_b"] = {
            "label": "Clockwise wrap",
            "direction": dir_b,
            "needed": needed_b,
            "selected": selected_b,
            "cost": cost_b,
            "pts": pts_b,
            "feasible": True,
        }

    return "paths", results, target_color

# ============================================================
# STREAMLIT UI
# ============================================================


def parse_full_export(text):
    """Parse a full game genome export and extract relevant chromosomes.
    Returns dict: {cr_number: normalized_string} for CRs 1, 3, 5, 9.
    Also handles raw single-chromosome strings (passes through).
    Game export notation: D=dominant, R=recessive, x=mixed
    Converted to app notation: D->X, R->o, x->X (mixed counts as dominant for hue)
    """
    lines = text.strip().splitlines()

    # Check if this looks like a full export (has [Genes] or lines with NN= format)
    gene_lines = {}
    in_genes = False
    for line in lines:
        line = line.strip()
        if line == "[Genes]":
            in_genes = True
            continue
        if line.startswith("[") and line != "[Genes]":
            in_genes = False
            continue
        if in_genes or "=" in line:
            # Try to parse lines like "01= DRxx RRRR ..."
            import re
            m = re.match(r"^(\d+)\s*=\s*(.+)$", line)
            if m:
                cr_num = int(m.group(1))
                raw_genes = m.group(2).replace(" ", "")
                # Convert D/R/x to X/o/X notation
                converted = ""
                for c in raw_genes:
                    if c.upper() == "D":
                        converted += "X"
                    elif c.upper() == "R":
                        converted += "o"
                    elif c.lower() == "x":
                        converted += "X"  # mixed counts as dominant for hue
                    else:
                        converted += c
                gene_lines[cr_num] = converted

    if not gene_lines:
        # Not a full export — return None so caller handles as raw string
        return None

    result = {}
    for cr in [1, 3, 5, 9]:
        if cr in gene_lines:
            result[cr] = gene_lines[cr]
    return result

def show_glow_path(path, label):
    """Display a CR5 glow flip path with stat notes in Streamlit."""
    flips = path["flips"]
    net = path["net_stat"]
    net_total = path["net_total"]
    if not flips:
        st.success(f"**{label}:** Already matches a glow-on pattern — no flips needed.")
        return
    if net_total > 0:
        summary = f"{path['flips_count']} flip(s) — 🟢 net +{net_total} stat points"
    elif net_total < 0:
        summary = f"{path['flips_count']} flip(s) — 🔴 net {net_total} stat points"
    else:
        summary = f"{path['flips_count']} flip(s) — no net stat change"
    st.markdown(f"**{label}:** {summary}")
    st.caption(f"Target pattern: `{path['target']}`")
    for f in flips:
        coord = f["coord"]
        direction = f["direction"]
        stat_info = f["stat"]
        if stat_info and stat_info[1] > 0:
            stat_name, stat_val = stat_info
            delta = stat_val if "dominant → recessive" in direction else -stat_val
            sign = "+" if delta > 0 else ""
            icon = "🟢" if delta > 0 else "🔴"
            st.markdown(f"  `{coord}` {direction} → {icon} {sign}{delta} {stat_name}")
        else:
            st.markdown(f"  `{coord}` {direction} → cosmetic")
    if net:
        for stat, delta in sorted(net.items()):
            sign = "+" if delta > 0 else ""
            icon = "🟢" if delta > 0 else "🔴"
            st.markdown(f"  {icon} **{stat}:** {sign}{delta}")


def show_cr9_path(path, label):
    """Display a CR9 flip path with stat notes in Streamlit."""
    if path is None or not path["flips"]:
        return
    flips = path["flips"]
    net_total = path["net_total"]
    net_stat = path["net_stat"]
    if net_total > 0:
        summary = f"{len(flips)} flip(s) — 🟢 net +{net_total} stat points"
    elif net_total < 0:
        summary = f"{len(flips)} flip(s) — 🔴 net {net_total} stat points"
    else:
        summary = f"{len(flips)} flip(s) — no net stat change"
    st.markdown(f"**{label}:** {summary}")
    st.caption(f"Target pattern: `{path['target']}`")
    for f in flips:
        coord = f["coord"]
        direction = f["direction"]
        stat_info = STAT_GENES_CR9.get(coord)
        if stat_info and stat_info[1] > 0:
            stat_name, stat_val = stat_info
            delta = stat_val if "dominant → recessive" in direction else -stat_val
            sign = "+" if delta > 0 else ""
            icon = "🟢" if delta > 0 else "🔴"
            st.markdown(f"  `{coord}` {direction} → {icon} {sign}{delta} {stat_name}")
        else:
            st.markdown(f"  `{coord}` {direction} → cosmetic")
    if net_stat:
        for stat, delta in sorted(net_stat.items()):
            sign = "+" if delta > 0 else ""
            icon = "🟢" if delta > 0 else "🔴"
            st.markdown(f"  {icon} **{stat}:** {sign}{delta}")


STAT_GENES_CR5 = {
    "5A2": ("Friendliness", 4),
    "5A4": ("Enthusiasm",   4),
    "5B1": ("Intelligence", 4),
    "5B2": ("Intelligence", 2),
    "5B3": ("Friendliness", 3),
    "5B4": ("Ferocity",     1),
    "5C2": ("Toughness",    7),
}

# CR9 stat gene map (positions A1-E4, 20 positions)
# Source: arthropod-stat-genome-v2.txt
STAT_GENES_CR9 = {
    "9A1": ("Toughness",     2),
    "9A3": ("Virility",      4),
    "9A4": ("Toughness",     2),
    "9B2": ("Ferocity",      4),
    "9B3": ("Ferocity",      1),
    "9B4": ("Enthusiasm",    4),
    "9C2": ("Friendliness",  7),
    "9D1": ("Friendliness",  2),
    "9D2": ("Ruggedness",    4),
    "9D4": ("Enthusiasm",    3),
    "9E1": ("Intelligence",  5),
    "9E4": ("Virility",      5),
}
# A2, B1, C1, C3, C4, D3, E2, E3 are cosmetic (_)

# CR5 glow-on patterns (normalized, 10 chars)
# Anything not in this set = glow off
GLOW_ON_PATTERNS = {
    "oooooXXXXo",  # glow on
    "oooooXXooo",  # glow on
    "oooooXXoXo",  # glow on
    "oooooXoXoo",  # glow on
}

# ---- CR9 PARTICLE LOOKUP ----
# Uses first 10 positions of CR9 (A1-A4, B1-B4, C1-C2)
# Key: 10-char normalized string
# Value: "Tail" | "Wing" | "None"
PARTICLE_LOOKUP = {
    # Tail particles
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
    # Wing particles
    "XooXXXXXXX": "Wing",
    "oXoXXXXXXX": "Wing",
    "ooXXXXXXXX": "Wing",
    # No particles
    "XooooooooX": "None",
    "XXXXXXXXXX": "None",
}

# ---- CR9 TAIL LIGHT LOOKUP ----
# Uses last 10 positions of CR9 (C3-C4, D1-D4, E1-E4)
# Key: 10-char normalized string
# Value: color name string
# Tail light lookup: key -> list of possible colors
# Source: Kaskrim raw data, correctly parsed
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

def normalize_genome_str(raw, expected_len):
    """Normalize a genome string to o/X notation, strip spaces."""
    cleaned = raw.replace(" ", "")
    if len(cleaned) != expected_len:
        return None, f"Expected {expected_len} positions, got {len(cleaned)}."
    result = ""
    for c in cleaned:
        if c.lower() in ("o", "r"):
            result += "o"
        else:
            result += "X"
    return result, None

def analyze_cr5(raw):
    """Parse CR5, determine glow on/off, and calculate stat contributions."""
    norm, err = normalize_genome_str(raw, 10)
    if err:
        return None, err

    labels_sizes = [("A", 4), ("B", 4), ("C", 2)]
    positions = {}
    idx = 0
    for label, size in labels_sizes:
        for pos in range(1, size + 1):
            coord = f"5{label}{pos}"
            positions[coord] = norm[idx]
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

    return {
        "glow": glow_on,
        "norm": norm,
        "positions": positions,
        "stat_totals": stat_totals,
        "expressing": expressing,
        "not_expressing": not_expressing,
    }, None

def glow_on_paths(positions, norm):
    """Calculate paths to reach each known glow-on pattern from current CR5 state.
    Returns list of path dicts sorted by (flips_needed, net_stat_loss).
    Only positions that differ between current and target are flipped.
    CR5 has no locked positions so all flips are always available.
    """
    coords = [f"5{l}{p}" for l, sz in [("A",4),("B",4),("C",2)] for p in range(1, sz+1)]

    paths = []
    for target_norm in sorted(GLOW_ON_PATTERNS):
        flips = []
        net_stat = {}  # stat_name -> delta (positive = gain, negative = loss)
        for i, coord in enumerate(coords):
            current = norm[i]
            target  = target_norm[i]
            if current == target:
                continue
            # This position needs to flip
            direction = "recessive → dominant" if target == "X" else "dominant → recessive"
            stat_info = STAT_GENES_CR5.get(coord)
            if stat_info:
                stat_name, stat_val = stat_info
                if stat_val > 0:
                    # dominant→recessive = stat turns ON = gain
                    # recessive→dominant = stat turns OFF = loss
                    delta = stat_val if direction == "dominant → recessive" else -stat_val
                    net_stat[stat_name] = net_stat.get(stat_name, 0) + delta
            flips.append({"coord": coord, "direction": direction, "stat": stat_info})

        total_loss = sum(v for v in net_stat.values() if v < 0)
        total_gain = sum(v for v in net_stat.values() if v > 0)
        paths.append({
            "target": target_norm,
            "flips": flips,
            "flips_count": len(flips),
            "net_stat": net_stat,
            "total_loss": total_loss,
            "total_gain": total_gain,
            "net_total": total_gain + total_loss,  # combined net (loss is negative)
        })

    # Sort by fewest flips, then by best net stat (highest net = least loss / most gain)
    paths_by_speed = sorted(paths, key=lambda p: (p["flips_count"], -p["net_total"]))
    paths_by_stat  = sorted(paths, key=lambda p: (-p["net_total"], p["flips_count"]))
    return paths_by_speed, paths_by_stat


def lookup_cr9(raw):
    norm, err = normalize_genome_str(raw, 20)
    if err:
        return None, err
    particle_key = norm[:10]
    taillight_key = norm[10:]

    # Particle result
    if particle_key in PARTICLE_LOOKUP:
        particle = PARTICLE_LOOKUP[particle_key]
    else:
        particle = "Unknown"

    # Tail light result — returns a list; multiple entries = ambiguous
    taillight_results = TAILLIGHT_LOOKUP.get(taillight_key, None)
    if taillight_results is None:
        taillight = ["Unknown"]
        ambiguous = False
    else:
        taillight = taillight_results
        ambiguous = len(taillight_results) > 1

    return {"particle": particle, "taillight": taillight, "taillight_ambiguous": ambiguous}, None


def _calc_flip_stats(flips, stat_genes):
    """Calculate net stat change for a list of flips.
    recessive→dominant = stat OFF = negative delta
    dominant→recessive = stat ON = positive delta
    """
    net = {}
    for f in flips:
        coord = f["coord"]
        if coord in stat_genes:
            stat_name, stat_val = stat_genes[coord]
            if stat_val > 0:
                delta = stat_val if "dominant → recessive" in f["direction"] else -stat_val
                net[stat_name] = net.get(stat_name, 0) + delta
    return net




def _build_paths(current_key, target_patterns, coords, stat_genes):
    """Build all paths from current_key to each target pattern, return (fastest, best_stat)."""
    all_paths = []
    for target_pattern in target_patterns:
        if len(target_pattern) != len(current_key):
            continue
        flips = []
        for i, (c, t) in enumerate(zip(current_key, target_pattern)):
            if c != t:
                direction = "recessive → dominant" if t == "X" else "dominant → recessive"
                flips.append({"coord": coords[i], "direction": direction})
        net_stat = _calc_flip_stats(flips, stat_genes)
        net_total = sum(net_stat.values())
        all_paths.append({
            "target": target_pattern,
            "flips_count": len(flips),
            "flips": flips,
            "net_stat": net_stat,
            "net_total": net_total,
        })
    if not all_paths:
        return None, None
    fastest = min(all_paths, key=lambda p: (p["flips_count"], -p["net_total"]))
    best_stat = min(all_paths, key=lambda p: (-p["net_total"], p["flips_count"]))
    return fastest, best_stat


def particle_paths(particle_key):
    """For each known particle location, return (fastest, best_stat) path dicts."""
    by_type = {"Tail": [], "Wing": [], "None": []}
    for pattern, ptype in PARTICLE_LOOKUP.items():
        if ptype in by_type:
            by_type[ptype].append(pattern)
    coords = ["9A1","9A2","9A3","9A4","9B1","9B2","9B3","9B4","9C1","9C2"]
    results = {}
    for target_type, patterns in by_type.items():
        fastest, best_stat = _build_paths(particle_key, patterns, coords, STAT_GENES_CR9)
        results[target_type] = {"fastest": fastest, "best_stat": best_stat}
    return results


def taillight_paths(taillight_key):
    """For each known tail light color, return (fastest, best_stat) path dicts."""
    by_color = {}
    for pattern, colors in TAILLIGHT_LOOKUP.items():
        for color in colors:
            by_color.setdefault(color, []).append(pattern)
    coords = ["9C3","9C4","9D1","9D2","9D3","9D4","9E1","9E2","9E3","9E4"]
    results = {}
    for target_color, patterns in by_color.items():
        fastest, best_stat = _build_paths(taillight_key, patterns, coords, STAT_GENES_CR9)
        results[target_color] = {"fastest": fastest, "best_stat": best_stat}
    return results


# ============================================================
# UI — Arthropod Visual Trait Calculator
# ============================================================

st.set_page_config(
    page_title="Arthropod Visual Trait Calculator",
    page_icon="🐝",
    layout="centered"
)

st.title("🐝 Arthropod Visual Trait Calculator")
st.caption("Project Gorgon Genetics Research · Kaskrim & Azizah · Lumière")
st.markdown("Calculate your bee or wasp's current visual traits and get flip instructions to change them.")
st.warning("⚠️ **Genetics skill must be uncapped at level 100.** Do not use this tool with genomes containing ? marks.")

# ── SECTION 1: Genome Input ───────────────────────────────────────────────
st.divider()
st.header("📋 Your Genome")

full_export_input = st.text_area(
    "Paste your full genome export here",
    placeholder="Paste everything — starting from [Overview] or [Genes] — and click Parse it.",
    height=150,
    key="full_export_input",
    label_visibility="visible"
)

if st.button("📋 Parse it", type="primary", key="parse_btn"):
    if full_export_input.strip():
        parsed = parse_full_export(full_export_input.strip())
        if parsed:
            # Clear all chromosome fields first so stale values don't carry over
            for key in ["export_cr1", "export_cr3", "cr5_input", "cr9_input"]:
                st.session_state[key] = ""
            if parsed.get(1): st.session_state["export_cr1"] = parsed[1]
            if parsed.get(3): st.session_state["export_cr3"] = parsed[3]
            if parsed.get(5): st.session_state["cr5_input"] = parsed[5]
            if parsed.get(9): st.session_state["cr9_input"] = parsed[9]
            st.success(f"✅ Parsed — found: {', '.join(f'CR{k}' for k in sorted(parsed.keys()))}")
            st.rerun()
        else:
            st.warning("Doesn't look like a full export. Use the individual fields below.")
    else:
        st.warning("Paste your genome export above first.")

with st.expander("Or enter individual chromosome strings"):
    _cr1_pre = st.session_state.get("export_cr1", "")
    _cr3_pre = st.session_state.get("export_cr3", "")
    ind_cr1 = st.text_input("CR1 — Body color (40 positions)", value=_cr1_pre, placeholder="e.g. DRDDRRRR...")
    ind_cr3 = st.text_input("CR3 — Wing color (40 positions)", value=_cr3_pre, placeholder="e.g. RRRRDRRR...")
    ind_cr5 = st.text_input("CR5 — Glow (10 positions)", key="cr5_input", placeholder="e.g. RRRR RDxR DR")
    ind_cr9 = st.text_input("CR9 — Particles & Tail Light (20 positions)", key="cr9_input", placeholder="e.g. DDxD DRxR xDRR DRRR RRRR")
    if ind_cr1: st.session_state["export_cr1"] = ind_cr1
    if ind_cr3: st.session_state["export_cr3"] = ind_cr3

# Resolve inputs
cr1_raw = st.session_state.get("export_cr1", "").strip()
cr3_raw = st.session_state.get("export_cr3", "").strip()
cr5_raw = st.session_state.get("cr5_input", "").strip()
cr9_raw = st.session_state.get("cr9_input", "").strip()

# Parse what we have
cr1_data = cr3_data = cr5_data = cr9_data = None
cr1_err = cr3_err = cr5_err = cr9_err = None

if cr1_raw:
    _pos, _err = parse_genome(cr1_raw, 1)
    if _err: cr1_err = _err
    else: cr1_data = {"positions": _pos, "fj": fj_dom_count(_pos, 1), "ae": ae_dom_count(_pos, 1)}
    if cr1_data: cr1_data["color"] = detect_color(cr1_data["fj"], cr1_data["ae"], 1)

if cr3_raw:
    _pos, _err = parse_genome(cr3_raw, 3)
    if _err: cr3_err = _err
    else: cr3_data = {"positions": _pos, "fj": fj_dom_count(_pos, 3), "ae": ae_dom_count(_pos, 3)}
    if cr3_data: cr3_data["color"] = detect_color(cr3_data["fj"], cr3_data["ae"], 3)

if cr5_raw:
    _res, _err = analyze_cr5(cr5_raw)
    if _err: cr5_err = _err
    else: cr5_data = _res

if cr9_raw:
    _res, _err = lookup_cr9(cr9_raw)
    if _err: cr9_err = _err
    else: cr9_data = _res

# ── SECTION 2: Current Traits Summary ────────────────────────────────────
if any([cr1_data, cr3_data, cr5_data, cr9_data]):
    st.divider()
    st.header("🐝 Your Bee — Current Traits")

    cols = st.columns(2)
    with cols[0]:
        if cr1_data:
            st.metric("Body color (CR1)", cr1_data["color"])
            st.caption(f"F-J: {cr1_data['fj']}/20 · A-E: {cr1_data['ae']}/20")
        else:
            st.metric("Body color (CR1)", "—")
        if cr5_data:
            glow_label = "✨ ON" if cr5_data["glow"] else "Off"
            st.metric("Glow (CR5)", glow_label)
        else:
            st.metric("Glow (CR5)", "—")
    with cols[1]:
        if cr3_data:
            st.metric("Wing color (CR3)", cr3_data["color"])
            st.caption(f"F-J: {cr3_data['fj']}/20 · A-E: {cr3_data['ae']}/20")
        else:
            st.metric("Wing color (CR3)", "—")
        if cr9_data:
            st.metric("Particles (CR9)", cr9_data["particle"])
            tl = cr9_data["taillight"]
            tl_label = " or ".join(tl) if cr9_data["taillight_ambiguous"] else (tl[0] if tl != ["Unknown"] else "Unknown")
            st.metric("Tail light (CR9)", tl_label)
        else:
            st.metric("Particles (CR9)", "—")
            st.metric("Tail light (CR9)", "—")

# ── SECTION 3: Change Body Color (CR1) ───────────────────────────────────
if cr1_data:
    st.divider()
    st.header("🎨 Change Body Color (CR1)")
    if cr1_err:
        st.error(f"⚠️ {cr1_err}")
    else:
        ladder = COLOR_LADDER_CR1
        target_color_cr1 = st.selectbox("Target body color", options=list(ladder.keys()), key="target_cr1")
        if st.button("Get flip instructions", key="run_cr1", type="primary"):
            status, paths, _ = calculate_changes(cr1_data["positions"], 1, target_color_cr1)
            fj, ae = cr1_data["fj"], cr1_data["ae"]
            if status == "already_there":
                st.success(f"✅ Already in the **{target_color_cr1}** zone (F-J = {fj}).")
                # A-E guidance
                ae_guidance = None
                if fj >= 17:
                    if target_color_cr1 == "Purple":      ae_guidance = ("below 4",   "ae_decrease", 4)
                    elif target_color_cr1 == "Blue-violet": ae_guidance = ("4 to 6",   "ae_range", (4,6))
                    elif target_color_cr1 == "Teal":       ae_guidance = ("7 or more", "ae_increase", 7)
                elif fj in (14,15,16):
                    if target_color_cr1 == "Blue":  ae_guidance = ("below 5",   "ae_decrease", 5)
                    elif target_color_cr1 == "Teal": ae_guidance = ("5 or more", "ae_increase", 5)
                elif fj in (11,12,13):
                    if target_color_cr1 == "Green":  ae_guidance = ("3 to 4",    "ae_range", (3,4))
                    elif target_color_cr1 == "Yellow": ae_guidance = ("5 to 8",   "ae_range", (5,8))
                    elif target_color_cr1 == "Orange": ae_guidance = ("9 or more","ae_increase", 9)
                elif fj == 9:
                    if target_color_cr1 == "Green":  ae_guidance = ("4 or below","ae_decrease", 4)
                    elif target_color_cr1 == "Yellow": ae_guidance = ("5 to 8",   "ae_range", (5,8))
                    elif target_color_cr1 == "Orange": ae_guidance = ("9 or more","ae_increase", 9)
                if ae_guidance:
                    label, direction, threshold = ae_guidance
                    if direction == "ae_increase":
                        needed = max(0, threshold - ae)
                        if needed > 0:
                            st.info(f"A-E is currently **{ae}/20**. To reach **{target_color_cr1}**, you need A-E **{label}** — flip **{needed} more A-E position(s) to dominant**.")
                        else:
                            st.success(f"A-E is {ae} — already in the {target_color_cr1} range.")
                    elif direction == "ae_decrease":
                        needed = max(0, ae - (threshold - 1))
                        if needed > 0:
                            st.info(f"A-E is currently **{ae}/20**. To reach **{target_color_cr1}**, you need A-E **{label}** — flip **{needed} A-E position(s) to recessive**.")
                        else:
                            st.success(f"A-E is {ae} — already in the {target_color_cr1} range.")
                    elif direction == "ae_range":
                        lo, hi = threshold
                        if ae < lo:
                            st.info(f"A-E is currently **{ae}/20**. To reach **{target_color_cr1}**, you need A-E **{label}** — flip **{lo-ae} more A-E position(s) to dominant**.")
                        elif ae > hi:
                            st.info(f"A-E is currently **{ae}/20**. To reach **{target_color_cr1}**, you need A-E **{label}** — flip **{ae-hi} A-E position(s) to recessive**.")
                        else:
                            st.success(f"A-E is {ae} — already in the {target_color_cr1} range.")
                else:
                    st.info(f"A-E is {ae}/20 — fine-tunes the exact shade within this zone.")
            else:
                def show_path(path, label):
                    direction = path["direction"]; needed = path["needed"]
                    selected = path["selected"]; cost = path["cost"]
                    pts = path["pts"]; feasible = path["feasible"]
                    if not feasible:
                        st.warning(f"⚠️ {label}: Only {len(selected)} eligible positions found.")
                        return
                    net = sum(cost.values())
                    if pts == 0: st.success(f"**{label}:** {needed} change(s) — 🟢 no stat cost")
                    elif net > 0: st.success(f"**{label}:** {needed} change(s) — 🟢 {pts} stat point(s) gained")
                    else: st.warning(f"**{label}:** {needed} change(s) — 🔴 {pts} stat point(s) lost")
                    st.markdown(f"*Direction: {direction}*")
                    for i, (coord, is_stat, stat_name, stat_val) in enumerate(selected):
                        if is_stat and stat_val > 0:
                            if direction == "dominant → recessive":
                                st.markdown(f"**{i+1}.** `{coord}` · gains **+{stat_val} {stat_name}**")
                            else:
                                st.markdown(f"**{i+1}.** `{coord}` · costs **−{stat_val} {stat_name}**")
                        else:
                            st.markdown(f"**{i+1}.** `{coord}` · cosmetic")
                    if cost:
                        for stat, delta in sorted(cost.items()):
                            sign = "+" if delta > 0 else ""
                            icon = "🟢" if delta > 0 else "🔴"
                            st.markdown(f"{icon} **{stat}:** {sign}{delta}")
                path_a = paths.get("path_a")
                path_b = paths.get("path_b")
                if path_b:
                    pts_a = path_a["pts"] if path_a else 999
                    pts_b = path_b["pts"]
                    if pts_a <= pts_b:
                        st.markdown("##### ✅ Recommended: Direct path")
                        show_path(path_a, path_a["label"])
                        st.divider()
                        st.markdown(f"##### Alternative: {path_b['label']}")
                        show_path(path_b, path_b["label"])
                    else:
                        st.markdown(f"##### ✅ Recommended: {path_b['label']}")
                        show_path(path_b, path_b["label"])
                        st.divider()
                        st.markdown("##### Alternative: Direct path")
                        show_path(path_a, path_a["label"])
                else:
                    show_path(path_a, path_a["label"])

# ── SECTION 4: Change Wing Color (CR3) ───────────────────────────────────
if cr3_data:
    st.divider()
    st.header("🪽 Change Wing Color (CR3)")
    if cr3_err:
        st.error(f"⚠️ {cr3_err}")
    else:
        ladder3 = COLOR_LADDER_CR3
        target_color_cr3 = st.selectbox("Target wing color", options=list(ladder3.keys()), key="target_cr3")
        if st.button("Get flip instructions", key="run_cr3", type="primary"):
            status, paths, _ = calculate_changes(cr3_data["positions"], 3, target_color_cr3)
            fj, ae = cr3_data["fj"], cr3_data["ae"]
            if status == "already_there":
                st.success(f"✅ Already in the **{target_color_cr3}** zone (F-J = {fj}).")
                ae_guidance = None
                if fj in (9,10,11,12,13):
                    if target_color_cr3 == "Green":  ae_guidance = ("4 or below","ae_decrease", 4)
                    elif target_color_cr3 == "Orange": ae_guidance = ("5 or more","ae_increase", 5)
                if ae_guidance:
                    label, direction, threshold = ae_guidance
                    if direction == "ae_increase":
                        needed = max(0, threshold - ae)
                        if needed > 0: st.info(f"A-E is **{ae}/20**. To reach **{target_color_cr3}**, need A-E **{label}** — flip **{needed} A-E position(s) to dominant**.")
                        else: st.success(f"A-E is {ae} — already in the {target_color_cr3} range.")
                    elif direction == "ae_decrease":
                        needed = max(0, ae - (threshold - 1))
                        if needed > 0: st.info(f"A-E is **{ae}/20**. To reach **{target_color_cr3}**, need A-E **{label}** — flip **{needed} A-E position(s) to recessive**.")
                        else: st.success(f"A-E is {ae} — already in the {target_color_cr3} range.")
                else:
                    st.info(f"A-E is {ae}/20 — fine-tunes the exact shade within this zone.")
            else:
                def show_path_cr3(path, label):
                    direction = path["direction"]; needed = path["needed"]
                    selected = path["selected"]; cost = path["cost"]
                    pts = path["pts"]; feasible = path["feasible"]
                    if not feasible:
                        st.warning(f"⚠️ {label}: Only {len(selected)} positions found.")
                        return
                    net = sum(cost.values())
                    if pts == 0: st.success(f"**{label}:** {needed} change(s) — 🟢 no stat cost")
                    elif net > 0: st.success(f"**{label}:** {needed} change(s) — 🟢 {pts} stat point(s) gained")
                    else: st.warning(f"**{label}:** {needed} change(s) — 🔴 {pts} stat point(s) lost")
                    st.markdown(f"*Direction: {direction}*")
                    for i, (coord, is_stat, stat_name, stat_val) in enumerate(selected):
                        if is_stat and stat_val > 0:
                            if direction == "dominant → recessive":
                                st.markdown(f"**{i+1}.** `{coord}` · gains **+{stat_val} {stat_name}**")
                            else:
                                st.markdown(f"**{i+1}.** `{coord}` · costs **−{stat_val} {stat_name}**")
                        else:
                            st.markdown(f"**{i+1}.** `{coord}` · cosmetic")
                    if cost:
                        for stat, delta in sorted(cost.items()):
                            sign = "+" if delta > 0 else ""
                            icon = "🟢" if delta > 0 else "🔴"
                            st.markdown(f"{icon} **{stat}:** {sign}{delta}")
                path_a = paths.get("path_a"); path_b = paths.get("path_b")
                if path_b:
                    if path_a["pts"] <= path_b["pts"]:
                        show_path_cr3(path_a, path_a["label"])
                        with st.expander("Alternative path"): show_path_cr3(path_b, path_b["label"])
                    else:
                        show_path_cr3(path_b, path_b["label"])
                        with st.expander("Alternative path"): show_path_cr3(path_a, path_a["label"])
                else:
                    show_path_cr3(path_a, path_a["label"])

# ── SECTION 5: Change Glow (CR5) ─────────────────────────────────────────
if cr5_data:
    st.divider()
    st.header("✨ Change Glow (CR5)")

    glow_on = cr5_data["glow"]
    current_norm = cr5_data["norm"]
    coords5 = [f"5{l}{p}" for l, sz in [("A",4),("B",4),("C",2)] for p in range(1, sz+1)]

    glow_choice = st.radio("I want glow:", ["On", "Off"], index=0 if glow_on else 1, horizontal=True, key="glow_choice")

    # Current CR5 stats
    with st.expander("Current CR5 stat contributions"):
        if cr5_data["expressing"]:
            for coord, stat_name, stat_val in sorted(cr5_data["expressing"]):
                st.markdown(f"  `{coord}` → +{stat_val} {stat_name}")
            for stat, total in sorted(cr5_data["stat_totals"].items()):
                st.markdown(f"  🟢 **{stat}:** +{total}")
        else:
            st.markdown("No stat genes expressing on CR5.")
        if cr5_data["not_expressing"]:
            for coord, stat_name, stat_val in sorted(cr5_data["not_expressing"]):
                st.markdown(f"  `{coord}` → {stat_val} {stat_name} (off)")

    if glow_choice == "On":
        if glow_on:
            # Already on — check for better-stat patterns
            WORST_GLOW_PATTERN = "oooooXXXXo"
            is_worst = current_norm == WORST_GLOW_PATTERN
            current_stat_total = sum(
                STAT_GENES_CR5[coord][1] for i, coord in enumerate(coords5)
                if current_norm[i] == "o" and coord in STAT_GENES_CR5 and STAT_GENES_CR5[coord][1] > 0
            )
            better_paths = []
            for target_norm in GLOW_ON_PATTERNS:
                if target_norm == current_norm: continue
                target_total = sum(
                    STAT_GENES_CR5[coord][1] for i, coord in enumerate(coords5)
                    if target_norm[i] == "o" and coord in STAT_GENES_CR5 and STAT_GENES_CR5[coord][1] > 0
                )
                if target_total > current_stat_total:
                    flips, net_stat = [], {}
                    for i, coord in enumerate(coords5):
                        c, t = current_norm[i], target_norm[i]
                        if c != t:
                            direction = "recessive → dominant" if t == "X" else "dominant → recessive"
                            stat_info = STAT_GENES_CR5.get(coord)
                            if stat_info and stat_info[1] > 0:
                                delta = stat_info[1] if "dominant → recessive" in direction else -stat_info[1]
                                net_stat[stat_info[0]] = net_stat.get(stat_info[0], 0) + delta
                            flips.append({"coord": coord, "direction": direction, "stat": stat_info})
                    better_paths.append({"target": target_norm, "flips": flips, "flips_count": len(flips),
                                         "net_stat": net_stat, "net_total": sum(net_stat.values())})
            if is_worst:
                st.warning("⚠️ Your current glow pattern has the lowest stat value of all known glow-on patterns — it costs both Ferocity and Friendliness. All other glow-on patterns are better.")
            if better_paths:
                best = max(better_paths, key=lambda p: p["net_total"])
                st.markdown(f"✨ Glow is already **ON** — but a better-stat pattern exists (+{best['net_total']} net stats):")
                show_glow_path(best, "Better stat option")
                if len(better_paths) > 1:
                    with st.expander(f"Other better options ({len(better_paths)-1} more)"):
                        for p in sorted(better_paths, key=lambda p: -p["net_total"])[1:]:
                            show_glow_path(p, f"Alternative ({p['flips_count']} flip(s))")
            else:
                st.success("✨ Glow is **ON** — current pattern already has the best stats among known glow-on patterns.")
        else:
            # Want on, currently off — show three paths
            FEROCITY_PATTERN    = "oooooXoXoo"
            FRIENDLINESS_PATTERN = "oooooXXoXo"
            paths_speed, _ = glow_on_paths(cr5_data["positions"], current_norm)
            fastest  = paths_speed[0]
            fe_path  = next((p for p in paths_speed if p["target"] == FEROCITY_PATTERN), None)
            fr_path  = next((p for p in paths_speed if p["target"] == FRIENDLINESS_PATTERN), None)
            st.markdown("##### ⚡ Shortest path to glow on")
            show_glow_path(fastest, "Shortest path")
            st.markdown("##### Path to −1 Ferocity glow")
            if fe_path and fe_path["flips_count"] == 0: st.success("Already on this pattern.")
            elif fe_path: show_glow_path(fe_path, f"{fe_path['flips_count']} flip(s)")
            else: st.info("No path available.")
            st.markdown("##### Path to −3 Friendliness glow")
            if fr_path and fr_path["flips_count"] == 0: st.success("Already on this pattern.")
            elif fr_path: show_glow_path(fr_path, f"{fr_path['flips_count']} flip(s)")
            else: st.info("No path available.")

    else:  # Glow Off
        if not glow_on:
            # Already off — check if stat improvement possible
            current_stat_total = sum(
                STAT_GENES_CR5[coord][1] for i, coord in enumerate(coords5)
                if current_norm[i] == "o" and coord in STAT_GENES_CR5 and STAT_GENES_CR5[coord][1] > 0
            )
            max_possible = sum(v[1] for v in STAT_GENES_CR5.values())
            if current_stat_total >= max_possible:
                st.success("🔘 Glow is **Off** — all CR5 stat genes already expressing.")
            else:
                off_flips, off_net = [], {}
                target_list = list(current_norm)
                for i, coord in enumerate(coords5):
                    if current_norm[i] == "X" and coord in STAT_GENES_CR5:
                        target_list[i] = "o"
                        stat_info = STAT_GENES_CR5[coord]
                        if stat_info[1] > 0:
                            off_net[stat_info[0]] = off_net.get(stat_info[0], 0) + stat_info[1]
                        off_flips.append({"coord": coord, "direction": "dominant → recessive", "stat": stat_info})
                off_target = "".join(target_list)
                if off_target in GLOW_ON_PATTERNS:
                    st.warning("⚠️ Flipping stat genes to recessive would result in a glow-on pattern. Additional cosmetic flip needed.")
                elif off_flips:
                    st.markdown("🔘 Glow is **Off** — but stat genes could be improved:")
                    off_path = {"target": off_target, "flips": off_flips, "flips_count": len(off_flips),
                                "net_stat": off_net, "net_total": sum(off_net.values())}
                    show_glow_path(off_path, f"Max stats glow-off ({len(off_flips)} flip(s))")
                else:
                    st.success("🔘 Glow is **Off** — all CR5 stat genes already expressing.")
        else:
            # Want off, currently on — flip stat genes to recessive
            off_flips, off_net = [], {}
            target_list = list(current_norm)
            for i, coord in enumerate(coords5):
                if current_norm[i] == "X" and coord in STAT_GENES_CR5:
                    target_list[i] = "o"
                    stat_info = STAT_GENES_CR5[coord]
                    if stat_info[1] > 0:
                        off_net[stat_info[0]] = off_net.get(stat_info[0], 0) + stat_info[1]
                    off_flips.append({"coord": coord, "direction": "dominant → recessive", "stat": stat_info})
            off_target = "".join(target_list)
            if off_target in GLOW_ON_PATTERNS:
                st.warning("⚠️ Flipping stat genes alone still results in a glow-on pattern. An additional cosmetic flip is needed.")
            elif not off_flips:
                st.success("All stat genes already recessive — glow is effectively off at max stats.")
            else:
                off_path = {"target": off_target, "flips": off_flips, "flips_count": len(off_flips),
                            "net_stat": off_net, "net_total": sum(off_net.values())}
                show_glow_path(off_path, f"Turn glow off — max stats ({len(off_flips)} flip(s))")

# ── SECTION 6: Change Particles & Tail Light (CR9) ───────────────────────
if cr9_data:
    st.divider()
    st.header("🐝 Change Particles & Tail Light (CR9)")
    norm_cr9, _ = normalize_genome_str(cr9_raw, 20)

    if norm_cr9:
        particle_key   = norm_cr9[:10]
        taillight_key  = norm_cr9[10:]

        col_p, col_t = st.columns(2)

        with col_p:
            st.subheader("Particle location")
            p = cr9_data["particle"]
            p_icon = {"Tail":"🐝","Wing":"🪽","None":"⬜","Unknown":"❓"}.get(p,"❓")
            st.markdown(f"**Current:** {p_icon} {p}")
            particle_options = ["Tail","Wing","None"]
            target_p = st.selectbox("Target particle location", options=particle_options,
                                    index=particle_options.index(p) if p in particle_options else 0,
                                    key="target_particle",
                                    format_func=lambda x: {"Tail":"🐝 Tail","Wing":"🪽 Wing","None":"⬜ None"}.get(x,x))
            if target_p == p:
                paths = particle_paths(particle_key)
                p_result = paths.get(target_p)
                best_stat = p_result["best_stat"] if p_result else None
                if best_stat and best_stat["flips_count"] > 0 and best_stat["net_total"] > 0:
                    st.markdown("📈 A better-stat pattern exists for this location:")
                    show_cr9_path(best_stat, "Better stat option")
                else:
                    st.success(f"Already {target_p} — optimal stats for this location.")
            else:
                if target_p == "None":
                    st.info("No-particle states are achievable but not yet documented in the research data.")
                else:
                    paths = particle_paths(particle_key)
                    p_result = paths.get(target_p)
                    fastest = p_result["fastest"] if p_result else None
                    best_stat = p_result["best_stat"] if p_result else None
                    if fastest:
                        st.markdown("##### ⚡ Fewest flips")
                        show_cr9_path(fastest, "Fastest path")
                        if best_stat and best_stat["target"] != fastest["target"]:
                            st.markdown("##### 📈 Best stat outcome")
                            show_cr9_path(best_stat, "Best stat path")
                        else:
                            st.caption("Fastest path is also the best stat outcome.")
                    else:
                        st.info(f"No known pattern for {target_p} in research data.")

        with col_t:
            st.subheader("Tail light color")
            tl = cr9_data["taillight"]
            ambiguous = cr9_data["taillight_ambiguous"]
            if tl == ["Unknown"]:
                st.markdown("**Current:** ❓ Unknown")
                st.caption("Pattern not in research data. Share with Kaskrim at twitch.tv/kaskrim.")
            elif ambiguous:
                st.markdown(f"**Current:** ⚠️ {' or '.join(tl)} (ambiguous)")
                st.caption(f"Needs more data. If you can confirm, share with Kaskrim at twitch.tv/kaskrim.")
            else:
                st.markdown(f"**Current:** 💡 {tl[0]}")

            all_colors = sorted(set(color for colors in TAILLIGHT_LOOKUP.values() for color in colors))
            current_tl = tl[0] if tl and tl != ["Unknown"] and not ambiguous else None
            default_idx = all_colors.index(current_tl) if current_tl in all_colors else 0
            target_tl = st.selectbox("Target tail light color", options=all_colors, index=default_idx, key="target_taillight")

            if current_tl and target_tl == current_tl:
                st.success(f"Already {target_tl} — no flips needed.")
            else:
                tl_paths = taillight_paths(taillight_key)
                tl_result = tl_paths.get(target_tl)
                tl_fastest = tl_result["fastest"] if tl_result else None
                tl_best    = tl_result["best_stat"] if tl_result else None
                if tl_fastest:
                    st.markdown("##### ⚡ Fewest flips")
                    show_cr9_path(tl_fastest, "Fastest path")
                    if tl_best and tl_best["target"] != tl_fastest["target"]:
                        st.markdown("##### 📈 Best stat outcome")
                        show_cr9_path(tl_best, "Best stat path")
                    else:
                        st.caption("Fastest path is also the best stat outcome.")
                else:
                    st.info(f"No known pattern for {target_tl} in research data.")

# ── Footer ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<small>
Color ladder based on research by Kaskrim and Azizah, 2021–2026.
Glow and particle data: Kaskrim, 2026. Tail light series data: community research.
Lookup tables are incomplete — Unknown = not yet documented, not necessarily absent.
</small>
""", unsafe_allow_html=True)
