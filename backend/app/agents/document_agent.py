"""Regulatory Document Agent - Generates FDA submission documents."""
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic import BaseModel
from typing import Optional
from ..core.config import settings


class SubmissionDocument(BaseModel):
    """Generated submission document."""
    executive_summary: str
    device_description: str
    indications_for_use: str
    technological_characteristics: str
    performance_testing: str
    substantial_equivalence: Optional[str] = None
    clinical_summary: Optional[str] = None
    labeling: str
    conclusion: str


class DocumentAgent:
    """Agent for generating FDA submission documents."""

    def __init__(self):
        """Initialize the document agent."""
        self.model = AnthropicModel(
            model_name=settings.CLAUDE_MODEL,
            
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_system_prompt(),
            result_type=str
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt for document generation."""
        return """You are an FDA regulatory affairs expert specializing in medical device submissions.

Your role is to generate comprehensive, compliant 510(k) premarket notification submissions.

Key responsibilities:
1. Create well-structured submission documents following FDA format
2. Ensure all required sections are included and properly formatted
3. Use clear, professional language appropriate for regulatory review
4. Highlight substantial equivalence to predicate devices
5. Present clinical and technical data effectively
6. Follow 21 CFR Part 807 requirements

Format guidelines:
- Use clear section headers
- Include all required information
- Present data in tables where appropriate
- Use objective, scientific language
- Cite relevant standards and regulations

Remember:
- Accuracy is critical - base all claims on provided data
- Maintain regulatory compliance throughout
- Present information logically and clearly
- Support all claims with evidence"""

    async def generate_510k_submission(
        self,
        device_name: str,
        device_description: str,
        manufacturer: str,
        indications_for_use: str,
        predicate_device: Optional[dict] = None,
        clinical_data: Optional[dict] = None
    ) -> str:
        """Generate a complete 510(k) submission document."""
        prompt = f"""Generate a comprehensive 510(k) Premarket Notification submission for the following device:

**Device Information:**
- Device Name: {device_name}
- Manufacturer: {manufacturer}
- Description: {device_description}
- Indications for Use: {indications_for_use}

**Predicate Device:**
{self._format_predicate(predicate_device) if predicate_device else "No predicate device specified"}

**Clinical Data:**
{self._format_clinical_data(clinical_data) if clinical_data else "No clinical data provided"}

Generate a complete submission document with the following sections:

1. EXECUTIVE SUMMARY
2. DEVICE DESCRIPTION
3. INDICATIONS FOR USE
4. TECHNOLOGICAL CHARACTERISTICS
5. PERFORMANCE TESTING
6. SUBSTANTIAL EQUIVALENCE COMPARISON
7. CLINICAL SUMMARY (if applicable)
8. LABELING
9. CONCLUSION

Each section should be comprehensive, professionally written, and FDA-compliant."""

        result = await self.agent.run(prompt)
        return result.data

    async def generate_substantial_equivalence_analysis(
        self,
        subject_device: dict,
        predicate_device: dict
    ) -> str:
        """Generate substantial equivalence analysis."""
        prompt = f"""Perform a detailed substantial equivalence analysis comparing:

**Subject Device:**
- Name: {subject_device.get('name')}
- Description: {subject_device.get('description')}
- Indications: {subject_device.get('indications')}
- Technology: {subject_device.get('technology')}

**Predicate Device:**
- Name: {predicate_device.get('name')}
- K-Number: {predicate_device.get('k_number')}
- Description: {predicate_device.get('description')}
- Indications: {predicate_device.get('indications')}
- Technology: {predicate_device.get('technology')}

Create a comprehensive substantial equivalence analysis covering:

1. INTENDED USE COMPARISON
   - Compare indications for use
   - Identify similarities and differences

2. TECHNOLOGICAL CHARACTERISTICS
   - Materials and design
   - Performance specifications
   - Operating principles
   - Energy sources

3. PERFORMANCE DATA
   - Compare test results
   - Address any differences
   - Demonstrate equivalent safety and effectiveness

4. CONCLUSION
   - Clear statement of substantial equivalence
   - Summary of key similarities
   - Explanation of any differences and their impact

Use a table format for side-by-side comparisons where appropriate."""

        result = await self.agent.run(prompt)
        return result.data

    def _format_predicate(self, predicate: dict) -> str:
        """Format predicate device information."""
        return f"""
- K-Number: {predicate.get('k_number', 'N/A')}
- Device Name: {predicate.get('name', 'N/A')}
- Manufacturer: {predicate.get('manufacturer', 'N/A')}
- Indications: {predicate.get('indications', 'N/A')}
"""

    def _format_clinical_data(self, clinical_data: dict) -> str:
        """Format clinical data."""
        if not clinical_data:
            return "No clinical data provided"

        formatted = []
        for key, value in clinical_data.items():
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)


# Global agent instance
document_agent = DocumentAgent()
