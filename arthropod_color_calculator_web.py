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


st.set_page_config(
    page_title="Arthropod Color Calculator",
    page_icon="🐝",
    layout="centered"
)

st.title("🐝 Arthropod Color Calculator")
st.caption("Project Gorgon Genetics Research · Kaskrim & Azizah · Lumière")

st.markdown("""
Calculate the minimum changes needed to reach a target body or wing color.

**You can paste either:**
- A single chromosome string (40 positions for CR1/CR3, 10 for CR5, 20 for CR9)
- Your full game genome export — the app will extract all relevant chromosomes automatically

**Notation:** The app accepts both game export format (`D` `R` `x`) and internal format (`X` `o` `t`) — both work.
""")

st.warning("⚠️ **Genetics skill must be uncapped at level 100.** Do not use this tool with a genome that contains ? marks.")

# ── Full export paste ──────────────────────────────────────────────────────
st.markdown("### 📋 Paste Full Genome Export")
st.markdown("If you have the full game export, paste it here and all chromosomes will be filled in automatically.")
full_export_input = st.text_area(
    "Full genome export",
    placeholder="Paste everything here — starting from [Overview] or [Genes] — and the app will do the rest.",
    height=150,
    key="full_export_input",
    label_visibility="collapsed"
)

if full_export_input.strip():
    parsed_export = parse_full_export(full_export_input.strip())
    if parsed_export:
        st.success(f"✅ Export parsed — found chromosomes: {', '.join(f'CR{k}' for k in sorted(parsed_export.keys()))}")
        st.session_state["export_cr1"] = parsed_export.get(1, "")
        st.session_state["export_cr3"] = parsed_export.get(3, "")
        st.session_state["export_cr5"] = parsed_export.get(5, "")
        st.session_state["export_cr9"] = parsed_export.get(9, "")
    else:
        st.info("This doesn't look like a full export — use the individual chromosome fields below.")

st.divider()

col1, col2 = st.columns(2)
with col1:
    cr_choice = st.radio(
        "Chromosome",
        options=["CR 1 — Body color", "CR 3 — Wing color"],
        index=0
    )
    cr = 1 if "CR 1" in cr_choice else 3

with col2:
    ladder = COLOR_LADDER_CR1 if cr == 1 else COLOR_LADDER_CR3
    target_color = st.selectbox(
        "Target color",
        options=list(ladder.keys()),
        index=0
    )

_cr_key = "export_cr1" if cr == 1 else "export_cr3"
_prefill = st.session_state.get(_cr_key, "")
genome_input = st.text_input(
    "Genome string (40 positions, spaces OK)",
    placeholder="e.g. RRRR DRRR RRDR RRRR RRRX DRDx DRDD DDDD DDDD RRRD",
    value=_prefill,
)

