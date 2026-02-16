"""Mock Tavily API responses for testing.

Provides pre-defined search results for news/media agent testing without
consuming actual API credits.
"""


# ============================================================================
# Mock Search Results - Supporting Evidence
# ============================================================================

MOCK_TAVILY_RESPONSE_SUPPORTING = {
    "results": [
        {
            "title": "Company Reports 12% Reduction in Scope 1 Emissions",
            "url": "https://reuters.com/business/sustainable-energy/company-reports-emissions-reduction-2024",
            "content": "The company announced today that its Scope 1 emissions decreased by 12% compared to the previous fiscal year, achieving its interim sustainability target ahead of schedule. The reduction was attributed to investments in energy efficiency and renewable energy.",
            "published_date": "2024-06-15",
            "score": 0.92,
        },
        {
            "title": "Sustainability Report Highlights Strong ESG Performance",
            "url": "https://bloomberg.com/news/articles/company-esg-performance",
            "content": "Independent analysts confirmed the company's emissions reduction claims, noting that the reported figures align with third-party verification data. The company ranks among the top performers in its sector for climate action.",
            "published_date": "2024-05-20",
            "score": 0.88,
        },
        {
            "title": "Industry Leaders Achieve Emissions Targets",
            "url": "https://ft.com/content/industry-emissions-targets-2024",
            "content": "Several major companies in the sector reported meeting or exceeding their emissions reduction targets for 2024. Industry analysts note this represents a significant shift toward genuine climate action.",
            "published_date": "2024-04-10",
            "score": 0.75,
        },
    ],
    "query": "company emissions reduction 2024",
    "follow_up_questions": None,
    "answer": None,
}


MOCK_TAVILY_RESPONSE_SUPPORTING_TIER_1 = {
    "results": [
        {
            "title": "SEC Filing Confirms Emissions Disclosure Compliance",
            "url": "https://sec.gov/cgi-bin/browse-edgar?action=getcompany&company=example",
            "content": "Form 10-K filing includes audited sustainability metrics confirming the company's reported emissions figures. External auditor provided reasonable assurance on GHG emissions data.",
            "published_date": "2024-03-15",
            "score": 0.95,
        },
    ],
    "query": "company SEC emissions disclosure",
}


# ============================================================================
# Mock Search Results - Contradicting Evidence
# ============================================================================

MOCK_TAVILY_RESPONSE_CONTRADICTING = {
    "results": [
        {
            "title": "Company Faces EPA Enforcement Action Over Emissions Violations",
            "url": "https://propublica.org/article/company-emissions-violations-investigation",
            "content": "An investigation reveals that the company's actual emissions may be significantly higher than reported in sustainability disclosures. EPA enforcement documents show the company exceeded permitted emission limits at three facilities during the reporting period.",
            "published_date": "2024-08-01",
            "score": 0.94,
        },
        {
            "title": "Whistleblower Alleges Greenwashing at Major Corporation",
            "url": "https://nytimes.com/2024/07/15/business/company-greenwashing-allegations",
            "content": "A former employee has come forward with documents suggesting the company manipulated emissions data in its sustainability reports. The whistleblower claims actual Scope 1 emissions increased by 5% rather than the reported 12% decrease.",
            "published_date": "2024-07-15",
            "score": 0.91,
        },
        {
            "title": "Environmental Group Questions Sustainability Claims",
            "url": "https://theguardian.com/environment/company-sustainability-questions",
            "content": "Environmental advocacy groups have raised concerns about the methodology used to calculate the company's reported emissions reductions. The groups argue that changes in accounting methods, rather than actual reductions, account for most of the improvement.",
            "published_date": "2024-06-22",
            "score": 0.82,
        },
    ],
    "query": "company emissions violation investigation",
}


MOCK_TAVILY_RESPONSE_DIRECT_CONTRADICTION = {
    "results": [
        {
            "title": "EPA Data Shows Company Emissions Actually Increased",
            "url": "https://epa.gov/enforcement/company-emissions-data-2024",
            "content": "According to EPA monitoring data, the company's Scope 1 emissions increased by 8% year-over-year, contradicting the company's sustainability report which claimed a 12% decrease. The discrepancy is under investigation.",
            "published_date": "2024-09-01",
            "score": 0.96,
        },
    ],
    "query": "company EPA emissions data",
}


