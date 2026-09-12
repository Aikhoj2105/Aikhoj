#!/usr/bin/env python3
"""
============================================================
AI KHOJ — FACT CHECKER v3
Foundation Block
============================================================
"""

import os
from pathlib import Path
import json
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error

# -----------------------------------------
# Import Gemini Client
# -----------------------------------------

import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from core.gemini_client import generate_text
except ImportError as e:
    print("❌ Could not import core.gemini_client")
    print(f"Error: {e}")
    raise

# -----------------------------------------
# Configuration
# -----------------------------------------


RESEARCH_FOLDER = "outputs/research"

FACTCHECK_FOLDER = "outputs/fact_check"

RSS_URL = "https://blog.google/rss/"

DEBUG = True

# -----------------------------------------
# Logger
# -----------------------------------------

def log(message, level="INFO"):
    print(f"[{level}] {message}")

# -----------------------------------------
# Timestamp Helper
# -----------------------------------------

def current_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# -----------------------------------------
# Safe JSON Parser
# -----------------------------------------

def safe_json_load(text):

    try:
        return json.loads(text)

    except json.JSONDecodeError as e:

        log(
            f"JSON Parse Error : {e}",
            "ERROR"
        )

        return None

# -----------------------------------------
# Ensure Output Folder
# -----------------------------------------

def ensure_output_folder():

    os.makedirs(
        FACTCHECK_FOLDER,
        exist_ok=True
    )

# -----------------------------------------
# Startup Banner
# -----------------------------------------

def banner():

    print()

    print("🛡️ AI KHOJ — FACT CHECKER v3")

    print("=" * 60)

# -----------------------------------------
# Find Latest Research Report
# -----------------------------------------

def find_latest_research():

    if not os.path.exists(RESEARCH_FOLDER):
        log(
            f"Research folder not found: {RESEARCH_FOLDER}",
            "ERROR"
        )
        return None

    research_files = []

    for filename in os.listdir(RESEARCH_FOLDER):

        if filename.startswith("research_") and filename.endswith(".md"):

            full_path = os.path.join(
                RESEARCH_FOLDER,
                filename
            )

            if os.path.isfile(full_path):
                research_files.append(full_path)

    if not research_files:
        log(
            "No research report found.",
            "ERROR"
        )
        return None

    research_files.sort(
        key=os.path.getmtime,
        reverse=True
    )

    latest_file = research_files[0]

    log(f"Latest research report: {latest_file}")

    return latest_file


# -----------------------------------------
# Read Research Report
# -----------------------------------------

def read_research_report(file_path):

    if not file_path:
        return None

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()

    except OSError as e:

        log(
            f"Could not read research report: {e}",
            "ERROR"
        )

        return None

    if not content.strip():

        log(
            "Research report is empty.",
            "ERROR"
        )

        return None

    log(
        f"Research report loaded: {len(content)} characters"
    )

    return content


# -----------------------------------------
# Extract JSON From Gemini Response
# -----------------------------------------

def extract_json_object(text):

    if not text:
        return None

    text = text.strip()

    # Direct JSON
    parsed = safe_json_load(text)

    if parsed is not None:
        return parsed

    # Remove markdown code fences
    if text.startswith("```"):

        lines = text.splitlines()

        if lines:

            lines = lines[1:]

        if lines and lines[-1].strip() == "```":

            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

        parsed = safe_json_load(cleaned)

        if parsed is not None:
            return parsed

    # Try to find JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:

        candidate = text[start:end + 1]

        parsed = safe_json_load(candidate)

        if parsed is not None:
            return parsed

    # Try to find JSON array
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1 and end > start:

        candidate = text[start:end + 1]

        parsed = safe_json_load(candidate)

        if parsed is not None:
            return parsed

    log(
        "Could not extract valid JSON from Gemini response.",
        "ERROR"
    )

    return None


# -----------------------------------------
# Validate Extracted Claims
# -----------------------------------------

def validate_claims(data):

    if not isinstance(data, dict):

        log(
            "Claim response is not a JSON object.",
            "ERROR"
        )

        return []

    claims = data.get("claims")

    if not isinstance(claims, list):

        log(
            "No valid 'claims' list found.",
            "ERROR"
        )

        return []

    validated_claims = []

    for item in claims:

        if not isinstance(item, dict):
            continue

        claim_id = item.get("id")
        claim_text = item.get("claim")
        importance = item.get("importance", "medium")

        if not claim_text:
            continue

        if not isinstance(claim_text, str):
            continue

        if not claim_text.strip():
            continue

        if not isinstance(claim_id, int):

            claim_id = len(validated_claims) + 1

        importance = str(
            importance
        ).lower().strip()

        if importance not in (
            "high",
            "medium",
            "low"
        ):
            importance = "medium"

        validated_claims.append(
            {
                "id": claim_id,
                "claim": claim_text.strip(),
                "importance": importance
            }
        )

    # Re-number claims to guarantee clean IDs
    for index, claim in enumerate(
        validated_claims,
        start=1
    ):
        claim["id"] = index

    log(
        f"Validated claims: {len(validated_claims)}"
    )

    return validated_claims


# -----------------------------------------
# Claim Extraction Prompt
# -----------------------------------------

