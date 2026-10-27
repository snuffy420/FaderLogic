"""Stable appearance identifiers; styling never changes harmonic relationships."""
WHEEL_STYLES = {
    "classic": "Classic",
    "obsidian": "Obsidian Neon",
    "minimal": "Dark Minimal",
    "outline": "Neon Outline",
    "accessible": "Colour-blind · labels + patterns",
}
WAVE_STYLES = {
    "classic": "Classic bars",
    "enhanced": "Enhanced glow bars",
    "filled": "Smooth filled",
    "spectrogram": "Spectrogram",
    "multilayer": "Multilayer",
    "segmented": "Energy segments",
    "line": "Minimal glow line",
    "split_bars": "Split bands · bars",
    "split_ribbon": "Split bands · ribbons",
}
WAVE_MODES = {"normal": "Normal", "rgb": "RGB", "bands": "3-band", "faderlogic": "FaderLogic · original colours"}

# Text codes convey the complete relation without needing to distinguish hues.
RELATION_CODES = {
    "Perfect Match": "=", "Perfect Mix": "=",
    "Energy Boost (+)": "+", "Energy Boost (++)": "++", "Energy Boost (+++)": "+++",
    "Energy Drop (-)": "-", "Energy Drop (--)": "--", "Energy Drop (---)": "---",
    "Mood Change": "M", "-1 Mix": "-1", "+1 Mix": "+1", "Energy Boost": "+2",
    "Scale Change": "S", "Diagonal Mix": "D", "Jaw's Mix": "J", "Mood Shifter": "M",
}

# Alternative relation palette. Patterns and printed codes carry the information
# independently of hue, including monochrome and different colour deficiencies.
ACCESSIBLE_RELATIONS = {
    "Perfect Match": ("#56B4E9", "dots"),
    "Energy Boost (+)": ("#E69F00", "forward hatch"),
    "Energy Boost (++)": ("#009E73", "cross hatch"),
    "Energy Boost (+++)": ("#CC79A7", "horizontal"),
    "Energy Drop (-)": ("#F0E442", "back hatch"),
    "Energy Drop (--)": ("#0072B2", "vertical"),
    "Energy Drop (---)": ("#D55E00", "diagonal cross"),
    "Mood Change": ("#BBBBBB", "dense dots"),
    "Perfect Mix": ("#56B4E9", "dots"),
    "-1 Mix": ("#F0E442", "back hatch"),
    "+1 Mix": ("#E69F00", "forward hatch"),
    "Energy Boost": ("#009E73", "cross hatch"),
    "Scale Change": ("#0072B2", "vertical"),
    "Diagonal Mix": ("#CC79A7", "horizontal"),
    "Jaw's Mix": ("#D55E00", "diagonal cross"),
    "Mood Shifter": ("#BBBBBB", "dense dots"),
}


def chart_relations(chart_name):
    names = list(ACCESSIBLE_RELATIONS)
    return names[:8] if chart_name.startswith('Chart 1') else names[8:]


def accessible_style(label, status, show_all):
    if show_all:
        return ACCESSIBLE_RELATIONS.get(label, ('#6B7684', 'none'))
    return ('#75CEFF', 'dots') if status == 'green' else ('#FFDC73', 'forward hatch')


def accessible_legend(chart_name, show_all):
    """Both Help and on-screen legends use exactly the rendered relation palette."""
    from . import camelot
    rows = []
    # Status classifications differ by chart and must come from the chart itself.
    statuses = {}
    for source in camelot.CHART_CHOICES[chart_name]:
        # Tables all expose the same relation categories on every source key.
        for target in camelot.CAMELOT_COLORS:
            status, label = camelot.get_compatibility(source, target, chart_name=chart_name)
            statuses[label] = status
        break
    for name in chart_relations(chart_name):
        colour, pattern = accessible_style(name, statuses[name], show_all)
        rows.append((RELATION_CODES[name], name, colour, pattern))
    return rows


def standard_legend(chart_name, show_all):
    from . import camelot
    from .theme import COLORS
    source = next(iter(camelot.CHART_CHOICES[chart_name]))
    statuses = {label: status for status,label in
                (camelot.get_compatibility(source,target,chart_name=chart_name) for target in camelot.CAMELOT_COLORS)}
    return [(RELATION_CODES[name], name,
             camelot.VARIATIONS[name][0] if show_all else COLORS[statuses[name]])
            for name in chart_relations(chart_name)]


def clean_appearance(values):
    values = dict(values)
    if values.get('wave_mode') == 'mixlogic':
        values['wave_mode'] = 'faderlogic'
    return {
        "wheel_style": values.get("wheel_style") if values.get("wheel_style") in WHEEL_STYLES else "classic",
        "wave_style": values.get("wave_style") if values.get("wave_style") in WAVE_STYLES else "classic",
        "wave_mode": values.get("wave_mode") if values.get("wave_mode") in WAVE_MODES else "bands",
        "theme": values.get('theme') if values.get('theme') in ('dark','light') else 'dark',
    }


def wheel_legend_html(chart_name, show_all, accessible=False):
    """One explanation for workspace and preview, using the rendered palette."""
    from .theme import COLORS
    divider=" <span style='color:#84909E'>&nbsp;|&nbsp;</span> "
    if accessible:
        header="SEL =: selected + perfect match (white double outline)"+divider+"×: unlisted / dimmed"
        rows=accessible_legend(chart_name,show_all)
        entries=[f"<span style='color:{colour}'>■</span> <b>{code}</b>: {name} ({pattern})" for code,name,colour,pattern in rows]
    else:
        header=f"<span style='color:{COLORS['cyan']}'>■</span> Selected"+divider+"Unlisted keys dimmed"
        entries=[f"<span style='color:{colour}'>■</span> {name}" for _,name,colour in standard_legend(chart_name,show_all)]
    return "<b>"+chart_name+"</b><br>"+header+"<br>"+divider.join(entries)