if genome_input.strip():
    positions, error = parse_genome(genome_input.strip(), cr)

    if error:
        st.error(f"⚠️ {error}")
    else:
        fj = fj_dom_count(positions, cr)
        ae = ae_dom_count(positions, cr)
        current_color = detect_color(fj, ae, cr)

        st.divider()

        m1, m2, m3 = st.columns(3)
        m1.metric("F-J dominant or mixed", f"{fj} / 20")
        m2.metric("A-E dominant or mixed", f"{ae} / 20")
        m3.metric("Estimated color", current_color)

        # Show low F-J note when genome is below ladder or targeting red with very low F-J
        if "Below ladder" in current_color or (target_color == "Red" and fj <= 6):
            st.info("""ℹ️ **Low F-J zone — bottom of the wheel**

The color wheel is circular. Red appears at both ends of the ladder.
All-recessive on CR 1 is confirmed to produce red by wrapping clockwise past violet.

What other colors may exist in this low F-J zone (F-J=0–6) is **untested**.
Other colors may be achievable here. Until data points confirm what lives in this zone,
this app defaults to Red for any genome below F-J=7.

If your bee has an unusual color at very low F-J, that is valuable research data.
Please share it with Kaskrim.""")

        st.divider()

        target_lo, target_hi = ladder[target_color]
        status, paths, _ = calculate_changes(positions, cr, target_color)

        if status == "already_there":
            st.success(f"✅ Already in the **{target_color}** zone (F-J dom/mixed = {fj}).")
            st.info("A-E dominant or mixed fine-tunes the exact shade within this zone.")
        else:
            def show_path(path, label):
                direction = path["direction"]
                needed = path["needed"]
                selected = path["selected"]
                cost = path["cost"]
                pts = path["pts"]
                feasible = path["feasible"]

                if not feasible:
                    st.warning(f"⚠️ {label}: Only {len(selected)} eligible positions found — not enough.")
                    return

                # Calculate net stat change for summary
                net = sum(cost.values())
                if pts == 0:
                    st.success(f"**{label}:** {needed} change(s) — 🟢 no stat cost")
                elif net > 0:
                    st.success(f"**{label}:** {needed} change(s) — 🟢 {pts} stat point(s) gained")
                else:
                    st.warning(f"**{label}:** {needed} change(s) — 🔴 {pts} stat point(s) lost")

                st.markdown(f"*Direction: {direction}*")
                for i, (coord, is_stat, stat_name, stat_val) in enumerate(selected):
                    if is_stat and stat_val > 0:
                        # dominant→recessive = stat ON = gain; recessive→dominant = stat OFF = loss
                        if direction == "dominant → recessive":
                            st.markdown(f"**{i+1}.** `{coord}` · gains **+{stat_val} {stat_name}**")
                        else:
                            st.markdown(f"**{i+1}.** `{coord}` · costs **−{stat_val} {stat_name}**")
                    else:
                        st.markdown(f"**{i+1}.** `{coord}` · cosmetic, no stat cost")

                if cost:
                    for stat, delta in sorted(cost.items()):
                        sign = "+" if delta > 0 else ""
                        color_str = "🟢" if delta > 0 else "🔴"
                        st.markdown(f"{color_str} **{stat}:** {sign}{delta}")
                else:
                    st.markdown("🟢 **No stat impact.**")

            path_a = paths.get("path_a")
            path_b = paths.get("path_b")

            if path_b:
                # Show both paths, recommend cheaper one
                pts_a = path_a["pts"] if path_a else 999
                pts_b = path_b["pts"]

                if pts_a <= pts_b:
                    st.markdown("### ✅ Recommended: Direct path")
                    show_path(path_a, path_a["label"])
                    st.divider()
                    st.markdown(f"### Alternative: {path_b['label']}")
                    st.caption(f"Costs {pts_b} stat points — more expensive than direct path.")
                    show_path(path_b, path_b["label"])
                else:
                    st.markdown(f"### ✅ Recommended: {path_b['label']}")
                    st.caption("Cheaper in stat cost than the direct path.")
                    show_path(path_b, path_b["label"])
                    st.divider()
                    st.markdown("### Alternative: Direct path")
                    st.caption(f"Costs {pts_a} stat points — more expensive.")
                    show_path(path_a, path_a["label"])
            else:
                show_path(path_a, path_a["label"])

st.divider()
st.markdown("""
<small>
Color ladder based on research by Kaskrim and Azizah, 2021–2026.
F-J dominant or mixed sets broad hue position (more F-J = clockwise = toward purple/blue).
A-E dominant or mixed fine-tunes within the zone (more A-E = counterclockwise = toward warmer colors).
The two axes push in opposite directions.
</small>
""", unsafe_allow_html=True)

# ============================================================
# CR5 GLOW + CR9 PARTICLES & TAIL LIGHT
# ============================================================

# ---- CR5 STAT GENE MAP ----
# Position: (stat_name, point_value)
# A1, A3, C1 are cosmetic (_)
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
# CR5 / CR9 UI SECTION
# ============================================================

st.divider()
st.header("🐝 Visual Traits — CR5 & CR9")
st.caption("Glow (CR5) · Particles & Tail Light (CR9)")
st.markdown("""
Paste your CR5 and CR9 genome strings to look up glow, particle location, and tail light color.
These are lookup tables — results not in the research data will show as **Unknown** or **Glow off**.
""")