MOCK_TAVILY_RESPONSE_TIMELINE_CONTRADICTION = {
    "results": [
        {
            "title": "Company Delays Net-Zero Target to 2060",
            "url": "https://wsj.com/articles/company-delays-climate-target",
            "content": "The company announced a revision to its climate strategy, pushing back its net-zero commitment from 2050 to 2060. The delay contradicts statements made in the company's most recent sustainability report which maintained the 2050 target.",
            "published_date": "2024-08-20",
            "score": 0.90,
        },
    ],
    "query": "company net-zero target delay",
}


# ============================================================================
# Mock Search Results - Mixed Evidence
# ============================================================================

MOCK_TAVILY_RESPONSE_MIXED = {
    "results": [
        {
            "title": "Company Reports Progress on Sustainability Goals",
            "url": "https://prnewswire.com/news/company-sustainability-update",
            "content": "The company announced continued progress toward its sustainability goals, reporting reductions in Scope 1 and 2 emissions for the fiscal year.",
            "published_date": "2024-05-01",
            "score": 0.85,
        },
        {
            "title": "Analysts Question Methodology in Emissions Report",
            "url": "https://seekingalpha.com/article/company-emissions-methodology",
            "content": "While the company reports emissions reductions, some analysts have questioned whether changes in business boundaries account for part of the reported improvement rather than genuine efficiency gains.",
            "published_date": "2024-06-10",
            "score": 0.78,
        },
    ],
    "query": "company emissions report analysis",
}


# ============================================================================
# Mock Search Results - Empty/No Results
# ============================================================================

MOCK_TAVILY_RESPONSE_EMPTY = {
    "results": [],
    "query": "obscure company nonexistent topic",
}


MOCK_TAVILY_RESPONSE_MINIMAL = {
    "results": [
        {
            "title": "Brief Industry Update",
            "url": "https://example-blog.com/industry-update",
            "content": "Various companies in the sector are making sustainability announcements.",
            "published_date": None,
            "score": 0.45,
        },
    ],
    "query": "industry sustainability news",
}


# ============================================================================
# Mock Search Results - Certification/Award Claims
# ============================================================================

MOCK_TAVILY_RESPONSE_CERTIFICATION_VERIFIED = {
    "results": [
        {
            "title": "ISO Certifies Company's Environmental Management System",
            "url": "https://bbc.com/news/business/company-iso-certification",
            "content": "The company has received ISO 14001 certification for its environmental management system at all major facilities. The certification was issued by an accredited third-party auditor following comprehensive review.",
            "published_date": "2024-02-28",
            "score": 0.93,
        },
        {
            "title": "Company Achieves Science Based Targets Initiative Validation",
            "url": "https://reuters.com/sustainability/company-sbti-validation",
            "content": "The Science Based Targets initiative has validated the company's emissions reduction targets as consistent with limiting global warming to 1.5°C. The company joins over 2,000 companies with validated science-based targets.",
            "published_date": "2024-04-15",
            "score": 0.89,
        },
    ],
    "query": "company ISO certification SBTi",
}


MOCK_TAVILY_RESPONSE_CERTIFICATION_REVOKED = {
    "results": [
        {
            "title": "Company Loses ISO 14001 Certification Following Audit",
            "url": "https://bloomberg.com/news/company-loses-certification",
            "content": "The company's ISO 14001 certification has been revoked following a compliance audit that found significant gaps in environmental management practices. The certification body cited failure to address non-conformances identified in previous audits.",
            "published_date": "2024-07-01",
            "score": 0.92,
        },
    ],
    "query": "company ISO certification status",
}


# ============================================================================
# Mock Search Results - Press Releases (Tier 3)
# ============================================================================

MOCK_TAVILY_RESPONSE_PRESS_RELEASE = {
    "results": [
        {
            "title": "FOR IMMEDIATE RELEASE: Company Announces Sustainability Milestone",
            "url": "https://prnewswire.com/news-releases/company-sustainability-milestone",
            "content": "Company today announced the achievement of its 2024 sustainability targets, including a 15% reduction in carbon emissions and 100% renewable energy procurement for North American operations.",
            "published_date": "2024-06-01",
            "score": 0.88,
        },
        {
            "title": "Company Reports Q3 Results and ESG Progress",
            "url": "https://businesswire.com/news/company-q3-results-esg",
            "content": "Company today reported strong Q3 financial results alongside continued progress on environmental, social, and governance initiatives. The company reaffirmed its commitment to net-zero emissions by 2050.",
            "published_date": "2024-10-15",
            "score": 0.82,
        },
    ],
    "query": "company sustainability announcement",
}


