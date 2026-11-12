"""NCBI PubMed E-utilities adapter for preliminary agricultural/nutrition literature."""

from typing import Any, Dict, List

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class PubMedAdapter(BaseIntegrationClient):
    """Queries https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi & esummary.fcgi."""

    service_name = "pubmed"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            timeout_seconds=10.0,
            max_retries=1,
            cache_ttl_seconds=86400,
        )
        self.settings = settings

    async def search_articles(self, query: str, max_results: int = 4) -> Dict[str, Any]:
        base_params: Dict[str, Any] = {
            "db": "pubmed",
            "retmode": "json",
            "tool": self.settings.NCBI_TOOL_NAME,
            "email": self.settings.NCBI_CONTACT_EMAIL,
        }
        if self.settings.NCBI_API_KEY:
            base_params["api_key"] = self.settings.NCBI_API_KEY

        try:
            search_res = await self.request_json(
                "GET",
                "/esearch.fcgi",
                params={
                    **base_params,
                    "term": f"{query} nutrition OR postharvest OR food composition",
                    "retmax": max_results,
                    "sort": "relevance",
                },
                cache_key=f"pubmed:search:{query.lower()}:{max_results}",
            )
            id_list = search_res.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return {"status": "ok", "articles": []}

            summary_res = await self.request_json(
                "GET",
                "/esummary.fcgi",
                params={**base_params, "id": ",".join(id_list)},
                cache_key=f"pubmed:sum:{','.join(id_list)}",
            )
            result_map = summary_res.get("result", {})
            articles: List[Dict[str, str]] = []
            for pmid in id_list:
                doc = result_map.get(pmid)
                if not isinstance(doc, dict):
                    continue
                articles.append(
                    {
                        "pmid": str(pmid),
                        "title": str(doc.get("title") or "PubMed Study"),
                        "journal": str(doc.get("fulljournalname") or doc.get("source") or "Journal"),
                        "pub_date": str(doc.get("pubdate") or ""),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    }
                )
            return {"status": "ok", "articles": articles}
        except IntegrationError:
            return {"status": "error", "articles": []}
