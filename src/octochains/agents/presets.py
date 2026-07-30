#==============================================================================
#
# Copyright (c) 2026 Ahmad Varasteh (octochains). All rights reserved.
# Licensed under the Business Source License 1.1 (the "License");
#
# you may not use this file except in compliance with the License.
#
#==============================================================================

import importlib.resources
from typing import List, Optional, Type
from pydantic import BaseModel

from octochains.base import LLMCallable
from octochains.skills import Skill
from octochains.agents.skilled_agent import SkilledAgent

def _load_skills(package_path: str, *skill_names: str) -> List[Skill]:
    """
    Internal helper to load SKILL.md files from the package data safely.
    """
    loaded_skills = []
    resource_module = importlib.resources.files(package_path)
    
    for name in skill_names:
        skill_file = resource_module / name / "SKILL.md"
        raw_text = skill_file.read_text(encoding="utf-8")
        loaded_skills.append(Skill.from_string(raw_text))
        
    return loaded_skills

# =============================================================================
# OFFICIAL PRESET FACTORIES
# =============================================================================

def data_sovereignty_auditor(llm_callable: LLMCallable, 
                             extra_skills: Optional[List[Skill]] = None,
                             output_format: Optional[Type[BaseModel]] = None,
                             input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.legal", "gdpr-review")
    return SkilledAgent(
        role="Data Sovereignty Auditor",
        goal=r"Focus 100% on geographic data flows, cross-border transfers, and GDPR Article 5/17 storage mandates.",
        input_description=input_description or r"Architecture proposals detailing database locations and data retention.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def ai_risk_assessor(llm_callable: LLMCallable, 
                     extra_skills: Optional[List[Skill]] = None,
                     output_format: Optional[Type[BaseModel]] = None,
                     input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.legal", "eu-ai-act-tiering")
    return SkilledAgent(
        role="AI Risk Assessor",
        goal=r"Determine the exact regulatory tier under the EU AI Act based on system capabilities and human interaction.",
        input_description=input_description or r"Use-case definitions, automation workflows, and user interaction designs.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def phi_sanitizer(llm_callable: LLMCallable, 
                  extra_skills: Optional[List[Skill]] = None,
                  output_format: Optional[Type[BaseModel]] = None,
                  input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.legal", "dsgvo-health-data-compliance")
    return SkilledAgent(
        role="Health Data Compliance Officer",
        goal=r"Hunt exclusively for the mishandling of Special Category Data (Sozialdaten/PHI) and ensure strict anonymization.",
        input_description=input_description or r"Data schemas, user input fields, and logging mechanisms.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def licensing_reviewer(llm_callable: LLMCallable, 
                       extra_skills: Optional[List[Skill]] = None,
                       output_format: Optional[Type[BaseModel]] = None,
                       input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.legal", "open-source-license-scan")
    return SkilledAgent(
        role="Open-Source Compliance Engineer",
        goal=r"Identify viral copyleft licenses (GPL/AGPL) that could legally contaminate proprietary codebases.",
        input_description=input_description or r"Technology stack outlines, software dependencies, and database choices.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )
    
def security_threat_hunter(llm_callable: LLMCallable, 
                           extra_skills: Optional[List[Skill]] = None,
                           output_format: Optional[Type[BaseModel]] = None,
                           input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.security", "threat-intel-triage")
    return SkilledAgent(
        role="Security Threat Hunter",
        goal="Identify indicators of compromise, anomalous network and endpoint behavior, and active intrusion patterns from the provided data.",
        input_description=input_description or "Network logs, endpoint activity reports, or firewall/IDS configuration data.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )
    
def identity_access_auditor(llm_callable: LLMCallable,
                            extra_skills: Optional[List[Skill]] = None,
                            output_format: Optional[Type[BaseModel]] = None,
                            input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.security", "identity-access-anomaly-review")
    return SkilledAgent(
        role="Identity & Access Auditor",
        goal="Analyze authentication logs for failed-login clustering, privilege-escalation chains, credential-stuffing patterns, and MFA-bypass indicators to determine how access was obtained.",
        input_description=input_description or "Authentication/SSO logs, IAM change history, and MFA event logs.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def breach_notification_analyst(llm_callable: LLMCallable,
                                extra_skills: Optional[List[Skill]] = None,
                                output_format: Optional[Type[BaseModel]] = None,
                                input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.security", "breach-notification-triage")
    return SkilledAgent(
        role="Breach Notification Analyst",
        goal="Determine whether an incident involves personal data, triggers regulatory breach-notification requirements, and what timelines apply.",
        input_description=input_description or "Security incident logs, data-access records, and affected-system inventories.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def cfo_agent(llm_callable: LLMCallable,
              extra_skills: Optional[List[Skill]] = None,
              output_format: Optional[Type[BaseModel]] = None,
              input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.strategy", "runway-burn-analysis")
    return SkilledAgent(
        role="Chief Financial Officer (CFO)",
        goal="Ruthlessly evaluate financial viability, calculate hard runway timelines, and identify margin threats.",
        input_description=input_description or "Business dossiers, financial projections, and operational cost breakdowns.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def cto_agent(llm_callable: LLMCallable, 
              extra_skills: Optional[List[Skill]] = None,
              output_format: Optional[Type[BaseModel]] = None,
              input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.strategy", "tech-debt-audit")
    return SkilledAgent(
        role="Chief Technology Officer (CTO)",
        goal="Audit technical architecture for scalability bottlenecks, key-person dependencies, and refactor timelines.",
        input_description=input_description or "System architecture, tech stack summaries, and engineering team structures.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def cro_agent(llm_callable: LLMCallable, 
              extra_skills: Optional[List[Skill]] = None,
              output_format: Optional[Type[BaseModel]] = None,
              input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.strategy", "revenue-synergy-mapping")
    return SkilledAgent(
        role="Chief Revenue Officer (CRO)",
        goal="Evaluate market synergy, sales cycle friction, and realistic short-term revenue integration timelines.",
        input_description=input_description or "Target demographics, current client volume, and product positioning.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def cpo_agent(llm_callable: LLMCallable, 
              extra_skills: Optional[List[Skill]] = None,
              output_format: Optional[Type[BaseModel]] = None,
              input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.strategy", "product-market-fit-score")
    return SkilledAgent(
        role="Chief Product Officer (CPO)",
        goal="Evaluate true Product-Market Fit (PMF), defensibility moats, and churn risk.",
        input_description=input_description or "Product features, user pain points, and competitive landscape summaries.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )

def cmo_agent(llm_callable: LLMCallable, 
              extra_skills: Optional[List[Skill]] = None,
              output_format: Optional[Type[BaseModel]] = None,
              input_description: Optional[str] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.strategy", "cac-ltv-viability")
    return SkilledAgent(
        role="Chief Marketing Officer (CMO)",
        goal="Audit unit economics, CAC to LTV ratios, and the sustainability of user acquisition channels.",
        input_description=input_description or "Growth metrics, marketing channels, and customer acquisition costs.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or []),
        output_format=output_format
    )