def build_claim_extraction_prompt(research_text):

    return f"""
You are the Claim Extraction module of the AI Khoj
Fact Checker v3.

Your job is to extract ONLY factual claims from the
research report below that can be checked against
original source evidence.

IMPORTANT RULES:

1. Do NOT invent facts.
2. Do NOT add information from your own knowledge.
3. Do NOT rewrite multiple independent facts into one claim.
4. Preserve important numbers, dates, names and measurements.
5. Extract claims about:
   - products
   - companies
   - technology
   - dates
   - numbers
   - funding
   - performance
   - availability
   - capabilities
   - announcements
6. Ignore opinions, speculation and general commentary.
7. A claim must be independently verifiable.
8. Keep the claim concise but complete.
9. Do not create duplicate claims.
10. Return ONLY valid JSON.

Required JSON format:

{{
  "claims": [
    {{
      "id": 1,
      "claim": "Verifiable factual claim",
      "importance": "high"
    }}
  ]
}}

Importance must be one of:

high
medium
low

RESEARCH REPORT:

{research_text}
"""


# -----------------------------------------
# Extract Claims Using Gemini
# -----------------------------------------

def extract_claims(research_text):

    if not research_text:

        log(
            "No research text available.",
            "ERROR"
        )

        return []

    log("🧠 Extracting factual claims...")

    prompt = build_claim_extraction_prompt(
        research_text
    )

    try:

        response = generate_text(
            prompt,
            timeout=120
        )

    except Exception as e:

        log(
            f"Gemini claim extraction failed: {e}",
            "ERROR"
        )

        return []

    if not response:

        log(
            "Gemini returned an empty response.",
            "ERROR"
        )

        return []

    data = extract_json_object(response)

    if data is None:

        return []

    claims = validate_claims(data)

    if not claims:

        log(
            "No valid claims extracted.",
            "ERROR"
        )

        return []

    log(
        f"✅ {len(claims)} claims extracted"
    )

    return claims


# -----------------------------------------
# Display Claims
# -----------------------------------------

def display_claims(claims):

    print()

    print("📋 EXTRACTED CLAIMS")
    print("-" * 60)

    for claim in claims:

        print(
            f"[{claim['id']}] "
            f"({claim['importance'].upper()}) "
            f"{claim['claim']}"
        )

    print("-" * 60)


# -----------------------------------------
# RSS Source Loader
# -----------------------------------------

