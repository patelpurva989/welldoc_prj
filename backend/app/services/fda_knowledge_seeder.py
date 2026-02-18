"""FDA Regulatory Knowledge Base Seeder.

Pre-populates the vector database with carefully curated excerpts from
FDA guidance documents, ISO standards, and 21 CFR regulations that are
most relevant to 510(k) premarket notification submissions.

No external API calls are made for seeding — all content is hardcoded
regulatory reference text.  This guarantees reproducible, offline seeding.

Usage
-----
Called directly by the admin API endpoint:
    POST /api/v1/admin/seed-knowledge-base

Or from any async context:
    from app.services.fda_knowledge_seeder import seed_fda_knowledge_base
    count = await seed_fda_knowledge_base(db)
"""
import logging
from typing import List, Tuple
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Knowledge corpus
# Each entry: (title, content, content_type, section)
# ---------------------------------------------------------------------------
# fmt: off
FDA_KNOWLEDGE_CORPUS: List[Tuple[str, str, str, str]] = [

    # =========================================================================
    # 510(k) GENERAL REQUIREMENTS
    # =========================================================================
    (
        "510(k) Premarket Notification — Overview and Substantial Equivalence",
        """A 510(k) is a premarket submission made to FDA to demonstrate that the device
to be marketed is at least as safe and effective (substantially equivalent) as a
legally marketed device (predicate) that is not subject to Premarket Approval (PMA).
Substantial equivalence means the new device has the same intended use as the
predicate AND the same technological characteristics, OR different technological
characteristics that do not raise new questions of safety and effectiveness and
the device is at least as safe and effective as the predicate device.

Key elements required in every 510(k) submission:
1. Cover letter identifying the submission type
2. Table of contents with page numbers
3. Indications for Use Statement (Form FDA 3881)
4. Device Description — materials, components, operating principles
5. Substantial Equivalence Comparison — side-by-side table
6. Performance Testing — bench, animal, or clinical data as appropriate
7. Biocompatibility data (ISO 10993) if device contacts patient
8. Software documentation (IEC 62304) if software-driven device
9. Risk Management summary (ISO 14971)
10. Labeling — draft labeling for intended use
11. Sterility information if device is sterile

Reference: 21 CFR Part 807 Subpart E; FDA Guidance "The 510(k) Program" (2019).""",
        "guidance",
        "510k",
    ),

    (
        "510(k) Device Description Requirements",
        """The Device Description section of a 510(k) must contain:

1. PHYSICAL DESCRIPTION: A thorough description of the device, including its physical
   characteristics (size, shape, configuration), materials of construction, components,
   accessories, and any software or firmware.

2. OPERATING PRINCIPLE: A clear explanation of how the device works, including the
   mechanism of action and the principle of operation.

3. INDICATIONS FOR USE: A precise statement of the intended use of the device,
   including the patient population, anatomical location, disease or condition, and
   clinical indication.

4. CONTRAINDICATIONS: Conditions under which the device should not be used.

5. STERILIZATION: If the device is marketed as sterile, describe the sterilization
   method and any reprocessing instructions.

6. SHELF LIFE AND STORAGE: Storage conditions and shelf life of the device.

Guidance documents to reference:
- "Deciding When to Submit a 510(k) for a Change to an Existing Device" (2017)
- "Format for Traditional and Abbreviated 510(k)s" (2005)

21 CFR 807.87(e) requires a description of the device, including a complete
description of the components and accessories of the device.""",
        "guidance",
        "510k",
    ),

    (
        "Substantial Equivalence Criteria — Intended Use and Technological Characteristics",
        """FDA evaluates substantial equivalence using the following framework:

STEP 1 — SAME INTENDED USE
The new device must have the same intended use as the predicate device. If the
indications for use differ in a way that raises new safety or effectiveness
questions, the device is not substantially equivalent (NSE).

STEP 2 — SAME TECHNOLOGICAL CHARACTERISTICS
If the intended use is the same:
  a) Same technological characteristics → SE without performance data
  b) Different technological characteristics → FDA evaluates if the differences:
     i.  Raise new questions of safety or effectiveness
     ii. The device is at least as safe and effective as the predicate

COMPARISON TABLE (required):
| Feature               | Subject Device | Predicate Device | Same/Different |
|-----------------------|---------------|-----------------|----------------|
| Materials             |               |                 |                |
| Energy source         |               |                 |                |
| Design characteristics|               |                 |                |
| Performance specs     |               |                 |                |

If technological characteristics differ, performance data must demonstrate
equivalent or superior safety and effectiveness.

Reference: Section 513(i)(1)(A) of the FD&C Act; 21 CFR 807.100(b).""",
        "guidance",
        "510k",
    ),

    # =========================================================================
    # BIOCOMPATIBILITY
    # =========================================================================
    (
        "Biocompatibility Testing — ISO 10993 Framework",
        """ISO 10993 is the internationally recognised standard for evaluating the
biocompatibility of medical devices. FDA requires biocompatibility testing for
devices or device components that contact patients directly or indirectly.

CONTACT CLASSIFICATION (ISO 10993-1):
- Surface devices: skin, mucosal membrane, compromised surfaces
- External communicating devices: blood path indirect, tissue/bone/dentine, circulating blood
- Implant devices: tissue/bone, blood

DURATION CATEGORIES:
- Limited: ≤24 hours
- Prolonged: >24 hours to 30 days
- Permanent: >30 days

REQUIRED TESTS BASED ON CONTACT (most commonly required):
1. Cytotoxicity (ISO 10993-5) — baseline for all devices
2. Sensitization (ISO 10993-10) — all devices with patient contact
3. Irritation or intracutaneous reactivity (ISO 10993-10/23)
4. Systemic toxicity (acute, subacute, subchronic) — ISO 10993-11
5. Genotoxicity (ISO 10993-3) — prolonged or permanent contact
6. Implantation (ISO 10993-6) — implant devices
7. Hemocompatibility (ISO 10993-4) — blood-contacting devices

FDA GUIDANCE: "Use of International Standard ISO 10993-1 'Biological Evaluation
of Medical Devices'" (2020 update). All test reports must include protocol,
results, and conclusion by qualified laboratory.""",
        "guidance",
        "biocompatibility",
    ),

    (
        "Biocompatibility — Material Characterisation and Existing Data",
        """For biocompatibility submissions, FDA accepts:

1. EXISTING DATA / LITERATURE: Published peer-reviewed data on the same
   materials with the same or greater contact conditions can substitute for
   new testing. Must reference ASTM, ISO, or peer-reviewed studies.

2. MATERIAL CHARACTERISATION: Chemical characterisation (ISO 10993-18)
   identifying extractables and leachables can reduce the test battery if
   risk assessment demonstrates acceptable exposure levels.

3. PREDICATE DEVICE COMPARISON: If the predicate device uses the same
   materials and received clearance, sponsor may reference that clearance
   as supporting evidence, supplemented with a material comparison table.

DOCUMENTATION REQUIREMENTS:
- List all materials in patient-contact and indirect-contact components
- Provide material specification sheets or ISO 10993-18 characterisation
- Provide a biocompatibility risk assessment matrix
- Identify any materials from non-biocompatibility-grade lots

Reference: FDA Guidance "Use of ISO 10993-1" (2020); ISO 10993-18 (2020).""",
        "guidance",
        "biocompatibility",
    ),

    # =========================================================================
    # SOFTWARE DOCUMENTATION
    # =========================================================================
    (
        "Software Documentation Requirements — IEC 62304 and FDA Guidance",
        """For devices containing software or firmware, FDA requires a Software
Documentation package per IEC 62304 and FDA's "Guidance for the Content of
Premarket Submissions for Software Contained in Medical Devices" (2005) and
the newer "Guidance for Software Functions" (2019).

SAFETY CLASS DETERMINATION (IEC 62304 clause 4.3):
- Class A: No injury or damage possible
- Class B: Non-serious injury possible
- Class C: Serious injury or death possible

SOFTWARE LEVEL OF CONCERN (FDA):
- Minor: No injury or minor injury possible
- Moderate: Non-serious injury
- Major: Death or serious injury

REQUIRED DOCUMENTATION ELEMENTS:
1. Level of Concern justification
2. Software Description — architecture, modules, data flows
3. Device Hazard Analysis — software-related hazards (links to ISO 14971)
4. Software Requirements Specification (SRS)
5. Architecture Design Chart
6. Software Design Specification (SDS) — for Moderate/Major
7. Traceability Analysis (requirements → design → test)
8. Software Development and Maintenance Plan
9. Unresolved Anomalies List with risk assessment
10. Revision Level History

For Major level of concern devices include:
- Source Code List / Description
- Full Verification and Validation (V&V) protocols and results""",
        "guidance",
        "software",
    ),

    (
        "Cybersecurity Requirements for Software Medical Devices",
        """FDA increasingly requires cybersecurity documentation for networked and
software-containing medical devices. Per the "Cybersecurity in Medical Devices"
guidance (2023), sponsors must submit:

PRE-MARKET CYBERSECURITY DOCUMENTATION:
1. Threat Modelling — STRIDE or equivalent
2. Cybersecurity Risk Assessment (integrated with ISO 14971 risk management)
3. Security Architecture Review (authentication, encryption, access control)
4. Software Bill of Materials (SBOM) listing all third-party components
5. Vulnerability disclosure policy reference
6. Patch management plan
7. Testing evidence: penetration testing results, fuzzing reports

POST-MARKET COMMITMENTS:
- Coordinated vulnerability disclosure process
- Plan for providing software updates and patches

FDA REQUIRES for networked devices: demonstrate that cybersecurity controls
do not introduce new patient safety risks and that the SBOM enables post-market
monitoring of known vulnerabilities (e.g., via NVD/CVE databases).""",
        "guidance",
        "software",
    ),

    # =========================================================================
    # RISK MANAGEMENT
    # =========================================================================
    (
        "Risk Management — ISO 14971:2019 Requirements",
        """ISO 14971:2019 is the internationally recognised standard for medical device
risk management and is required for all FDA 510(k) submissions.

RISK MANAGEMENT PROCESS (ISO 14971 clause 4):
1. Risk Management Plan — define scope, risk acceptability criteria, activities
2. Intended Use and Reasonably Foreseeable Misuse Analysis
3. Hazard Identification — systematic identification of all hazards
4. Risk Estimation — severity × probability matrix
5. Risk Evaluation — compare to acceptance criteria
6. Risk Control — implement controls (inherently safe design > protective measures > information)
7. Residual Risk Evaluation — verify controls are effective
8. Risk/Benefit Analysis — overall residual risk acceptable?
9. Risk Management Report — summary of the entire process

SEVERITY LEVELS (typical scale):
- Negligible (1): No injury or negligible harm
- Minor (2): Injury not requiring professional medical intervention
- Serious (3): Injury requiring professional intervention
- Critical (4): Permanent impairment or life-threatening injury
- Catastrophic (5): Death

PROBABILITY LEVELS: Frequent, Probable, Occasional, Remote, Improbable

REQUIRED SUBMISSION CONTENT:
- Risk Management Plan or Risk Management Summary
- Hazard/risk traceability table mapping hazards → controls → verification
- Residual risk evaluation for each hazard
- Overall residual risk acceptability statement""",
        "guidance",
        "risk_management",
    ),

    # =========================================================================
    # PERFORMANCE TESTING
    # =========================================================================
    (
        "Performance Testing — Bench and Non-Clinical Testing Requirements",
        """Performance testing demonstrates that the device meets its design specifications
and performs as intended. For 510(k) submissions, FDA requires:

TYPES OF PERFORMANCE TESTS:
1. Bench/Laboratory Testing: mechanical, electrical, optical, chemical, or
   functional tests performed in a controlled laboratory setting
2. Simulated Use Testing: tests that replicate actual clinical conditions
3. Animal Studies: for novel technologies or implants (IACUC approval required)
4. Clinical Data: required for PMA; optional for 510(k) if bench data sufficient

REQUIRED REPORTING FORMAT FOR EACH TEST:
1. Test Protocol — objective, test method, pass/fail criteria, rationale
2. Test samples — lot numbers, production method, quantity
3. Testing laboratory — accreditation (ISO 17025 preferred)
4. Results — raw data, statistical analysis
5. Conclusion — pass/fail determination and comparison to predicate

STATISTICAL REQUIREMENTS:
- Sample size justification (typically n ≥ 30 for mechanical testing)
- Confidence level and significance threshold defined in protocol
- Pass criteria based on 95% confidence / 95% reliability (95/95) common

ACCEPTANCE TESTING STANDARDS to cite:
- ASTM International standards relevant to device type
- ISO standards (e.g., ISO 11135 for sterilization)
- IEC standards for electrical devices
- AAMI standards for specific device categories""",
        "guidance",
        "performance_testing",
    ),

    (
        "Electrical Safety and EMC Testing for Active Medical Devices",
        """Active medical devices require electrical safety and electromagnetic compatibility
(EMC) testing before 510(k) clearance.

APPLICABLE STANDARDS:
- IEC 60601-1 (3rd edition): General requirements for basic safety and essential performance
- IEC 60601-1-2 (4th edition): EMC requirements
- IEC 60601-1-6: Usability engineering
- Device-specific collateral/particular standards (IEC 60601-1-X series)

REQUIRED TEST REPORTS:
1. Dielectric Strength Test
2. Earth Leakage Current Test
3. Patient Leakage Current Test
4. Enclosure Leakage Current Test
5. Radiated/Conducted Emissions (CISPR 11/CISPR 32)
6. Radiated/Conducted Immunity (IEC 61000-4 series)
7. Electrostatic Discharge (ESD) Immunity
8. Power Line Magnetic Field Immunity

THIRD-PARTY LAB REQUIREMENT: FDA expects testing at an ISO 17025 accredited lab
or equivalent. Test reports must bear accreditation mark and lab signatory.

ESSENTIAL PERFORMANCE: Sponsors must define essential performance parameters
and demonstrate these are maintained throughout EMC testing.""",
        "guidance",
        "performance_testing",
    ),

    # =========================================================================
    # LABELING
    # =========================================================================
    (
        "Labeling Requirements for 510(k) Devices — 21 CFR 801",
        """Device labeling must comply with 21 CFR Part 801 and include all information
necessary for safe and effective use. Labeling includes the device label,
instructions for use (IFU), and any promotional materials.

REQUIRED LABEL ELEMENTS (21 CFR 801.1):
1. Proprietary (trade) name of the device
2. Established (common) name of the device
3. Name and place of business of the manufacturer, packer, or distributor
4. Net quantity of contents
5. Statement of intended use/indications
6. Adequate directions for use
7. Warnings, precautions, and contraindications
8. Symbols used on labeling (ISO 15223-1)

INSTRUCTIONS FOR USE (IFU) MUST INCLUDE:
1. Intended use and indications
2. Contraindications
3. Warnings and precautions
4. Device description (brief)
5. How to use the device (step-by-step)
6. How to clean/sterilize/reprocess (if applicable)
7. Storage conditions
8. Shelf life / expiration date
9. Symbols legend
10. Technical specifications

UDI REQUIREMENT: All medical devices must bear a Unique Device Identifier (UDI)
on the label per 21 CFR Part 830 and comply with FDA's UDI system.

ELECTRONIC IFU: Permitted for certain device categories per FDA guidance
"Electronic Instructions for Use of Medical Devices" (2019).""",
        "guidance",
        "labeling",
    ),

    # =========================================================================
    # STERILIZATION
    # =========================================================================
    (
        "Sterilization Documentation Requirements for Sterile Devices",
        """For devices marketed as sterile, FDA requires comprehensive sterilization
validation documentation.

STERILIZATION METHODS AND STANDARDS:
1. Ethylene Oxide (EtO): ISO 11135 — most common for polymer devices
2. Radiation (gamma/e-beam): ISO 11137 series
3. Steam Autoclave (moist heat): ISO 17665-1
4. Dry Heat: ISO 20857
5. Liquid Chemical Sterilization (e.g., peracetic acid): ISO 14937

REQUIRED DOCUMENTATION FOR 510(k):
1. Sterilization Method Rationale — why this method is appropriate
2. Validation Protocol and Summary — per applicable ISO standard
3. Bioburden Testing Results — pre-sterilization bioburden data
4. Sterility Assurance Level (SAL): must demonstrate SAL ≤ 10⁻⁶
5. Half-Cycle / Overkill Studies (for EtO and radiation)
6. Requalification Policy — frequency of annual revalidation

PACKAGING REQUIREMENTS:
- Packaging validation per ASTM F2475 / ISO 11607
- Accelerated aging per ASTM F1980 to support shelf-life claims

For reusable devices: instructions for cleaning and reprocessing per
FDA "Reprocessing of Single-Use Devices" guidance and AAMI TIR12.""",
        "guidance",
        "sterilization",
    ),

    # =========================================================================
    # CLINICAL DATA
    # =========================================================================
    (
        "Clinical Data Requirements — When Clinical Evidence is Needed",
        """For most 510(k) submissions, bench and non-clinical testing is sufficient.
However, clinical data may be required when:

1. The device has a new intended use not covered by the predicate
2. New technological characteristics raise safety questions that bench data
   cannot resolve
3. Performance Standards require clinical data (e.g., certain diagnostic devices)
4. FDA requests clinical data during the review process

TYPES OF CLINICAL EVIDENCE:
a) Published literature: peer-reviewed studies on the same or substantially
   similar device; systematic review / meta-analysis preferred
b) Post-market clinical follow-up (PMCF) data from the EU MDR
c) Clinical investigations conducted under IDE (Investigational Device Exemption)

IF CLINICAL DATA IS SUBMITTED, INCLUDE:
1. Study protocol(s) with IRB/Ethics Committee approval
2. Informed consent forms
3. Clinical study report with statistical analysis plan
4. Serious adverse events (SAE) summary
5. Comparison of subject vs. predicate device clinical outcomes

GOOD CLINICAL PRACTICE: All clinical studies must comply with 21 CFR Part 812
(IDE), ICH E6 GCP, and the Declaration of Helsinki.

FDA GUIDANCE: "Design Considerations for Pivotal Clinical Investigations for
Medical Devices" (2013).""",
        "guidance",
        "clinical_data",
    ),

    # =========================================================================
    # PREDICATE DEVICE SUMMARIES
    # =========================================================================
    (
        "Selecting and Documenting a Predicate Device for 510(k) Clearance",
        """A predicate device is a legally marketed device to which the new device is
compared to establish substantial equivalence. Selecting the right predicate
is one of the most critical steps in a 510(k) submission.

ELIGIBLE PREDICATES:
1. Device legally marketed before May 28, 1976 (pre-amendments device)
2. Device previously found substantially equivalent through 510(k) clearance
3. Device reclassified to Class I or Class II

HOW TO IDENTIFY A PREDICATE:
- Search FDA's 510(k) database at https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm
- Filter by device type (product code), intended use, and technology
- Review cleared K-numbers for comparable devices
- FDA's iRIS system and CDRH Product Classification database

DOCUMENTING THE PREDICATE:
- K-Number, device name, and manufacturer
- Indications for Use (must match or be more specific)
- Technological characteristics comparison table
- Any differences and supporting performance data

SPLIT PREDICATE APPROACH: A single predicate is preferred. A split predicate
(one predicate for intended use, another for technological characteristics) is
acceptable but requires strong justification.

MULTIPLE PREDICATES: Acceptable when no single predicate covers all intended
uses; each predicate comparison must be fully documented.""",
        "guidance",
        "510k",
    ),

    # =========================================================================
    # QUALITY SYSTEMS
    # =========================================================================
    (
        "Quality System Regulations — 21 CFR Part 820 / ISO 13485",
        """Manufacturers of medical devices distributed in the US must comply with
FDA's Quality System Regulation (QSR) under 21 CFR Part 820, which aligns
closely with ISO 13485:2016.

KEY QSR REQUIREMENTS (21 CFR Part 820):
1. Management Responsibility: Quality policy, objectives, management review
2. Design Controls (21 CFR 820.30): Design planning, inputs, outputs, review,
   verification, validation, transfer, changes, history file (DHF)
3. Document Controls (21 CFR 820.40): Approval, distribution, changes
4. Purchasing Controls (21 CFR 820.50): Supplier qualification
5. Production and Process Controls (21 CFR 820.70)
6. Acceptance Activities (21 CFR 820.80): Inspection and testing
7. Nonconforming Product (21 CFR 820.90)
8. Corrective and Preventive Action — CAPA (21 CFR 820.100)
9. Labeling and Packaging Controls (21 CFR 820.120/130)
10. Records Requirements: Device History Record (DHR), Device Master Record (DMR)

NOTE: FDA has proposed updating 21 CFR Part 820 to align with ISO 13485:2016
(QSR Modernisation Rule). Manufacturers should track this rulemaking.

FOR 510(k) SUBMISSIONS: The submission does not require submission of QSR
documentation, but the manufacturer must have a compliant QMS in place prior
to marketing clearance and before any FDA inspection.""",
        "regulation",
        "general",
    ),

    # =========================================================================
    # GENERAL FDA SUBMISSION REQUIREMENTS
    # =========================================================================
    (
        "510(k) Submission Format and Cover Letter Requirements",
        """FDA's "Format for Traditional and Abbreviated 510(k)s" guidance specifies
the required format for a 510(k) submission.

REQUIRED SECTIONS IN ORDER:
1. Medical Device User Fee Cover Sheet (Form FDA 3601) — required for paid submissions
2. CDRH Premarket Review Submission Cover Sheet (Form FDA 3514)
3. Cover Letter — signed by authorized representative; must include:
   a. Device name, regulation number, product code
   b. Predicate device K-number(s)
   c. Statement of no clinical studies (if applicable)
   d. Contact information
4. Table of Contents — page-referenced
5. Indications for Use Statement (Form FDA 3881)
6. Device Description
7. Substantial Equivalence Discussion
8. Proposed Labeling (draft)
9. Performance Testing / Supporting Data
10. Any other relevant information

ELECTRONIC SUBMISSION: FDA requires eCopy submission via eCopy system or
eSTAR template. Paper submissions are no longer accepted for most device types.

eSTAR TEMPLATE: FDA's Electronic Submission Template and Resource (eSTAR)
is now required for Traditional 510(k) submissions. Available at:
https://www.fda.gov/medical-devices/how-study-and-market-your-device/estar

FEES: Subject to Medical Device User Fee Act (MDUFA). Small business
discounts available with FDA qualification.""",
        "guidance",
        "510k",
    ),
]
# fmt: on


