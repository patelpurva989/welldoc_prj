"""Compliance Agent - 21 CFR Part 11 compliance checker."""
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic import BaseModel
from typing import Optional
from ..core.config import settings


class ComplianceCheckResult(BaseModel):
    """Result of compliance check."""
    compliant: bool
    score: int  # 0-100
    issues: list[dict]
    recommendations: list[str]
    audit_items: list[str]


class ComplianceAgent:
    """Agent for checking 21 CFR Part 11 compliance."""

    def __init__(self):
        """Initialize the compliance agent."""
        self.model = AnthropicModel(
            model_name=settings.CLAUDE_MODEL,
            
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_system_prompt(),
            result_type=str
        )

    def _get_system_prompt(self) -> str:
        """Get system prompt for compliance checking."""
        return """You are a regulatory compliance expert specializing in 21 CFR Part 11 (Electronic Records; Electronic Signatures).

Your role is to ensure FDA submission documents and processes comply with federal regulations.

Key compliance areas:
1. Electronic Records (Subpart B)
   - Validation of systems
   - Ability to generate accurate copies
   - Protection of records
   - Audit trail requirements

2. Electronic Signatures (Subpart C)
   - Electronic signature components
   - Controls for identification codes/passwords
   - Electronic signature manifestations
   - Signature/record linking

3. Data Integrity (ALCOA+ principles)
   - Attributable
   - Legible
   - Contemporaneous
   - Original
   - Accurate
   - Complete
   - Consistent
   - Enduring
   - Available

Compliance scoring:
- 90-100: Fully compliant
- 75-89: Mostly compliant (minor issues)
- 60-74: Partially compliant (significant gaps)
- Below 60: Non-compliant (major issues)

Remember:
- Be thorough and detail-oriented
- Cite specific CFR sections
- Provide actionable recommendations
- Consider both technical and procedural controls
- Focus on risk-based approach"""

    async def check_submission_compliance(
        self,
        submission_data: dict,
        check_electronic_signatures: bool = True,
        check_audit_trail: bool = True,
        check_record_retention: bool = True
    ) -> dict:
        """Check 21 CFR Part 11 compliance for a submission."""
        prompt = f"""Perform a comprehensive 21 CFR Part 11 compliance check for the following FDA submission:

**Submission Information:**
- Device Name: {submission_data.get('device_name')}
- Submission Type: {submission_data.get('submission_type')}
- Status: {submission_data.get('status')}
- Created: {submission_data.get('created_at')}

**Compliance Checks Required:**
- Electronic Signatures: {'Yes' if check_electronic_signatures else 'No'}
- Audit Trail: {'Yes' if check_audit_trail else 'No'}
- Record Retention: {'Yes' if check_record_retention else 'No'}

**Document Metadata:**
{self._format_metadata(submission_data)}

Perform compliance analysis covering:

1. ELECTRONIC RECORDS COMPLIANCE (21 CFR Part 11, Subpart B)
   - System validation status
   - Ability to generate accurate copies
   - Record protection mechanisms
   - Archive and retrieval capabilities

2. ELECTRONIC SIGNATURES COMPLIANCE (21 CFR Part 11, Subpart C)
   - Signature components present
   - Identification/authentication controls
   - Signature manifestations
   - Signature-record linking

3. AUDIT TRAIL REQUIREMENTS
   - Change tracking
   - User attribution
   - Timestamp accuracy
   - Completeness of trail

4. DATA INTEGRITY (ALCOA+)
   - Attributable to author
   - Legible and clear
   - Contemporaneous recording
   - Original or true copy
   - Accurate and complete

5. COMPLIANCE SCORE (0-100)
   - Overall compliance score
   - Scoring breakdown by section
   - Critical vs non-critical issues

6. IDENTIFIED ISSUES
   - List all compliance gaps
   - Severity (Critical/High/Medium/Low)
   - CFR section references
   - Impact on submission

7. RECOMMENDATIONS
   - Specific corrective actions
   - Implementation priority
   - Resources needed
   - Timeline estimates

8. AUDIT ITEMS
   - Items requiring documentation
   - Evidence to collect
   - Validation activities needed

Format as structured compliance report."""

        result = await self.agent.run(prompt)

        # Parse response
        analysis_text = result.data
        score = self._extract_compliance_score(analysis_text)

        return {
            "analysis": analysis_text,
            "score": score,
            "compliant": score >= 75,
            "requires_remediation": score < 75
        }

    async def validate_electronic_signature(
        self,
        signature_data: dict
    ) -> dict:
        """Validate electronic signature compliance."""
        prompt = f"""Validate the following electronic signature for 21 CFR Part 11 compliance:

**Signature Information:**
- Signer Name: {signature_data.get('signer_name')}
- Signer Role: {signature_data.get('signer_role')}
- Signature Date: {signature_data.get('signature_date')}
- Authentication Method: {signature_data.get('auth_method')}
- Document Signed: {signature_data.get('document_name')}

**Signature Components:**
{self._format_signature_components(signature_data)}

Verify compliance with 21 CFR 11.50, 11.70, 11.100, 11.200, and 11.300:

1. SIGNATURE COMPONENTS (§11.50)
   - Two distinct identification components
   - Executed under sole control of signer
   - Non-reusable signature elements

2. SIGNATURE MANIFESTATIONS (§11.70)
   - Clear indication of signed document
   - Date and time of signature
   - Meaning of signature (e.g., review, approval)
   - Signer's printed name

3. SIGNATURE/RECORD LINKING (§11.70)
   - Signature cannot be removed
   - Signature cannot be transferred
   - Record integrity maintained

4. IDENTIFICATION CODES/PASSWORDS (§11.300)
   - Unique to one individual
   - Periodically checked, recalled, revised
   - Loss management procedures
   - Transaction safeguards

Provide:
- Compliance status (Pass/Fail)
- Specific issues found
- Recommendations for remediation"""

        result = await self.agent.run(prompt)
        return {
            "validation": result.data,
            "compliant": "pass" in result.data.lower()
        }

    async def generate_compliance_checklist(
        self,
        submission_type: str
    ) -> str:
        """Generate compliance checklist for submission type."""
        prompt = f"""Generate a comprehensive 21 CFR Part 11 compliance checklist for {submission_type} submissions.

Create a detailed checklist covering:

1. PRE-SUBMISSION REQUIREMENTS
   - System validation documentation
   - SOP availability
   - Training records
   - User access controls

2. SUBMISSION PREPARATION
   - Electronic record requirements
   - Signature requirements
   - Audit trail configuration
   - Data integrity controls

3. SUBMISSION REVIEW
   - Document completeness
   - Signature validity
   - Audit trail review
   - Archive procedure

4. POST-SUBMISSION
   - Record retention
   - Archive integrity
   - Retrieval capability
   - Change control

For each item:
- Requirement description
- CFR section reference
- Verification method
- Documentation needed
- Pass/Fail/N/A checkbox

Format as actionable checklist suitable for printing."""

        result = await self.agent.run(prompt)
        return result.data

    async def audit_record_retention(
        self,
        retention_policy: dict,
        stored_records: list[dict]
    ) -> str:
        """Audit record retention compliance."""
        prompt = f"""Audit record retention compliance for FDA submissions.

**Retention Policy:**
{self._format_policy(retention_policy)}

**Stored Records ({len(stored_records)} total):**
{self._format_records(stored_records)}

Verify compliance with 21 CFR 11.10(c) and FDA guidance:

1. RETENTION REQUIREMENTS
   - Minimum retention period met
   - Records protected from loss
   - Records readily retrievable
   - Accurate copies can be generated

2. STORAGE CONDITIONS
   - Appropriate storage media
   - Environmental controls
   - Backup procedures
   - Disaster recovery plans

3. ARCHIVE INTEGRITY
   - Records complete and unaltered
   - Metadata preserved
   - Audit trails intact
   - Chain of custody documented

4. RETRIEVAL CAPABILITY
   - Records can be retrieved timely
   - Format remains readable
   - Associated metadata available
   - Search/filter capabilities

5. IDENTIFIED ISSUES
   - Records approaching retention end
   - Integrity concerns
   - Retrieval difficulties
   - Policy gaps

6. RECOMMENDATIONS
   - Immediate actions
   - Process improvements
   - Technology upgrades
   - Policy updates"""

        result = await self.agent.run(prompt)
        return result.data

    def _format_metadata(self, submission_data: dict) -> str:
        """Format submission metadata."""
        metadata = []
        for key, value in submission_data.items():
            if key not in ['device_name', 'submission_type', 'status', 'created_at']:
                metadata.append(f"- {key}: {value}")
        return "\n".join(metadata) if metadata else "No additional metadata"

    def _format_signature_components(self, signature_data: dict) -> str:
        """Format signature components."""
        components = signature_data.get('components', {})
        formatted = []
        for key, value in components.items():
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted) if formatted else "No components specified"

    def _format_policy(self, policy: dict) -> str:
        """Format retention policy."""
        formatted = []
        for key, value in policy.items():
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)

    def _format_records(self, records: list[dict]) -> str:
        """Format stored records summary."""
        if not records:
            return "No records found"

        summary = [f"Total: {len(records)}"]
        # Sample first 5
        for i, record in enumerate(records[:5], 1):
            summary.append(f"""
Record {i}:
- ID: {record.get('id')}
- Type: {record.get('type')}
- Created: {record.get('created_at')}
- Status: {record.get('status')}
""")
        if len(records) > 5:
            summary.append(f"... and {len(records) - 5} more records")

        return "\n".join(summary)

    def _extract_compliance_score(self, analysis_text: str) -> int:
        """Extract compliance score from analysis."""
        import re
        match = re.search(r'(?:compliance\s+)?score[:\s]+(\d+)', analysis_text, re.IGNORECASE)
        if match:
            return min(100, max(0, int(match.group(1))))
        return 50  # Default moderate compliance


# Global agent instance
compliance_agent = ComplianceAgent()
