from typing import List, Optional, Set, Dict, Any
import time

from app.adapters.zabbix.base import ZabbixAdapterBase
from app.core.logging import get_module_logger
from modules.global_search.backend.schemas import (
    HostSearchResultDTO,
    ProblemSearchResultDTO,
    ServiceSearchResultDTO,
    ItemSearchResultDTO,
    HostCategoryResultDTO,
    ProblemCategoryResultDTO,
    ServiceCategoryResultDTO,
    ItemCategoryResultDTO,
    SearchCategoriesDTO,
    GlobalSearchResponseDTO
)

logger = get_module_logger("global_search")

METRIC_DEFINITIONS = [
    ("cpu_util", "CPU utilization", "system.cpu.util", "%"),
    ("cpu_load", "CPU load", "system.cpu.load", ""),
    ("memory_util", "Memory utilization", "vm.memory.util", "%"),
    ("storage_util", "Storage utilization on /", "vfs.fs.size[/,pused]", "%"),
    ("net_rx_rate", "Inbound network traffic", "net.if.in[eth0]", "Mbps"),
    ("net_tx_rate", "Outbound network traffic", "net.if.out[eth0]", "Mbps")
]


class GlobalSearchService:
    """
    Business service for Module 08: Global Search.
    Provides unified search across Hosts, Problems, Services, and Metrics.
    Enforces Zero-Fabrication: missing metric values are returned as None (NO_DATA).
    """

    def __init__(self, adapter: ZabbixAdapterBase):
        self.adapter = adapter

    async def search(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        limit: int = 20
    ) -> GlobalSearchResponseDTO:
        now_ts = int(time.time())
        clean_query = query.strip() if query else ""

        # Early return for empty query without querying backend or Zabbix
        if not clean_query:
            return GlobalSearchResponseDTO(
                query=query,
                timestamp=now_ts,
                categories=SearchCategoriesDTO(),
                total_results=0
            )

        # Normalize categories
        allowed_categories = {"hosts", "problems", "services", "items"}
        if categories:
            active_cats: Set[str] = {
                c.lower().strip() for c in categories if c.lower().strip() in allowed_categories
            }
        else:
            active_cats = allowed_categories

        hosts_result = HostCategoryResultDTO()
        problems_result = ProblemCategoryResultDTO()
        services_result = ServiceCategoryResultDTO()
        items_result = ItemCategoryResultDTO()

        total_results = 0
        all_servers = None
        if "hosts" in active_cats or "items" in active_cats:
            all_servers = await self.adapter.get_server_inventory(limit=1000)

        # 1. Search Hosts
        if "hosts" in active_cats:
            q_low = clean_query.lower()
            matched_servers = []
            for s in (all_servers or []):
                hname = s.get("name") or s.get("host") or ""
                tech_host = s.get("host") or ""
                os_str = s.get("os") or ""
                ip_match = any(q_low in iface.get("ip", "").lower() for iface in s.get("interfaces", []))
                dns_match = any(q_low in iface.get("dns", "").lower() for iface in s.get("interfaces", []))
                
                if (q_low in hname.lower() or 
                    q_low in tech_host.lower() or 
                    q_low in os_str.lower() or 
                    ip_match or 
                    dns_match):
                    matched_servers.append(s)

            total_matched = len(matched_servers)
            paged_servers = matched_servers[:limit]
            
            host_items: List[HostSearchResultDTO] = []
            for s in paged_servers:
                primary_ip = ""
                for iface in s.get("interfaces", []):
                    if iface.get("ip"):
                        primary_ip = iface["ip"]
                        break

                prob_summary = s.get("problem_summary", {})
                if isinstance(prob_summary, dict):
                    prob_cnt = prob_summary.get("total", 0)
                else:
                    prob_cnt = getattr(prob_summary, "total", 0) if prob_summary else 0

                host_items.append(HostSearchResultDTO(
                    id=str(s.get("hostid", "")),
                    name=s.get("name") or s.get("host") or "",
                    host=s.get("host") or "",
                    ip=primary_ip,
                    status=s.get("status", "UNKNOWN"),
                    groups=s.get("groups", []),
                    os=s.get("os"),
                    problems_count=prob_cnt
                ))

            hosts_result = HostCategoryResultDTO(
                items=host_items,
                total_matched=total_matched,
                is_truncated=total_matched > limit
            )
            total_results += total_matched

        # 2. Search Problems
        if "problems" in active_cats:
            raw_problems = await self.adapter.get_problem_feed(search=clean_query, limit=1000)
            total_matched = len(raw_problems)
            paged_problems = raw_problems[:limit]

            problem_items: List[ProblemSearchResultDTO] = []
            for p in paged_problems:
                h_name = ""
                h_id = ""
                hosts_list = p.get("hosts", [])
                if hosts_list:
                    h_name = hosts_list[0].get("name") or hosts_list[0].get("host") or ""
                    h_id = str(hosts_list[0].get("hostid", ""))

                ack = p.get("acknowledged") in (True, 1, "1")
                try:
                    sev = int(p.get("severity", 0))
                except (ValueError, TypeError):
                    sev = 0
                try:
                    clk = int(p.get("clock", 0))
                except (ValueError, TypeError):
                    clk = 0

                problem_items.append(ProblemSearchResultDTO(
                    eventid=str(p.get("eventid", "")),
                    name=p.get("name", ""),
                    severity=sev,
                    clock=clk,
                    acknowledged=ack,
                    host_name=h_name,
                    host_id=h_id,
                    opdata=p.get("opdata")
                ))

            problems_result = ProblemCategoryResultDTO(
                items=problem_items,
                total_matched=total_matched,
                is_truncated=total_matched > limit
            )
            total_results += total_matched

        # 3. Search Services
        if "services" in active_cats:
            raw_services = await self.adapter.get_services(search=clean_query, limit=1000)
            total_matched = len(raw_services)
            paged_services = raw_services[:limit]

            service_items: List[ServiceSearchResultDTO] = []
            for s in paged_services:
                try:
                    st = int(s.get("status", 0))
                except (ValueError, TypeError):
                    st = 0

                service_items.append(ServiceSearchResultDTO(
                    serviceid=str(s.get("serviceid", "")),
                    name=s.get("name", ""),
                    status=st,
                    description=s.get("description"),
                    tags=s.get("tags", [])
                ))

            services_result = ServiceCategoryResultDTO(
                items=service_items,
                total_matched=total_matched,
                is_truncated=total_matched > limit
            )
            total_results += total_matched

        # 4. Search Items / Metrics
        if "items" in active_cats:
            q_low = clean_query.lower()
            matched_items: List[ItemSearchResultDTO] = []

            for s in (all_servers or []):
                hid = str(s.get("hostid", ""))
                hname = s.get("name") or s.get("host") or f"Host-{hid}"
                tech_host = s.get("host") or ""
                metrics = s.get("metrics") or {}

                host_matches = q_low in hname.lower() or q_low in tech_host.lower()

                for m_key, m_name, m_item_key, m_unit in METRIC_DEFINITIONS:
                    if host_matches or q_low in m_name.lower() or q_low in m_item_key.lower():
                        val = metrics.get(m_key)
                        matched_items.append(ItemSearchResultDTO(
                            itemid=f"{hid}_{m_key}",
                            name=m_name,
                            key_=m_item_key,
                            host_name=hname,
                            host_id=hid,
                            lastvalue=val,
                            units=m_unit
                        ))

            total_matched = len(matched_items)
            paged_items = matched_items[:limit]

            items_result = ItemCategoryResultDTO(
                items=paged_items,
                total_matched=total_matched,
                is_truncated=total_matched > limit
            )
            total_results += total_matched

        return GlobalSearchResponseDTO(
            query=query,
            timestamp=now_ts,
            categories=SearchCategoriesDTO(
                hosts=hosts_result,
                problems=problems_result,
                services=services_result,
                items=items_result
            ),
            total_results=total_results
        )