# ---------------------------------------------------------------------------
# Seeder function
# ---------------------------------------------------------------------------

async def seed_fda_knowledge_base(db: Session, skip_existing: bool = True) -> int:
    """
    Populate the ``fda_knowledge_base`` table with curated FDA guidance text.

    Parameters
    ----------
    db:
        Active SQLAlchemy database session.
    skip_existing:
        If True (default), checks whether any rows already exist and skips
        seeding to avoid duplicates.  Set to False to force a re-seed (idempotent
        because content is identified by title).

    Returns
    -------
    int
        Number of new entries inserted.
    """
    from ..models.fda_knowledge import FDAKnowledgeBase
    from .rag_service import embed_text

    # Check if already seeded
    if skip_existing:
        existing_count = db.query(FDAKnowledgeBase).count()
        if existing_count > 0:
            logger.info(
                "FDA knowledge base already has %d entries — skipping seed. "
                "Use skip_existing=False to force re-seed.",
                existing_count,
            )
            return 0

    inserted = 0
    for title, content, content_type, section in FDA_KNOWLEDGE_CORPUS:
        # Check for duplicate by title (idempotent)
        existing = (
            db.query(FDAKnowledgeBase)
            .filter(FDAKnowledgeBase.title == title)
            .first()
        )
        if existing:
            logger.debug("Skipping duplicate entry: %r", title[:60])
            continue

        try:
            embedding = await embed_text(f"{title} {content}")
            entry = FDAKnowledgeBase(
                title=title,
                content=content,
                content_type=content_type,
                section=section,
                embedding=embedding,
            )
            db.add(entry)
            inserted += 1
            logger.debug("Seeded: [%s] %s", section, title[:60])
        except Exception as exc:
            logger.error("Failed to seed entry %r: %s", title[:60], exc)
            db.rollback()
            continue

    if inserted > 0:
        db.commit()
        logger.info("FDA knowledge base seeded: %d new entries inserted", inserted)
    else:
        logger.info("FDA knowledge base seed complete: no new entries added")

    return inserted