def fetch_rss_sources():

    log("📡 Loading RSS sources...")

    request = urllib.request.Request(
        RSS_URL,
        headers={
            "User-Agent": "AI-Khoj-Fact-Checker/3.0"
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            rss_data = response.read().decode(
                "utf-8",
                errors="ignore"
            )

    except urllib.error.HTTPError as e:

        log(
            f"RSS HTTP Error {e.code}",
            "ERROR"
        )

        return []

    except urllib.error.URLError as e:

        log(
            f"RSS Network Error: {e.reason}",
            "ERROR"
        )

        return []

    except Exception as e:

        log(
            f"RSS loading failed: {e}",
            "ERROR"
        )

        return []

    return parse_rss_sources(rss_data)


# -----------------------------------------
# Parse RSS XML
# -----------------------------------------

def parse_rss_sources(rss_data):

    if not rss_data:

        return []

    try:

        import xml.etree.ElementTree as ET

        root = ET.fromstring(rss_data)

    except Exception as e:

        log(
            f"RSS XML parsing failed: {e}",
            "ERROR"
        )

        return []

    sources = []

    for item in root.iter("item"):

        title_element = item.find("title")
        link_element = item.find("link")
        description_element = item.find(
            "description"
        )

        title = ""

        url = ""

        description = ""

        if title_element is not None:
            title = (
                title_element.text or ""
            ).strip()

        if link_element is not None:
            url = (
                link_element.text or ""
            ).strip()

        if description_element is not None:
            description = (
                description_element.text or ""
            ).strip()

        if not title or not url:
            continue

        sources.append(
            {
                "id": len(sources) + 1,
                "title": title,
                "url": url,
                "description": description
            }
        )

        if len(sources) >= 10:
            break

    log(
        f"RSS sources loaded: {len(sources)}"
    )

    return sources


# -----------------------------------------
# Extract Source URL From Research Report
# -----------------------------------------

def extract_research_source_url(research_text=None):
    """
    Extract the original article URL from the latest research report.
    Supports both:
    1. SOURCE URL:
       https://example.com
    2. **Source:** https://example.com
    """

    latest_report = find_latest_research()

    if not latest_report:
        log("No research report found.", "WARNING")
        return None

    try:
        with open(
            latest_report,
            "r",
            encoding="utf-8"
        ) as f:
            content = f.read()

    except Exception as e:
        log(
            f"Could not read research report: {e}",
            "ERROR"
        )
        return None

    lines = content.splitlines()

    for index, line in enumerate(lines):

        clean_line = line.strip()

        # Format 1:
        # SOURCE URL:
        # https://example.com
        if clean_line.upper() == "SOURCE URL:":
            if index + 1 < len(lines):
                url = lines[index + 1].strip()

                if is_valid_url(url):
                    return url

        # Format 2:
        # **Source:** https://example.com
        if clean_line.lower().startswith("**source:**"):
            url = clean_line[len("**source:**"):].strip()

            if is_valid_url(url):
                return url

        # Format 3:
        # Source: https://example.com
        if clean_line.lower().startswith("source:"):
            url = clean_line[len("source:"):].strip()

            if is_valid_url(url):
                return url

    return None

# -----------------------------------------
# Validate URL
# -----------------------------------------

def is_valid_url(url):

    if not isinstance(url, str):
        return False

    url = url.strip()

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        return False

    return True


# -----------------------------------------
# Add Research Source
# -----------------------------------------

def add_research_source(
    sources,
    research_text
):

    research_url = extract_research_source_url(
        research_text
    )

    if not research_url:

        log(
            "No research source URL found."
        )

        return sources

    if not is_valid_url(research_url):

        log(
            "Research source URL is invalid.",
            "ERROR"
        )

        return sources

    # Check duplicate URL
    for source in sources:

        if source["url"].strip() == research_url:

            log(
                "Research source already exists in RSS list."
            )

            return sources

    research_source = {
        "id": 0,
        "title": "Primary Research Source",
        "url": research_url,
        "description": (
            "Original source referenced by "
            "the research report."
        )
    }

    sources.insert(
        0,
        research_source
    )

    # Re-number IDs
    for index, source in enumerate(
        sources,
        start=1
    ):

        source["id"] = index

    log(
        "✅ Primary research source added."
    )

    return sources


# -----------------------------------------
# Clean Source Metadata
# -----------------------------------------

def prepare_sources_for_matching(
    sources
):

    prepared = []

    for source in sources:

        source_id = source.get("id")

        title = source.get(
            "title",
            ""
        )

        url = source.get(
            "url",
            ""
        )

        description = source.get(
            "description",
            ""
        )

        if not isinstance(source_id, int):
            continue

        if not is_valid_url(url):
            continue

        prepared.append(
            {
                "id": source_id,
                "title": str(title).strip(),
                "url": url.strip(),
                "description": str(
                    description
                ).strip()[:1000]
            }
        )

    return prepared


# -----------------------------------------
# Build Source Matching Prompt
# -----------------------------------------

def build_source_matching_prompt(
    claims,
    sources
):

    claims_text = json.dumps(
        claims,
        ensure_ascii=False,
        indent=2
    )

    sources_text = json.dumps(
        sources,
        ensure_ascii=False,
        indent=2
    )

    return f"""
You are the Source Matching module of the
AI Khoj Fact Checker v3.

Your task is to identify which supplied sources
are relevant to each factual claim.

IMPORTANT:

1. Use ONLY the supplied claims and sources.
2. Do NOT use your own knowledge.
3. Do NOT invent source IDs.
4. A source should be selected only when its
   title, URL or description indicates that it
   may contain evidence relevant to the claim.
5. It is acceptable to return no source.
6. Do NOT assume that a source proves a claim.
7. This stage only finds potentially relevant
   sources. Actual verification happens later.
8. Multiple sources may be selected.
9. If no relevant source exists, use an empty
   source_ids list.
10. Return ONLY valid JSON.

Required format:

{{
  "matches": [
    {{
      "claim_id": 1,
      "source_ids": [1],
      "reason": "Short explanation"
    }}
  ]
}}

CLAIMS:

{claims_text}

AVAILABLE SOURCES:

{sources_text}
"""


# -----------------------------------------
# Validate Source Matches
# -----------------------------------------

def validate_source_matches(
    data,
    claims,
    sources
):

    if not isinstance(data, dict):

        log(
            "Source matching response is not an object.",
            "ERROR"
        )

        return []

    matches = data.get("matches")

    if not isinstance(matches, list):

        log(
            "No valid 'matches' list found.",
            "ERROR"
        )

        return []

    valid_claim_ids = {
        claim["id"]
        for claim in claims
    }

    valid_source_ids = {
        source["id"]
        for source in sources
    }

    validated = []

    for match in matches:

        if not isinstance(
            match,
            dict
        ):
            continue

        claim_id = match.get(
            "claim_id"
        )

        source_ids = match.get(
            "source_ids",
            []
        )

        reason = match.get(
            "reason",
            ""
        )

        if claim_id not in valid_claim_ids:
            continue

        if not isinstance(
            source_ids,
            list
        ):
            source_ids = []

        clean_source_ids = []

        for source_id in source_ids:

            if source_id in valid_source_ids:

                if source_id not in clean_source_ids:

                    clean_source_ids.append(
                        source_id
                    )

        validated.append(
            {
                "claim_id": claim_id,
                "source_ids": clean_source_ids,
                "reason": str(
                    reason
                ).strip()
            }
        )

    # Make sure every claim gets an entry
    existing_claim_ids = {
        item["claim_id"]
        for item in validated
    }

    for claim in claims:

        if claim["id"] not in existing_claim_ids:

            validated.append(
                {
                    "claim_id": claim["id"],
                    "source_ids": [],
                    "reason": (
                        "No relevant source "
                        "identified."
                    )
                }
            )

    validated.sort(
        key=lambda item: item["claim_id"]
    )

    return validated


# -----------------------------------------
# Match Claims With Sources
# -----------------------------------------

def match_claims_to_sources(
    claims,
    sources
):

    if not claims:

        log(
            "No claims available for matching.",
            "ERROR"
        )

        return []

    if not sources:

        log(
            "No sources available for matching.",
            "ERROR"
        )

        return [
            {
                "claim_id": claim["id"],
                "source_ids": [],
                "reason": "No sources available."
            }
            for claim in claims
        ]

    log(
        "🔗 Matching claims with sources..."
    )

    prepared_sources = prepare_sources_for_matching(
        sources
    )

    prompt = build_source_matching_prompt(
        claims,
        prepared_sources
    )

    try:

        response = generate_text(
            prompt,
            timeout=120
        )

    except Exception as e:

        log(
            f"Source matching failed: {e}",
            "ERROR"
        )

        return [
            {
                "claim_id": claim["id"],
                "source_ids": [],
                "reason": (
                    "Source matching failed."
                )
            }
            for claim in claims
        ]

    if not response:

        log(
            "Gemini returned empty source matching response.",
            "ERROR"
        )

        return [
            {
                "claim_id": claim["id"],
                "source_ids": [],
                "reason": (
                    "Empty Gemini response."
                )
            }
            for claim in claims
        ]

    data = extract_json_object(
        response
    )

    if data is None:

        return [
            {
                "claim_id": claim["id"],
                "source_ids": [],
                "reason": (
                    "Invalid JSON response."
                )
            }
            for claim in claims
        ]

    validated = validate_source_matches(
        data,
        claims,
        prepared_sources
    )

    matched_count = sum(
        1
        for item in validated
        if item["source_ids"]
    )

    log(
        f"✅ Source matching complete: "
        f"{matched_count}/{len(claims)} claims matched"
    )

    return validated


# -----------------------------------------
# Display Source Matches
# -----------------------------------------

def display_source_matches(
    matches
):

    print()

    print("🔗 SOURCE MATCHING RESULTS")
    print("-" * 60)

    for match in matches:

        claim_id = match["claim_id"]

        source_ids = match["source_ids"]

        if source_ids:

            source_text = ", ".join(
                f"Source {source_id}"
                for source_id in source_ids
            )

        else:

            source_text = "NONE"

        print(
            f"Claim {claim_id} → "
            f"{source_text}"
        )

        if match.get("reason"):

            print(
                f"   Reason: {match['reason']}"
            )

    print("-" * 60)


# -----------------------------------------
# Test Main
# -----------------------------------------
# ============================================================
# BLOCK 4 — ORIGINAL SOURCE FETCH + EVIDENCE EXTRACTION
# ============================================================

import re
import html
import urllib.request
import urllib.error


def clean_html_text(raw_html):
    """
    Convert raw HTML into readable plain text.
    """

    if not raw_html:
        return ""

    text = raw_html

    # Remove scripts and styles
    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove HTML comments
    text = re.sub(
        r"<!--.*?-->",
        " ",
        text,
        flags=re.DOTALL
    )

    # Replace common block elements with spaces
    text = re.sub(
        r"</?(p|div|br|li|h[1-6]|section|article|header|footer|main)[^>]*>",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    # Remove remaining HTML tags
    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # Decode HTML entities
    text = html.unescape(text)

    # Normalize whitespace
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text
    )

    return text.strip()


def fetch_original_source(url, timeout=30):
    """
    Fetch an original webpage and return cleaned text.
    """

    if not is_valid_url(url):
        log(
            f"Invalid source URL: {url}",
            "WARNING"
        )
        return None

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Linux; Android) "
                "AppleWebKit/537.36 "
                "Chrome/120 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml"
        },
        method="GET"
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            raw_data = response.read()

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            if "text/html" not in content_type.lower():
                log(
                    f"Unexpected content type for {url}: "
                    f"{content_type}",
                    "WARNING"
                )

            charset = "utf-8"

            match = re.search(
                r"charset=([^\s;]+)",
                content_type,
                flags=re.IGNORECASE
            )

            if match:
                charset = match.group(1).strip(
                    "\"'"
                )

            try:
                raw_html = raw_data.decode(
                    charset,
                    errors="replace"
                )
            except LookupError:
                raw_html = raw_data.decode(
                    "utf-8",
                    errors="replace"
                )

    except urllib.error.HTTPError as e:
        log(
            f"Source HTTP Error {e.code}: {url}",
            "WARNING"
        )
        return None

    except urllib.error.URLError as e:
        log(
            f"Source Network Error: {e.reason}",
            "WARNING"
        )
        return None

    except TimeoutError:
        log(
            f"Source fetch timeout: {url}",
            "WARNING"
        )
        return None

    except Exception as e:
        log(
            f"Source fetch failed: {e}",
            "WARNING"
        )
        return None

    cleaned_text = clean_html_text(raw_html)

    if not cleaned_text:
        log(
            f"No readable text extracted: {url}",
            "WARNING"
        )
        return None

    log(
        f"Source fetched successfully: "
        f"{len(cleaned_text)} characters"
    )

    return cleaned_text


