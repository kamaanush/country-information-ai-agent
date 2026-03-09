from typing import Any, Dict, List, Literal, Optional, TypedDict

Field = Literal[
    "capital",
    "population",
    "currency",
    "region",
    "subregion",
    "languages",
    "timezones",
    "area",
    "flags",
]

class AgentState(TypedDict, total=False):
    user_query: str
    country: str
    fields: List[Field]
    api_result: Optional[Dict[str, Any]]
    answer: str
    error: Optional[str]