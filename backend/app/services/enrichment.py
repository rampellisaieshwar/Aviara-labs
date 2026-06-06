import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# List of common public/free email domains to detect personal accounts
PERSONAL_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "aol.com", "zoho.com", "protonmail.com", "proton.me", "mail.com",
    "yandex.com", "gmx.com", "live.com"
}

# Pre-mapped company enrichment database for testing
COMPANY_KNOWLEDGE_BASE = {
    "google.com": {
        "company_size": "10,000+",
        "industry": "Technology / Internet",
        "official_name": "Google LLC"
    },
    "microsoft.com": {
        "company_size": "10,000+",
        "industry": "Technology / Software",
        "official_name": "Microsoft Corporation"
    },
    "stripe.com": {
        "company_size": "5,000 - 10,000",
        "industry": "Financial Technology (Fintech)",
        "official_name": "Stripe, Inc."
    },
    "meta.com": {
        "company_size": "10,000+",
        "industry": "Social Media / Technology",
        "official_name": "Meta Platforms, Inc."
    },
    "acme.com": {
        "company_size": "100 - 500",
        "industry": "Manufacturing & Logistics",
        "official_name": "Acme Inc."
    },
    "netflix.com": {
        "company_size": "5,000 - 10,000",
        "industry": "Entertainment / Streaming",
        "official_name": "Netflix, Inc."
    },
    "airbnb.com": {
        "company_size": "5,000 - 10,000",
        "industry": "Hospitality / Travel",
        "official_name": "Airbnb, Inc."
    }
}

class EnrichmentService:
    @staticmethod
    def extract_domain(email: str) -> Optional[str]:
        """Extract the domain name from an email address."""
        if not email or "@" not in email:
            return None
        parts = email.split("@")
        return parts[-1].strip().lower()

    @classmethod
    async def enrich_lead(cls, name: Optional[str], email: str, company: Optional[str] = None) -> Dict[str, Any]:
        """
        Enriches a lead using email domain parsing and heuristic lookups.
        
        In production, this would make external API calls to Apollo.io, Clearbit, or Lusha.
        We simulate this with a structured, deterministic lookup strategy.
        """
        logger.info(f"Enriching lead: name={name}, email={email}, company={company}")
        
        # Determine company name or fallback to domain name
        domain = cls.extract_domain(email)
        company_name = company or ""
        
        # Standardize company size & industry placeholders
        company_size = "Unknown"
        industry = "Unknown"
        linkedin_url = None
        
        # 1. Parse name for LinkedIn Profile generation
        clean_name = "john-doe"
        if name:
            clean_name = re.sub(r'[^a-zA-Z0-9\s-]', '', name).strip().replace(" ", "-").lower()
            linkedin_url = f"https://linkedin.com/in/{clean_name}"
        else:
            linkedin_url = "https://linkedin.com/in/anonymous-lead"
            
        # 2. Check if the domain is a corporate domain
        if domain and domain not in PERSONAL_EMAIL_DOMAINS:
            # Check knowledge base first
            if domain in COMPANY_KNOWLEDGE_BASE:
                kb_data = COMPANY_KNOWLEDGE_BASE[domain]
                company_size = kb_data["company_size"]
                industry = kb_data["industry"]
                if not company_name:
                    company_name = kb_data["official_name"]
            else:
                # Deterministic fallback generator for unknown corporate domains
                # E.g. testcompany.com -> Industry: Business Services, Size: 10-50
                domain_parts = domain.split(".")
                display_name = domain_parts[0].capitalize() if domain_parts else "Corporation"
                if not company_name:
                    company_name = f"{display_name} Inc."
                
                # Use string hashing to return stable, realistic mock data for any unknown corporate domain
                hash_val = sum(ord(char) for char in domain)
                sizes = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5000+"]
                industries = ["Software Development", "Financial Services", "Healthcare", "E-Commerce", "Marketing & Advertising", "Real Estate"]
                
                company_size = sizes[hash_val % len(sizes)]
                industry = industries[hash_val % len(industries)]
                
            # Update linkedin URL with company details if we have it
            linkedin_url = f"{linkedin_url}?org={company_name.lower().replace(' ', '-')}"
        else:
            # It's a personal email domain (gmail.com, etc.)
            # If the user specified a company, we attempt to enrich from it
            if company_name:
                company_size = "50-200 (Estimated)"
                industry = "Professional Services"
                linkedin_url = f"{linkedin_url}?org={company_name.lower().replace(' ', '-')}"
            else:
                company_size = "Individual / Freelancer"
                industry = "Consumer"

        logger.info(f"Enrichment result: linkedin_url={linkedin_url}, company_size={company_size}, industry={industry}")
        return {
            "linkedin_url": linkedin_url,
            "company_size": company_size,
            "industry": industry
        }
