"""Clinical Evidence Synthesizer Agent."""
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic import BaseModel
from typing import Optional
from ..core.config import settings


class ClinicalSummary(BaseModel):
    """Synthesized clinical evidence summary."""
    study_overview: str
    methodology: str
    results: str
    safety_profile: str
    effectiveness: str
    conclusions: str
    references: list[str]


class EvidenceAgent:
    """Agent for synthesizing clinical evidence."""

    def __init__(self):
        """Initialize the evidence agent."""
        self.model = AnthropicModel(
            model_name=settings.CLAUDE_MODEL,
            
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_system_prompt(),
            result_type=str
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt for evidence synthesis."""
        return """You are a clinical research expert specializing in medical device evidence synthesis.

Your role is to analyze and synthesize clinical evidence for FDA submissions.

Key responsibilities:
1. Review clinical study data objectively
2. Identify key safety and effectiveness outcomes
3. Synthesize results into clear, concise summaries
4. Highlight statistical significance and clinical relevance
5. Present adverse events and safety data transparently
6. Compare results to predicate devices when available

Analysis standards:
- Use evidence-based approach
- Present data objectively without bias
- Include confidence intervals and p-values
- Acknowledge limitations
- Follow ICH-GCP guidelines
- Comply with FDA evidence standards

Remember:
- Accuracy is paramount
- Present both positive and negative findings
- Use scientific terminology appropriately
- Support conclusions with data"""

    async def synthesize_clinical_evidence(
        self,
        clinical_data: dict,
        device_name: str,
        study_type: Optional[str] = None
    ) -> str:
        """Synthesize clinical evidence into FDA-ready summary."""
        prompt = f"""Synthesize the following clinical evidence for {device_name}:

**Study Type:** {study_type or 'Not specified'}

**Clinical Data:**
{self._format_clinical_data(clinical_data)}

Create a comprehensive clinical summary with the following sections:

1. STUDY OVERVIEW
   - Study design and objectives
   - Patient population
   - Sample size and duration

2. METHODOLOGY
   - Inclusion/exclusion criteria
   - Primary and secondary endpoints
   - Statistical methods

3. RESULTS
   - Primary endpoint results
   - Secondary endpoint results
   - Statistical analysis

4. SAFETY PROFILE
   - Adverse events
   - Serious adverse events
   - Device-related complications

5. EFFECTIVENESS
   - Clinical outcomes
   - Comparison to predicate (if applicable)
   - Clinical significance

6. CONCLUSIONS
   - Summary of findings
   - Risk-benefit analysis
   - Clinical implications

Include all relevant statistics (p-values, confidence intervals, etc.)."""

        result = await self.agent.run(prompt)
        return result.data

    async def analyze_safety_data(
        self,
        adverse_events: list[dict],
        device_name: str
    ) -> str:
        """Analyze safety data and adverse events."""
        prompt = f"""Analyze the safety profile for {device_name} based on the following adverse events:

**Adverse Events:**
{self._format_adverse_events(adverse_events)}

Provide a comprehensive safety analysis including:

1. EVENT SUMMARY
   - Total number of events
   - Event severity distribution
   - Event types and frequencies

2. RISK ANALYSIS
   - Serious vs non-serious events
   - Device-related vs non-related events
   - Risk patterns and trends

3. COMPARATIVE ANALYSIS
   - Compare to expected background rates
   - Compare to predicate device (if data available)
   - Industry benchmarks

4. RISK MITIGATION
   - Identified risks
   - Mitigation strategies
   - Labeling recommendations

5. CONCLUSIONS
   - Overall safety profile
   - Risk-benefit assessment
   - Safety monitoring recommendations

Present data in tables where appropriate."""

        result = await self.agent.run(prompt)
        return result.data

    async def compare_to_literature(
        self,
        device_results: dict,
        literature_references: list[str]
    ) -> str:
        """Compare device results to published literature."""
        prompt = f"""Compare the following device results to published literature:

**Device Results:**
{self._format_clinical_data(device_results)}

**Literature References:**
{chr(10).join([f'- {ref}' for ref in literature_references])}

Provide a literature comparison analysis:

1. DEVICE PERFORMANCE vs LITERATURE
   - Compare key outcomes
   - Identify similarities and differences
   - Context and interpretation

2. CONSISTENCY ANALYSIS
   - Results consistent with literature
   - Notable deviations and explanations
   - Validation of findings

3. CLINICAL CONTEXT
   - How results fit in current evidence base
   - Clinical significance
   - Implications for practice

4. SUMMARY
   - Key takeaways
   - Strength of evidence
   - Future research needs"""

        result = await self.agent.run(prompt)
        return result.data

    def _format_clinical_data(self, clinical_data: dict) -> str:
        """Format clinical data for prompt."""
        formatted = []
        for key, value in clinical_data.items():
            if isinstance(value, dict):
                formatted.append(f"**{key}:**")
                for sub_key, sub_value in value.items():
                    formatted.append(f"  - {sub_key}: {sub_value}")
            else:
                formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)

    def _format_adverse_events(self, adverse_events: list[dict]) -> str:
        """Format adverse events for prompt."""
        if not adverse_events:
            return "No adverse events reported"

        formatted = []
        for i, event in enumerate(adverse_events, 1):
            formatted.append(f"""
Event {i}:
- Type: {event.get('event_type', 'N/A')}
- Severity: {event.get('severity', 'N/A')}
- Description: {event.get('description', 'N/A')}
- Outcome: {event.get('outcome', 'N/A')}
""")
        return "\n".join(formatted)


# Global agent instance
evidence_agent = EvidenceAgent()