def limit_source_text(text, max_chars=30000):
    """
    Prevent extremely large webpages from being sent
    to Gemini in later blocks.
    """

    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    log(
        f"Source text truncated: "
        f"{len(text)} → {max_chars} characters",
        "WARNING"
    )

    return text[:max_chars]


def fetch_matched_sources(
    sources,
    source_matches
):
    """
    Fetch every unique source referenced by the
    source-matching results.
    """

    matched_source_ids = set()

    for match in source_matches:

        for source_id in match.get(
            "source_ids",
            []
        ):
            try:
                matched_source_ids.add(
                    int(source_id)
                )
            except (TypeError, ValueError):
                continue

    source_map = {}

    for source in sources:

        try:
            source_id = int(
                source.get("id")
            )
        except (TypeError, ValueError):
            continue

        source_map[source_id] = source

    fetched_sources = {}

    log(
        f"📥 Fetching matched original sources..."
    )

    for source_id in sorted(
        matched_source_ids
    ):

        source = source_map.get(source_id)

        if not source:
            log(
                f"Source ID {source_id} not found.",
                "WARNING"
            )
            continue

        url = source.get(
            "url",
            ""
        ).strip()

        title = source.get(
            "title",
            "Untitled Source"
        )

        log(
            f"Fetching Source {source_id}: "
            f"{title}"
        )

        article_text = fetch_original_source(
            url
        )

        if article_text:

            fetched_sources[source_id] = {
                "id": source_id,
                "title": title,
                "url": url,
                "text": limit_source_text(
                    article_text
                )
            }

    log(
        f"✅ Original sources fetched: "
        f"{len(fetched_sources)}/"
        f"{len(matched_source_ids)}"
    )

    return fetched_sources