col_cr5, col_cr9 = st.columns(2)

with col_cr5:
    st.subheader("CR5 — Glow (10 positions)")
    _cr5_prefill = st.session_state.get("export_cr5", "")
    cr5_input = st.text_input(
        "CR5 genome string",
        placeholder="e.g. RRRR RDxR DR",
        key="cr5_input",
        value=_cr5_prefill,
    )
    if cr5_input.strip():
        result, err = analyze_cr5(cr5_input.strip())
        if err:
            st.error(f"⚠️ {err}")
        else:
            if result["glow"]:
                st.success("✨ **Glow: ON**")
            else:
                st.info("🔘 **Glow: Off**")

            st.markdown("**CR5 stat contributions (recessive positions):**")
            if result["expressing"]:
                for coord, stat_name, stat_val in sorted(result["expressing"]):
                    st.markdown(f"  `{coord}` → +{stat_val} {stat_name}")
                st.markdown("**Totals from CR5:**")
                for stat, total in sorted(result["stat_totals"].items()):
                    st.markdown(f"  🟢 {stat}: +{total}")
            else:
                st.markdown("  No stat genes expressing on CR5.")

            if result["not_expressing"]:
                with st.expander("Stat genes not expressing (dominant)"):
                    for coord, stat_name, stat_val in sorted(result["not_expressing"]):
                        st.markdown(f"  `{coord}` → {stat_val} {stat_name} (off)")

            # ---- Glow: show paths or better-stat alternatives ----
            if result["glow"]:
                # Already glowing — check if a better-stat glow-on pattern exists
                st.divider()
                st.markdown("**Optimize glow stats:**")
                current_norm = result["norm"]
                coords = [f"5{l}{p}" for l, sz in [("A",4),("B",4),("C",2)] for p in range(1, sz+1)]
                better_paths = []
                current_stat_total = sum(
                    STAT_GENES_CR5[coord][1]
                    for i, coord in enumerate(coords)
                    if current_norm[i] == "o" and coord in STAT_GENES_CR5 and STAT_GENES_CR5[coord][1] > 0
                )
                for target_norm in GLOW_ON_PATTERNS:
                    if target_norm == current_norm:
                        continue
                    target_stat_total = sum(
                        STAT_GENES_CR5[coord][1]
                        for i, coord in enumerate(coords)
                        if target_norm[i] == "o" and coord in STAT_GENES_CR5 and STAT_GENES_CR5[coord][1] > 0
                    )
                    if target_stat_total > current_stat_total:
                        flips = []
                        net_stat = {}
                        for i, coord in enumerate(coords):
                            c, t = current_norm[i], target_norm[i]
                            if c != t:
                                direction = "recessive → dominant" if t == "X" else "dominant → recessive"
                                stat_info = STAT_GENES_CR5.get(coord)
                                if stat_info and stat_info[1] > 0:
                                    delta = stat_info[1] if "dominant → recessive" in direction else -stat_info[1]
                                    net_stat[stat_info[0]] = net_stat.get(stat_info[0], 0) + delta
                                flips.append({"coord": coord, "direction": direction, "stat": stat_info})
                        better_paths.append({
                            "target": target_norm,
                            "flips": flips,
                            "flips_count": len(flips),
                            "net_stat": net_stat,
                            "net_total": sum(net_stat.values()),
                        })
                WORST_GLOW_PATTERN = "oooooXXXXo"  # loses both Ferocity and Friendliness
                is_worst = current_norm == WORST_GLOW_PATTERN

                if better_paths:
                    if is_worst:
                        st.warning("⚠️ Your current glow pattern has the lowest stat value of all known glow-on patterns — it costs both Ferocity and Friendliness. All other glow-on patterns are better.")
                    best = max(better_paths, key=lambda p: p["net_total"])
                    st.markdown(f"A better-stat glow-on pattern exists (+{best['net_total']} net stats):")
                    show_glow_path(best, "Better stat option")
                    if len(better_paths) > 1:
                        with st.expander(f"Other better options ({len(better_paths) - 1} more)"):
                            for p in sorted(better_paths, key=lambda p: -p["net_total"])[1:]:
                                show_glow_path(p, f"Alternative ({p['flips_count']} flip(s))")
                else:
                    st.success("Current glow pattern already has the best stats among known glow-on patterns.")
            elif not result["glow"]:
                st.divider()
                st.markdown("**Paths to turn glow on:**")
                paths_speed, paths_stat = glow_on_paths(result["positions"], result["norm"])

                def show_glow_path(path, label):
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

                # Three fixed sections:
                # 1. Shortest path to any glow-on
                # 2. Path to -1 Ferocity pattern
                # 3. Path to -3 Friendliness pattern
                FEROCITY_PATTERN    = "oooooXoXoo"
                FRIENDLINESS_PATTERN = "oooooXXoXo"

                fastest = paths_speed[0]
                st.markdown("##### ⚡ Shortest path to glow")
                show_glow_path(fastest, "Shortest path")

                # Path to -1 Ferocity pattern
                fe_path = next((p for p in paths_speed if p["target"] == FEROCITY_PATTERN), None)
                st.markdown("##### Path to −1 Ferocity glow")
                if fe_path and fe_path["flips_count"] == 0:
                    st.success("Already on this pattern.")
                elif fe_path:
                    show_glow_path(fe_path, f"{fe_path['flips_count']} flip(s)")
                else:
                    st.info("No path available.")

                # Path to -3 Friendliness pattern
                fr_path = next((p for p in paths_speed if p["target"] == FRIENDLINESS_PATTERN), None)
                st.markdown("##### Path to −3 Friendliness glow")
                if fr_path and fr_path["flips_count"] == 0:
                    st.success("Already on this pattern.")
                elif fr_path:
                    show_glow_path(fr_path, f"{fr_path['flips_count']} flip(s)")
                else:
                    st.info("No path available.")