# ============================================================================
# Mock Search Results - Social Media / Tier 4
# ============================================================================

MOCK_TAVILY_RESPONSE_LOW_CREDIBILITY = {
    "results": [
        {
            "title": "My Thoughts on Company's Green Claims",
            "url": "https://medium.com/@blogger/company-green-claims",
            "content": "I've been looking into this company's sustainability claims and I'm not convinced. Here are my personal opinions on their latest report...",
            "published_date": "2024-05-15",
            "score": 0.55,
        },
        {
            "title": "Reddit Discussion: Is Company Actually Sustainable?",
            "url": "https://reddit.com/r/sustainability/company-claims",
            "content": "User discussion thread debating the merits of the company's environmental initiatives. Various unverified opinions shared.",
            "published_date": None,
            "score": 0.42,
        },
    ],
    "query": "company sustainability opinions",
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_mock_tavily_response(scenario: str = "supporting") -> dict:
    """Get a mock Tavily response for a given scenario.
    
    Args:
        scenario: One of:
            - "supporting": Multiple sources supporting the claim
            - "contradicting": Multiple sources contradicting the claim
            - "direct_contradiction": Clear direct contradiction from credible source
            - "timeline_contradiction": Timeline/date contradiction
            - "mixed": Mix of supporting and questioning sources
            - "empty": No search results
            - "certification_verified": Certification confirmed by sources
            - "certification_revoked": Certification revoked
            - "press_release": Tier 3 press release sources
            - "low_credibility": Tier 4 blog/social media sources
            - "tier_1": High credibility regulatory sources
            
    Returns:
        Mock Tavily API response dict
    """
    scenarios = {
        "supporting": MOCK_TAVILY_RESPONSE_SUPPORTING,
        "contradicting": MOCK_TAVILY_RESPONSE_CONTRADICTING,
        "direct_contradiction": MOCK_TAVILY_RESPONSE_DIRECT_CONTRADICTION,
        "timeline_contradiction": MOCK_TAVILY_RESPONSE_TIMELINE_CONTRADICTION,
        "mixed": MOCK_TAVILY_RESPONSE_MIXED,
        "empty": MOCK_TAVILY_RESPONSE_EMPTY,
        "certification_verified": MOCK_TAVILY_RESPONSE_CERTIFICATION_VERIFIED,
        "certification_revoked": MOCK_TAVILY_RESPONSE_CERTIFICATION_REVOKED,
        "press_release": MOCK_TAVILY_RESPONSE_PRESS_RELEASE,
        "low_credibility": MOCK_TAVILY_RESPONSE_LOW_CREDIBILITY,
        "tier_1": MOCK_TAVILY_RESPONSE_SUPPORTING_TIER_1,
    }
    return scenarios.get(scenario, MOCK_TAVILY_RESPONSE_SUPPORTING)


def get_formatted_tavily_response(scenario: str = "supporting") -> dict:
    """Get a mock Tavily response formatted as search_web_async returns it.
    
    Transforms raw Tavily response to match the format returned by
    the TavilySearchProvider.search() method.
    
    Args:
        scenario: Scenario name (see get_mock_tavily_response)
        
    Returns:
        Formatted response dict matching search_web_async output
    """
    raw_response = get_mock_tavily_response(scenario)
    
    # Transform to match search_web_async output format
    results = []
    for result in raw_response.get("results", []):
        # Extract domain from URL
        url = result.get("url", "")
        domain = ""
        if url:
            from urllib.parse import urlparse
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
            except Exception:
                pass
        
        results.append({
            "title": result.get("title", ""),
            "url": url,
            "snippet": result.get("content", ""),
            "published_date": result.get("published_date"),
            "source_domain": domain,
            "relevance_score": result.get("score"),
        })
    
    return {
        "results": results,
        "total_results": len(results),
        "query": raw_response.get("query", ""),
        "search_provider": "tavily",
    }