def build_evidence_dataset(
    claims,
    source_matches,
    fetched_sources
):
    """
    Prepare claim → source → evidence structure
    for the next verification block.
    """

    evidence_dataset = []

    source_match_map = {}

    for match in source_matches:

        try:
            claim_id = int(
                match.get("claim_id")
            )
        except (TypeError, ValueError):
            continue

        source_match_map[claim_id] = match

    for claim in claims:

        try:
            claim_id = int(
                claim.get("id")
            )
        except (TypeError, ValueError):
            continue

        match = source_match_map.get(
            claim_id,
            {}
        )

        source_ids = match.get(
            "source_ids",
            []
        )

        evidence_sources = []

        for source_id in source_ids:

            try:
                source_id = int(source_id)
            except (TypeError, ValueError):
                continue

            source = fetched_sources.get(
                source_id
            )

            if not source:
                continue

            evidence_sources.append({
                "source_id": source_id,
                "title": source.get(
                    "title",
                    ""
                ),
                "url": source.get(
                    "url",
                    ""
                ),
                "evidence_text": source.get(
                    "text",
                    ""
                )
            })

        evidence_dataset.append({
            "claim_id": claim_id,
            "claim": claim.get(
                "claim",
                ""
            ),
            "priority": claim.get(
                "priority",
                "MEDIUM"
            ),
            "sources": evidence_sources
        })

    log(
        f"✅ Evidence dataset prepared: "
        f"{len(evidence_dataset)} claims"
    )

    return evidence_dataset


def display_evidence_summary(
    evidence_dataset
):
    """
    Display a compact evidence summary.
    """

    print()
    print("📚 EVIDENCE DATASET")
    print("-" * 60)

    for item in evidence_dataset:

        claim_id = item.get(
            "claim_id"
        )

        sources = item.get(
            "sources",
            []
        )

        print(
            f"Claim {claim_id} → "
            f"{len(sources)} source(s)"
        )

        for source in sources:

            evidence_text = source.get(
                "evidence_text",
                ""
            )

            print(
                f"   Source {source.get('source_id')} "
                f"→ {len(evidence_text)} chars"
            )

    print("-" * 60)
# ============================================================
# BLOCK 4A — ORIGINAL SOURCE FETCH
# ============================================================

import re
import html
import urllib.request
import urllib.error



# ============================================================
# BLOCK 5A — EVIDENCE VERIFICATION
# ============================================================

def build_verification_prompt(evidence_dataset):
    """
    Build a Gemini prompt for claim verification.
    """

    prompt = """
You are the Evidence Verification Agent for AI Khoj.

Your job is to verify factual claims using ONLY the supplied
original-source evidence.

For each claim:

1. Compare the claim against the supplied evidence.
2. Decide exactly one status:
   - SUPPORTED
   - CONFLICTING
   - NOT ENOUGH EVIDENCE
3. Explain the decision briefly.
4. Do not use outside knowledge.
5. Do not invent facts.
6. If the source is only a company statement, treat it as
   evidence of what the company says, not independent proof.
7. Numbers, dates, versions, prices or performance figures
   require direct evidence.

Return ONLY valid JSON.

Required JSON format:

{
  "verifications": [
    {
      "claim_id": 1,
      "status": "SUPPORTED",
      "confidence": "HIGH",
      "reason": "Brief evidence-based explanation.",
      "source_ids": [1]
    }
  ]
}

EVIDENCE DATASET:
"""

    for item in evidence_dataset:

        claim_id = item.get(
            "claim_id"
        )

        claim_text = item.get(
            "claim",
            ""
        )

        priority = item.get(
            "priority",
            "MEDIUM"
        )

        prompt += f"""

CLAIM {claim_id}
Priority: {priority}
Claim: {claim_text}

EVIDENCE:
"""

        sources = item.get(
            "sources",
            []
        )

        if not sources:
            prompt += "No matched evidence source available.\n"
            continue

        for source in sources:

            source_id = source.get(
                "source_id"
            )

            title = source.get(
                "title",
                "Untitled Source"
            )

            url = source.get(
                "url",
                ""
            )

            evidence_text = source.get(
                "evidence_text",
                ""
            )

            prompt += f"""
SOURCE {source_id}
Title: {title}
URL: {url}

Evidence:
{evidence_text}
"""

    return prompt


def validate_verifications(data):
    """
    Validate Gemini verification output.
    """

    if not isinstance(data, dict):
        return None

    verifications = data.get(
        "verifications"
    )

    if not isinstance(
        verifications,
        list
    ):
        return None

    valid_statuses = {
        "SUPPORTED",
        "CONFLICTING",
        "NOT ENOUGH EVIDENCE"
    }

    valid_confidence = {
        "HIGH",
        "MEDIUM",
        "LOW"
    }

    cleaned = []

    for item in verifications:

        if not isinstance(
            item,
            dict
        ):
            continue

        claim_id = item.get(
            "claim_id"
        )

        status = str(
            item.get(
                "status",
                ""
            )
        ).strip().upper()

        confidence = str(
            item.get(
                "confidence",
                ""
            )
        ).strip().upper()

        reason = str(
            item.get(
                "reason",
                ""
            )
        ).strip()

        source_ids = item.get(
            "source_ids",
            []
        )

        if status not in valid_statuses:
            continue

        if confidence not in valid_confidence:
            confidence = "LOW"

        if not isinstance(
            source_ids,
            list
        ):
            source_ids = []

        cleaned_source_ids = []

        for source_id in source_ids:
            try:
                cleaned_source_ids.append(
                    int(source_id)
                )
            except (
                TypeError,
                ValueError
            ):
                continue

        cleaned.append({
            "claim_id": claim_id,
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "source_ids": cleaned_source_ids
        })

    return cleaned