with col_cr9:
    st.subheader("CR9 — Particles & Tail Light (20 positions)")
    _cr9_prefill = st.session_state.get("export_cr9", "")
    cr9_input = st.text_input(
        "CR9 genome string",
        placeholder="e.g. DDxD DRxR xDRR DRRR RRRR",
        key="cr9_input",
        value=_cr9_prefill,
    )
    if cr9_input.strip():
        result, err = lookup_cr9(cr9_input.strip())
        if err:
            st.error(f"⚠️ {err}")
        else:
            p = result["particle"]
            tl = result["taillight"]
            ambiguous = result["taillight_ambiguous"]

            p_icon = {"Tail": "🐝", "Wing": "🪽", "None": "⬜", "Unknown": "❓"}.get(p, "❓")
            st.markdown(f"**Particles:** {p_icon} {p}")

            if tl == ["Unknown"]:
                st.markdown("**Tail light:** ❓ Unknown")
                st.caption("This pattern isn't in the research data yet. If you know what tail light color this bee has, please share the genome with Kaskrim at twitch.tv/kaskrim.")
            elif ambiguous:
                colors_str = " or ".join(tl)
                st.warning(f"**Tail light:** ⚠️ {colors_str}")
                st.caption(
                    f"This genome pattern matches multiple tail light colors in the research data "
                    f"({colors_str}). The decode for this pattern is not yet confirmed. "
                    f"If you can confirm which color your bee actually has, please share it with "
                    f"Kaskrim at twitch.tv/kaskrim — it will help resolve the ambiguity."
                )
            else:
                st.markdown(f"**Tail light:** 💡 {tl[0]}")

            if p == "Unknown":
                st.caption("Particle result unknown — pattern not in research data. Share with Kaskrim at twitch.tv/kaskrim.")

            # ---- Particle target dropdown ----
            st.divider()
            st.markdown("**Change particle location:**")
            particle_options = ["Tail", "Wing", "None"]
            current_label = p if p in particle_options else None
            default_idx = particle_options.index(current_label) if current_label in particle_options else 0
            target_particle = st.selectbox(
                "Target particle location",
                options=particle_options,
                index=default_idx,
                key="target_particle",
                format_func=lambda x: {"Tail": "🐝 Tail", "Wing": "🪽 Wing", "None": "⬜ None"}.get(x, x)
            )

            norm_full, _ = normalize_genome_str(cr9_input.strip(), 20)
            if norm_full:
                particle_key = norm_full[:10]
                if target_particle == p:
                    # Same type — check if a better-stat pattern exists within this type
                    paths = particle_paths(particle_key)
                    p_result = paths.get(target_particle)
                    best_stat = p_result["best_stat"] if p_result else None
                    if best_stat and best_stat["flips_count"] > 0 and best_stat["net_total"] > 0:
                        st.success(f"Already {target_particle} particles.")
                        st.markdown("📈 **A better-stat pattern exists for this type:**")
                        show_cr9_path(best_stat, "Better stat option")
                    elif best_stat and best_stat["flips_count"] > 0 and best_stat["net_total"] == 0:
                        st.success(f"Already {target_particle} particles — current pattern has optimal stats for this type.")
                    else:
                        st.success(f"Already {target_particle} particles — current pattern has optimal stats for this type.")
                else:
                    paths = particle_paths(particle_key)
                    p_result = paths.get(target_particle)
                    fastest = p_result["fastest"] if p_result else None
                    best_stat = p_result["best_stat"] if p_result else None
                    if fastest is None:
                        if target_particle == "None":
                            st.info("No-particle states are achievable but the research data in this app doesn't yet include documented patterns to aim for. Check back as more data is added.")
                        else:
                            st.info("No known pattern available for this particle location.")
                    else:
                        st.markdown("##### ⚡ Fewest flips")
                        show_cr9_path(fastest, "Fastest path")
                        if best_stat and best_stat["target"] != fastest["target"]:
                            st.markdown("##### 📈 Best stat outcome")
                            show_cr9_path(best_stat, "Best stat path")
                        else:
                            st.caption("The fastest path is also the best stat outcome.")

            # ---- Tail light color target dropdown ----
            st.divider()
            st.markdown("**Change tail light color:**")
            norm_full2, _ = normalize_genome_str(cr9_input.strip(), 20)
            if norm_full2:
                taillight_key = norm_full2[10:]
                # Build color options from lookup
                all_colors = sorted(set(
                    color for colors in TAILLIGHT_LOOKUP.values() for color in colors
                ))
                current_tl = tl[0] if tl and tl != ["Unknown"] and not ambiguous else None
                default_tl_idx = all_colors.index(current_tl) if current_tl in all_colors else 0
                target_tl = st.selectbox(
                    "Target tail light color",
                    options=all_colors,
                    index=default_tl_idx,
                    key="target_taillight"
                )
                if current_tl and target_tl == current_tl:
                    st.success(f"Already {target_tl} — no flips needed.")
                else:
                    tl_paths = taillight_paths(taillight_key)
                    tl_result = tl_paths.get(target_tl)
                    tl_fastest = tl_result["fastest"] if tl_result else None
                    tl_best_stat = tl_result["best_stat"] if tl_result else None
                    if tl_fastest is None:
                        st.info(f"No known pattern for {target_tl} in research data.")
                    else:
                        st.markdown("##### ⚡ Fewest flips")
                        show_cr9_path(tl_fastest, "Fastest path")
                        if tl_best_stat and tl_best_stat["target"] != tl_fastest["target"]:
                            st.markdown("##### 📈 Best stat outcome")
                            show_cr9_path(tl_best_stat, "Best stat path")
                        else:
                            st.caption("The fastest path is also the best stat outcome.")

st.divider()
st.markdown("""
<small>
Glow and particle data: Kaskrim, 2026. Tail light series data: community research.
Lookup tables are incomplete — Unknown = not yet documented, not necessarily absent.
</small>
""", unsafe_allow_html=True)

