import re
from typing import Any, Dict, List
from langgraph.graph import StateGraph, END
from .schemas import AgentState, Field
from .tools import fetch_country_by_name

FIELD_KEYWORDS = [
    ("population", ["population", "people", "how many", "citizens"]),
    ("capital", ["capital"]),
    ("currency", ["currency", "money"]),
    ("region", ["region", "continent"]),
    ("subregion", ["subregion"]),
    ("languages", ["language", "languages", "spoken"]),
    ("timezones", ["timezone", "time zone"]),
    ("area", ["area", "size"]),
    ("flags", ["flag"]),
]

STOPWORDS = {
    "what", "is", "the", "a", "an", "does", "do", "use", "uses", "using",
    "currency", "capital", "population", "of", "in", "about", "and", "please", "tell", "me"
}

def identify_intent(state: AgentState) -> AgentState:
    user_query = state["user_query"].strip()
    q = user_query.lower()

    fields: List[Field] = []
    for field, kws in FIELD_KEYWORDS:
        if any(kw in q for kw in kws):
            fields.append(field)  # type: ignore[arg-type]

    if not fields:
        fields = ["capital", "population", "currency"]  # type: ignore[assignment]

    patterns = [
        r"\bof\s+([A-Za-z][A-Za-z\s\-]+)\??$",
        r"\bdoes\s+([A-Za-z][A-Za-z\s\-]+)\s+use\??$",
        r"\bin\s+([A-Za-z][A-Za-z\s\-]+)\??$",
        r"\babout\s+([A-Za-z][A-Za-z\s\-]+)\??$",
    ]

    country = ""
    for pat in patterns:
        m = re.search(pat, user_query, flags=re.IGNORECASE)
        if m:
            country = m.group(1).strip()
            break

    if not country:
        cleaned = re.sub(r"[^A-Za-z\s\-]", " ", user_query).strip()
        tokens = [t for t in cleaned.split() if t.lower() not in STOPWORDS]
        country = " ".join(tokens[-2:]) if len(tokens) >= 2 else (tokens[-1] if tokens else cleaned)

    return {**state, "country": country, "fields": fields}

def call_tool(state: AgentState) -> AgentState:
    try:
        result = fetch_country_by_name(state["country"])
        return {**state, "api_result": result, "error": None}
    except RuntimeError as e:
        return {**state, "api_result": None, "error": str(e)}

def synthesize_answer(state: AgentState) -> AgentState:
    if state.get("error"):
        return {**state, "answer": state["error"]}

    api_json = state.get("api_result") or {}
    fields = state.get("fields", [])

    name = api_json.get("name", {}).get("common") or api_json.get("name", {}).get("official") or state.get("country")

    def get_currency(d: Dict[str, Any]) -> str:
        currencies = d.get("currencies", {})
        if isinstance(currencies, dict) and currencies:
            code = next(iter(currencies.keys()))
            cur = currencies.get(code, {})
            return f"{cur.get('name', 'Unknown')} ({code})"
        return "Not available"

    parts = [f"Country: {name}"]

    for f in fields:
        if f == "capital":
            capital = (api_json.get("capital") or ["Not available"])[0]
            parts.append(f"Capital: {capital}")
        elif f == "population":
            parts.append(f"Population: {api_json.get('population', 'Not available')}")
        elif f == "currency":
            parts.append(f"Currency: {get_currency(api_json)}")
        elif f == "region":
            parts.append(f"Region: {api_json.get('region', 'Not available')}")
        elif f == "subregion":
            parts.append(f"Subregion: {api_json.get('subregion', 'Not available')}")
        elif f == "languages":
            langs = api_json.get("languages", {})
            parts.append(f"Languages: {', '.join(langs.values()) if isinstance(langs, dict) and langs else 'Not available'}")
        elif f == "timezones":
            tz = api_json.get("timezones", [])
            parts.append(f"Timezones: {', '.join(tz) if tz else 'Not available'}")
        elif f == "area":
            parts.append(f"Area (km²): {api_json.get('area', 'Not available')}")
        elif f == "flags":
            flags = api_json.get("flags", {})
            parts.append(f"Flag: {flags.get('png') or flags.get('svg') or 'Not available'}")

    return {**state, "answer": " | ".join(parts)}

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("identify_intent", identify_intent)
    g.add_node("call_tool", call_tool)
    g.add_node("synthesize_answer", synthesize_answer)

    g.set_entry_point("identify_intent")
    g.add_edge("identify_intent", "call_tool")
    g.add_edge("call_tool", "synthesize_answer")
    g.add_edge("synthesize_answer", END)

    return g.compile()