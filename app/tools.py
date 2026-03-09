import requests
from .config import RESTCOUNTRIES_BASE, REQUEST_TIMEOUT_S

def fetch_country_by_name(country: str):
    """
    Calls REST Countries API: https://restcountries.com/v3.1/name/{country}
    Returns the first match (best-effort).
    """
    url = f"{RESTCOUNTRIES_BASE}/{country}"
    params = {
        "fullText": "false",
        "fields": "name,capital,population,currencies,region,subregion,languages,timezones,area,flags",
    }

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_S)
    except requests.RequestException:
        raise RuntimeError("Network error while calling REST Countries API.")

    if resp.status_code == 404:
        raise RuntimeError(f"I couldn't find a country matching '{country}'.")
    if resp.status_code >= 400:
        raise RuntimeError("REST Countries API returned an error.")

    data = resp.json()
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"I couldn't find a country matching '{country}'.")

    return data[0]