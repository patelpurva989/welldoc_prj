"""Adverse Event Monitor Agent - Monitors FAERS database."""
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic import BaseModel
from typing import Optional
import httpx
from datetime import datetime
from ..core.config import settings


class AdverseEventAnalysis(BaseModel):
    """AI analysis of adverse event."""
    severity_assessment: str
    device_relationship: str
    risk_score: int  # 0-100
    recommendations: list[str]
    requires_action: bool


class AdverseEventAgent:
    """Agent for monitoring and analyzing adverse events."""

    def __init__(self):
        """Initialize the adverse event agent."""
        self.model = AnthropicModel(
            model_name=settings.CLAUDE_MODEL,
            
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_system_prompt(),
            result_type=str
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt for adverse event analysis."""
        return """You are a medical device safety expert specializing in adverse event monitoring and analysis.

Your role is to analyze adverse events from the FDA Adverse Event Reporting System (FAERS) and other sources.

Key responsibilities:
1. Assess severity and impact of adverse events
2. Determine relationship to device use
3. Calculate risk scores based on multiple factors
4. Identify patterns and trends
5. Recommend appropriate actions
6. Flag events requiring immediate attention

Analysis criteria:
- Event severity (death, serious injury, malfunction)
- Frequency and pattern
- Device relationship (definite, probable, possible, unlikely)
- Patient impact
- Root cause indicators
- Regulatory implications

Risk scoring (0-100):
- 0-25: Low risk, routine monitoring
- 26-50: Moderate risk, enhanced monitoring
- 51-75: High risk, investigation required
- 76-100: Critical risk, immediate action required

Remember:
- Patient safety is paramount
- Be objective and evidence-based
- Consider all contributing factors
- Flag systematic issues
- Follow FDA adverse event guidelines"""

    async def analyze_adverse_event(
        self,
        event_data: dict
    ) -> dict:
        """Analyze an adverse event and generate risk assessment."""
        prompt = f"""Analyze the following adverse event:

**Event Details:**
- Device Name: {event_data.get('device_name')}
- Event Type: {event_data.get('event_type')}
- Severity: {event_data.get('severity')}
- Description: {event_data.get('description')}
- Patient Age: {event_data.get('patient_age', 'Unknown')}
- Patient Sex: {event_data.get('patient_sex', 'Unknown')}
- Event Date: {event_data.get('event_date', 'Unknown')}

Provide a comprehensive analysis including:

1. SEVERITY ASSESSMENT
   - Clinical significance
   - Patient impact
   - Potential outcomes

2. DEVICE RELATIONSHIP
   - Probability device caused event (definite/probable/possible/unlikely)
   - Evidence supporting relationship
   - Alternative causes to consider

3. RISK SCORE (0-100)
   - Numerical risk score with justification
   - Key factors influencing score
   - Comparison to baseline risk

4. PATTERN ANALYSIS
   - Similar events with this device
   - Known device issues
   - Systematic concerns

5. RECOMMENDATIONS
   - Immediate actions required
   - Investigation steps
   - Monitoring recommendations
   - Regulatory reporting needs

6. REQUIRES ACTION
   - Yes/No decision on immediate action
   - Justification

Format response as structured analysis with clear sections."""

        result = await self.agent.run(prompt)

        # Parse response and extract risk score
        analysis_text = result.data
        risk_score = self._extract_risk_score(analysis_text)

        return {
            "analysis": analysis_text,
            "risk_score": risk_score,
            "requires_action": risk_score >= 51
        }

    async def monitor_faers_database(
        self,
        device_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[dict]:
        """Monitor FAERS database for device-related adverse events."""
        try:
            # Build FAERS API query
            query = self._build_faers_query(device_name, start_date, end_date)

            # Call FAERS API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.FAERS_API_URL,
                    params=query,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_faers_response(data)
                else:
                    return []

        except Exception as e:
            print(f"Error querying FAERS: {e}")
            return []

    async def generate_safety_report(
        self,
        events: list[dict],
        device_name: str,
        time_period: str
    ) -> str:
        """Generate comprehensive safety report from adverse events."""
        prompt = f"""Generate a comprehensive safety report for {device_name} covering {time_period}.

**Adverse Events ({len(events)} total):**
{self._format_events_summary(events)}

Create a detailed safety report with:

1. EXECUTIVE SUMMARY
   - Total events and key findings
   - Critical issues identified
   - Overall safety profile assessment

2. EVENT ANALYSIS
   - Event types and frequencies
   - Severity distribution
   - Temporal trends

3. RISK ASSESSMENT
   - High-risk events
   - Systematic issues
   - Patient populations at risk

4. COMPARATIVE ANALYSIS
   - Compare to previous periods
   - Industry benchmarks
   - Expected vs actual rates

5. ROOT CAUSE ANALYSIS
   - Potential device issues
   - Use errors
   - External factors

6. RECOMMENDATIONS
   - Immediate actions
   - Long-term improvements
   - Labeling updates
   - Training needs

7. REGULATORY CONSIDERATIONS
   - Reporting requirements
   - Required notifications
   - Documentation needs

Use tables and charts descriptions where appropriate."""

        result = await self.agent.run(prompt)
        return result.data

    def _build_faers_query(
        self,
        device_name: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> dict:
        """Build FAERS API query parameters."""
        query = {
            "search": f'patient.drug.openfda.device_name:"{device_name}"',
            "limit": 100
        }

        if start_date and end_date:
            query["search"] += f" AND receivedate:[{start_date.strftime('%Y%m%d')} TO {end_date.strftime('%Y%m%d')}]"

        return query

    def _parse_faers_response(self, data: dict) -> list[dict]:
        """Parse FAERS API response."""
        events = []
        results = data.get("results", [])

        for result in results:
            event = {
                "event_id": result.get("safetyreportid"),
                "device_name": result.get("patient", {}).get("drug", [{}])[0].get("openfda", {}).get("device_name", ["Unknown"])[0],
                "event_type": result.get("patient", {}).get("reaction", [{}])[0].get("reactionmeddrapt", "Unknown"),
                "severity": result.get("serious", "Unknown"),
                "description": result.get("patient", {}).get("reaction", [{}])[0].get("reactionmeddrapt", ""),
                "patient_age": result.get("patient", {}).get("patientonsetage"),
                "patient_sex": result.get("patient", {}).get("patientsex"),
                "reported_date": result.get("receivedate")
            }
            events.append(event)

        return events

    def _extract_risk_score(self, analysis_text: str) -> int:
        """Extract risk score from analysis text."""
        # Simple extraction - look for "Risk Score: XX" or "Score: XX"
        import re
        match = re.search(r'(?:risk\s+)?score[:\s]+(\d+)', analysis_text, re.IGNORECASE)
        if match:
            return min(100, max(0, int(match.group(1))))
        return 50  # Default moderate risk

    def _format_events_summary(self, events: list[dict]) -> str:
        """Format events summary for prompt."""
        if not events:
            return "No events to report"

        # Group by severity
        by_severity = {}
        for event in events:
            severity = event.get('severity', 'Unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1

        summary = [f"Total Events: {len(events)}\n"]
        summary.append("Severity Distribution:")
        for severity, count in by_severity.items():
            summary.append(f"  - {severity}: {count}")

        # Sample events
        summary.append("\nSample Events:")
        for i, event in enumerate(events[:5], 1):
            summary.append(f"""
Event {i}:
- Type: {event.get('event_type')}
- Severity: {event.get('severity')}
- Description: {event.get('description')}
""")

        return "\n".join(summary)


# Global agent instance
adverse_event_agent = AdverseEventAgent()