# ============================================================
# END BLOCK 5A
# ============================================================



# ============================================================
# BLOCK 5B — GEMINI EVIDENCE VERIFICATION
# ============================================================

def run_evidence_verification(evidence_dataset):
    """
    Send the evidence dataset to Gemini and validate
    the returned verification results.
    """

    if not evidence_dataset:
        log(
            "No evidence dataset available for verification.",
            "WARNING"
        )
        return []

    prompt = build_verification_prompt(
        evidence_dataset
    )

    log(
        "🔎 Sending evidence dataset to Gemini..."
    )

    try:
        response_text = generate_text(
            prompt,
            timeout=180
        )

    except Exception as e:
        log(
            f"Evidence verification failed: {e}",
            "ERROR"
        )
        return []

    if not response_text:
        log(
            "Gemini returned an empty verification response.",
            "ERROR"
        )
        return []

    parsed_data = extract_json_object(
        response_text
    )

    if parsed_data is None:
        log(
            "Could not extract valid JSON from Gemini response.",
            "ERROR"
        )
        return []

    verifications = validate_verifications(
        parsed_data
    )

    if verifications is None:
        log(
            "Gemini verification JSON failed validation.",
            "ERROR"
        )
        return []

    log(
        f"✅ Evidence verification complete: "
        f"{len(verifications)} results"
    )

    return verifications


def display_verification_results(
    verifications
):
    """
    Display compact verification results.
    """

    print()
    print("🔎 EVIDENCE VERIFICATION")
    print("-" * 60)

    if not verifications:
        print(
            "No verification results available."
        )
        print("-" * 60)
        return

    for item in verifications:

        claim_id = item.get(
            "claim_id",
            "?"
        )

        status = item.get(
            "status",
            "UNKNOWN"
        )

        confidence = item.get(
            "confidence",
            "LOW"
        )

        reason = item.get(
            "reason",
            ""
        )

        source_ids = item.get(
            "source_ids",
            []
        )

        print(
            f"Claim {claim_id} → "
            f"{status} "
            f"({confidence})"
        )

        if source_ids:
            print(
                f"   Sources: {source_ids}"
            )

        if reason:
            print(
                f"   Reason: {reason}"
            )

        print()

    print("-" * 60)


# ============================================================
# END BLOCK 5B
# ============================================================



# ============================================================
# BLOCK 5C — SAVE VERIFICATION REPORT
# ============================================================

def save_verification_report(verifications, evidence_dataset, quality_summary=None):
    """Save fact-check verification results as Markdown."""

    if not verifications:
        log(
            "No verification results to save.",
            "WARNING"
        )
        return None

    output_dir = Path(
        "outputs/fact_check"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = current_timestamp().replace(
        ":",
        ""
    ).replace(
        "-",
        ""
    ).replace(
        " ",
        "_"
    )

    output_path = (
        output_dir /
        f"fact_check_{timestamp}.md"
    )

    evidence_map = {}

    for item in evidence_dataset:
        evidence_map[
            item.get("claim_id")
        ] = item

    lines = []

    lines.append(
        "# AI Khoj Fact Check Report"
    )
    lines.append("")
    lines.append(
        f"**Generated:** {current_timestamp()}"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    if quality_summary:
        lines.append("## Quality Gate Summary")
        lines.append("")

        lines.append(
            f"**Total Claims:** "
            f"{quality_summary.get('total_claims', 0)}"
        )
        lines.append("")

        lines.append(
            f"**Supported:** "
            f"{quality_summary.get('supported', 0)}"
        )
        lines.append("")

        lines.append(
            f"**Conflicting:** "
            f"{quality_summary.get('conflicting', 0)}"
        )
        lines.append("")

        lines.append(
            f"**Not Enough Evidence:** "
            f"{quality_summary.get('not_enough_evidence', 0)}"
        )
        lines.append("")

        lines.append(
            f"**High Confidence:** "
            f"{quality_summary.get('high_confidence', 0)}"
        )
        lines.append("")

        lines.append(
            f"**Medium Confidence:** "
            f"{quality_summary.get('medium_confidence', 0)}"
        )
        lines.append("")

        lines.append(
            f"**Low Confidence:** "
            f"{quality_summary.get('low_confidence', 0)}"
        )
        lines.append("")

        lines.append(
            f"**Script-Ready Claims:** "
            f"{quality_summary.get('script_ready_claims', [])}"
        )
        lines.append("")

        lines.append(
            f"**Review Required:** "
            f"{quality_summary.get('review_required_claims', [])}"
        )
        lines.append("")

        lines.append("---")
        lines.append("")

    if quality_summary:
        script_ready_ids = quality_summary.get(
            "script_ready_claims",
            []
        )

        if script_ready_ids:
            lines.append(
                "## Script-Ready Claims"
            )
            lines.append("")

            for claim_id in script_ready_ids:
                for verification in verifications:
                    try:
                        verification_id = int(
                            verification.get("claim_id")
                        )
                    except (TypeError, ValueError):
                        continue

                    if verification_id != int(claim_id):
                        continue

                    evidence_item = evidence_map.get(
                        verification_id,
                        {}
                    )

                    lines.append(
                        f"### Claim {verification_id}"
                    )
                    lines.append("")

                    lines.append(
                        f"**Claim:** "
                        f"{evidence_item.get('claim', '')}"
                    )
                    lines.append("")

                    lines.append(
                        f"**Priority:** "
                        f"{evidence_item.get('priority', 'MEDIUM')}"
                    )
                    lines.append("")

                    lines.append(
                        f"**Status:** "
                        f"{verification.get('status', '')}"
                    )
                    lines.append("")

                    lines.append(
                        f"**Confidence:** "
                        f"{verification.get('confidence', '')}"
                    )
                    lines.append("")

                    source_ids = verification.get(
                        "source_ids",
                        []
                    )

                    if source_ids:
                        lines.append(
                            f"**Source IDs:** "
                            f"{source_ids}"
                        )
                        lines.append("")

                    break

            lines.append("---")
            lines.append("")

    for verification in verifications:

        claim_id = verification.get(
            "claim_id",
            "?"
        )

        evidence_item = evidence_map.get(
            claim_id,
            {}
        )

        claim = evidence_item.get(
            "claim",
            ""
        )

        priority = evidence_item.get(
            "priority",
            "MEDIUM"
        )

        status = verification.get(
            "status",
            "UNKNOWN"
        )

        confidence = verification.get(
            "confidence",
            "LOW"
        )

        reason = verification.get(
            "reason",
            ""
        )

        source_ids = verification.get(
            "source_ids",
            []
        )

        lines.append(
            f"## Claim {claim_id}"
        )
        lines.append("")

        lines.append(
            f"**Claim:** {claim}"
        )
        lines.append("")

        lines.append(
            f"**Priority:** {priority}"
        )
        lines.append("")

        lines.append(
            f"**Status:** {status}"
        )
        lines.append("")

        lines.append(
            f"**Confidence:** {confidence}"
        )
        lines.append("")

        lines.append(
            f"**Reason:** {reason}"
        )
        lines.append("")

        if source_ids:
            lines.append(
                "**Sources:**"
            )
            lines.append("")

            for source_id in source_ids:

                source_info = None

                for source in evidence_item.get(
                    "sources",
                    []
                ):
                    if source.get(
                        "source_id"
                    ) == source_id:
                        source_info = source
                        break

                if source_info:
                    title = source_info.get(
                        "title",
                        "Untitled Source"
                    )

                    url = source_info.get(
                        "url",
                        ""
                    )

                    lines.append(
                        f"- Source {source_id}: {title}"
                    )

                    if url:
                        lines.append(
                            f"  - URL: {url}"
                        )
                else:
                    lines.append(
                        f"- Source {source_id}"
                    )

            lines.append("")

        lines.append("---")
        lines.append("")

    report_text = "\n".join(lines)

    output_path.write_text(
        report_text,
        encoding="utf-8"
    )

    log(
        f"✅ Fact-check report saved: {output_path}"
    )

    return str(output_path)


# ============================================================
# END BLOCK 5C
# ============================================================



# ============================================================
# BLOCK 6A — FACT-CHECK QUALITY GATE
# ============================================================

def build_quality_gate(verifications):
    """
    Analyze verification results and create a quality summary.
    No Gemini/API call is required.
    """

    summary = {
        "total_claims": 0,
        "supported": 0,
        "conflicting": 0,
        "not_enough_evidence": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0,
        "script_ready_claims": [],
        "review_required_claims": []
    }

    if not verifications:
        return summary

    summary["total_claims"] = len(
        verifications
    )

    for item in verifications:

        claim_id = item.get(
            "claim_id"
        )

        status = str(
            item.get("status", "")
        ).strip().upper()

        confidence = str(
            item.get("confidence", "")
        ).strip().upper()

        if status == "SUPPORTED":
            summary["supported"] += 1

        elif status == "CONFLICTING":
            summary["conflicting"] += 1

        elif status == "NOT ENOUGH EVIDENCE":
            summary["not_enough_evidence"] += 1

        if confidence == "HIGH":
            summary["high_confidence"] += 1

        elif confidence == "MEDIUM":
            summary["medium_confidence"] += 1

        elif confidence == "LOW":
            summary["low_confidence"] += 1

        # Only supported claims can be directly used
        # as script-ready factual claims.
        if (
            status == "SUPPORTED"
            and confidence in {
                "HIGH",
                "MEDIUM"
            }
        ):
            summary[
                "script_ready_claims"
            ].append(claim_id)

        else:
            summary[
                "review_required_claims"
            ].append(claim_id)

    return summary


def display_quality_gate(summary):
    """
    Display the fact-check quality gate summary.
    """

    print()
    print("🛡️ FACT-CHECK QUALITY GATE")
    print("-" * 60)

    print(
        f"Total Claims       : "
        f"{summary.get('total_claims', 0)}"
    )

    print(
        f"SUPPORTED          : "
        f"{summary.get('supported', 0)}"
    )

    print(
        f"CONFLICTING        : "
        f"{summary.get('conflicting', 0)}"
    )

    print(
        f"NOT ENOUGH EVIDENCE: "
        f"{summary.get('not_enough_evidence', 0)}"
    )

    print()

    print(
        f"HIGH Confidence    : "
        f"{summary.get('high_confidence', 0)}"
    )

    print(
        f"MEDIUM Confidence  : "
        f"{summary.get('medium_confidence', 0)}"
    )

    print(
        f"LOW Confidence     : "
        f"{summary.get('low_confidence', 0)}"
    )

    print()

    print(
        "Script-Ready Claims:",
        summary.get(
            "script_ready_claims",
            []
        )
    )

    print(
        "Review Required:",
        summary.get(
            "review_required_claims",
            []
        )
    )

    print("-" * 60)


# ============================================================
# END BLOCK 6A
# ============================================================


def extract_script_ready_claims(
    verifications,
    evidence_dataset
):
    """
    Extract claims that passed the fact-check quality gate
    and are safe to provide to the script writer.

    Script-ready criteria:
    - Status must be SUPPORTED
    - Confidence must be HIGH or MEDIUM

    No Gemini/API call is required.
    """

    if not verifications:
        return []

    evidence_map = {}

    for item in evidence_dataset:
        try:
            claim_id = int(
                item.get("claim_id")
            )
        except (TypeError, ValueError):
            continue

        evidence_map[claim_id] = item

    script_ready_claims = []

    for verification in verifications:
        try:
            claim_id = int(
                verification.get("claim_id")
            )
        except (TypeError, ValueError):
            continue

        status = str(
            verification.get("status", "")
        ).strip().upper()

        confidence = str(
            verification.get("confidence", "")
        ).strip().upper()

        if status != "SUPPORTED":
            continue

        if confidence not in {
            "HIGH",
            "MEDIUM"
        }:
            continue

        evidence_item = evidence_map.get(
            claim_id,
            {}
        )

        script_ready_claims.append({
            "claim_id": claim_id,
            "claim": evidence_item.get(
                "claim",
                ""
            ),
            "priority": evidence_item.get(
                "priority",
                "MEDIUM"
            ),
            "status": status,
            "confidence": confidence,
            "reason": verification.get(
                "reason",
                ""
            ),
            "source_ids": verification.get(
                "source_ids",
                []
            ),
            "sources": evidence_item.get(
                "sources",
                []
            )
        })

    return script_ready_claims


def display_script_ready_claims(
    script_ready_claims
):
    """
    Display claims approved for script writing.
    """

    print()
    print("📝 SCRIPT-READY CLAIMS")
    print("-" * 60)

    if not script_ready_claims:
        print(
            "No script-ready claims available."
        )
        print("-" * 60)
        return

    for item in script_ready_claims:
        print(
            f"Claim {item.get('claim_id', '?')} "
            f"→ {item.get('status', 'UNKNOWN')} "
            f"({item.get('confidence', 'LOW')})"
        )

        print(
            f"   Priority: "
            f"{item.get('priority', 'MEDIUM')}"
        )

        print(
            f"   Claim: "
            f"{item.get('claim', '')}"
        )

        if item.get("source_ids"):
            print(
                f"   Sources: "
                f"{item.get('source_ids')}"
            )

        print()

    print("-" * 60)

def main():
        banner()

        ensure_output_folder()

        log("Foundation Loaded")

        log("Gemini Client Imported")

        log("Output Folder Ready")

        # -------------------------------------
        # Research
        # -------------------------------------

        research_file = find_latest_research()

        if not research_file:

            log(
                "Stopping because no research report exists.",
                "ERROR"
            )

            return

        research_text = read_research_report(
            research_file
        )

        if not research_text:

            log(
                "Stopping because research could not be loaded.",
                "ERROR"
            )

            return

        # -------------------------------------
        # Claims
        # -------------------------------------

        claims = extract_claims(
            research_text
        )

        if not claims:

            log(
                "Stopping because no claims were extracted.",
                "ERROR"
            )

            return

        display_claims(
            claims
        )

        # -------------------------------------
        # Sources
        # -------------------------------------

        sources = fetch_rss_sources()

        sources = add_research_source(
            sources,
            research_text
        )

        sources = prepare_sources_for_matching(
            sources
        )

        log(
            f"Total unique sources: {len(sources)}"
        )

        # -------------------------------------
        # Source Matching
        # -------------------------------------

        matches = match_claims_to_sources(
            claims,
            sources
        )

        display_source_matches(
            matches
        )
        fetched_sources = fetch_matched_sources(
            sources,
            matches
        )
        evidence_dataset = build_evidence_dataset(
            claims,
            matches,
            fetched_sources
        )

        display_evidence_summary(
            evidence_dataset
        )

        # -------------------------------------
        # Evidence Verification
        # -------------------------------------

        verifications = run_evidence_verification(
            evidence_dataset
        )

        display_verification_results(
            verifications
        )

        # -------------------------------------
        # Fact-Check Quality Gate
        # -------------------------------------

        quality_summary = build_quality_gate(
            verifications
        )

        display_quality_gate(
            quality_summary
        )

        # -------------------------------------
        # Save Fact-Check Report
        # -------------------------------------

        report_path = save_verification_report(
            verifications,
            evidence_dataset,
            quality_summary
        )

        if report_path:
            log(
                f"Fact-check report ready: {report_path}"
            )

        print()
        print("📥 FETCHED SOURCE SUMMARY")
        print("-" * 60)

        for source_id, source in fetched_sources.items():
            print(
                f"Source {source_id} → "
                f"{source.get('title', 'Untitled')} "
                f"→ {len(source.get('text', ''))} chars"
            )

        print("-" * 60)

        print()

        log(
            "Timestamp : " + current_timestamp()
        )

        print()

        print("✅ Block 3 Ready")



    # -----------------------------------------

if __name__ == "__main__":
    main()

# -----------------------------------------

