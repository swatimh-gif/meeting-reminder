"""
Mock External Booking Module Service
Fetches scheduled meeting details from the external booking system.
Generates 40 realistic fictional sample meetings with both participants' details,
purposes, dates/times, and authorization statuses.
"""
from django.utils import timezone
from datetime import timedelta

class ExternalBookingClient:
    """
    Simulates external booking engine API client (e.g. Cal.com / Acuity / Calendly).
    Provides 40 realistic mock scheduled meetings.
    """

    @classmethod
    def get_mock_scheduled_meetings(cls):
        now = timezone.now()

        # 40 realistic fictional corporate meeting schedules
        raw_data = [
            # 1 to 5
            {
                "id": "MF-BK-1001",
                "purpose": "Series A Capital Allocation & Board Strategy Review",
                "p1": ("Elena Vance", "e.vance@hyperion.vc", "+1 (555) 301-4401", "Host / General Partner"),
                "p2": ("Marcus Chen", "mchen@apextechnologies.io", "+1 (555) 782-9901", "Client / Chief Executive Officer"),
                "offset_h": 2.5, "dur": 60, "auth": "PENDING",
                "notes": "Review FY27 hiring roadmap, runway projections, and burn-multiple targets.",
                "loc": "Google Meet (meet.google.com/hpr-vanc-cap)"
            },
            {
                "id": "MF-BK-1002",
                "purpose": "Cloud Infrastructure Migration & Multi-Region SLA Briefing",
                "p1": ("Jordan Hayes", "jordan.h@fintechflow.net", "+1 (555) 887-5521", "Host / Principal Architect"),
                "p2": ("Sophia Morales", "s.morales@novabiotech.io", "+1 (555) 412-3304", "Client / Head of DevOps"),
                "offset_h": 5.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "Discuss AWS us-east failover topology, Kafka cluster replication, and egress latency.",
                "loc": "Zoom (zoom.us/j/9082341908)"
            },
            {
                "id": "MF-BK-1003",
                "purpose": "Annual SOC2 Type II Security & Data Privacy Audit",
                "p1": ("Vikram Patel", "vpatel@quantumsol.com", "+1 (555) 923-4411", "Host / Compliance Director"),
                "p2": ("Rachel Drummond", "rdrummond@globalaudit.uk", "+44 20 7946 0912", "Client / Lead Security Partner"),
                "offset_h": 9.0, "dur": 90, "auth": "PENDING",
                "notes": "Review pentest findings, automated IAM credential rotations, and KMS envelope encryption.",
                "loc": "Microsoft Teams (teams.microsoft.com/l/soc2-audit)"
            },
            {
                "id": "MF-BK-1004",
                "purpose": "Series B Technical Due Diligence & IP Architecture",
                "p1": ("Claire Beaumont", "claire.b@strataforge.fr", "+33 1 42 68 55 00", "Host / VP Engineering"),
                "p2": ("Tariq Al-Mansoor", "tariq@gulfinnovations.ae", "+971 4 429 8800", "Client / Chief Technology Officer"),
                "offset_h": 14.0, "dur": 60, "auth": "ACCEPTED",
                "notes": "Review distributed ledger consensus algorithms and patent assignments.",
                "loc": "Google Meet (meet.google.com/str-tech-ip)"
            },
            {
                "id": "MF-BK-1005",
                "purpose": "Global Brand Redesign: Master Design Tokens & Typography",
                "p1": ("Samantha Wu", "samantha.wu@synthetica.ai", "+1 (555) 234-7719", "Host / Design Director"),
                "p2": ("Julian Ortiz", "j.ortiz@branddynamix.es", "+34 91 587 2300", "Client / Creative VP"),
                "offset_h": 18.0, "dur": 45, "auth": "REJECTED",
                "notes": "Timing cancelled due to international design board conflict.",
                "loc": "Google Meet (meet.google.com/art-brand-sync)"
            },

            # 6 to 10
            {
                "id": "MF-BK-1006",
                "purpose": "Enterprise Multi-Tenant SaaS SLA & Licensing Negotiation",
                "p1": ("David K. O'Connor", "doconnor@neurometric.org", "+1 (555) 612-4402", "Host / Sales VP"),
                "p2": ("Amara Okafor", "amara.okafor@lagostech.ng", "+234 1 234 5678", "Client / Procurement Lead"),
                "offset_h": 24.0, "dur": 60, "auth": "PENDING",
                "notes": "Review 99.99% uptime commitment and indemnity clause revisions.",
                "loc": "Zoom (zoom.us/j/4491028341)"
            },
            {
                "id": "MF-BK-1007",
                "purpose": "Healthcare AI Predictive Diagnostic Model IRB Sign-off",
                "p1": ("Dr. Aris Vance", "aris.vance@blackmesa-health.org", "+1 (555) 349-8812", "Host / Medical Director"),
                "p2": ("Lucas Lindholm", "l.lindholm@nordicmed.se", "+46 8 123 4567", "Client / Clinical Trials Director"),
                "offset_h": 28.5, "dur": 60, "auth": "ACCEPTED",
                "notes": "Patient cohort anonymization and sensitivity-specificity validation.",
                "loc": "Google Meet (meet.google.com/hlth-irb-sign)"
            },
            {
                "id": "MF-BK-1008",
                "purpose": "Fintech Core Banking API Integration & Webhook Reliability",
                "p1": ("Jordan Hayes", "jordan.h@fintechflow.net", "+1 (555) 887-5521", "Host / Lead Architect"),
                "p2": ("Kavita Sharma", "kavita.sharma@mumbai-payments.in", "+91 22 6789 0123", "Client / Engineering Manager"),
                "offset_h": 33.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "Review idempotency keys, ISO 20022 payloads, and retry backoff policies.",
                "loc": "Google Meet (meet.google.com/fnt-core-api)"
            },
            {
                "id": "MF-BK-1009",
                "purpose": "Cybersecurity Incident Response Drills & Threat Modeling",
                "p1": ("Vikram Patel", "vpatel@quantumsol.com", "+1 (555) 923-4411", "Host / Security Lead"),
                "p2": ("Evelyn Thorne", "ethorne@sentineldefense.com", "+1 (555) 334-1902", "Client / Threat Analyst"),
                "offset_h": 38.0, "dur": 60, "auth": "PENDING",
                "notes": "Simulated ransomware intrusion vector and cold-backup restoration drills.",
                "loc": "Microsoft Teams (teams.microsoft.com/l/threat-drill)"
            },
            {
                "id": "MF-BK-1010",
                "purpose": "E-Commerce Black Friday High-Traffic Load Test Review",
                "p1": ("Elena Vance", "e.vance@hyperion.vc", "+1 (555) 301-4401", "Host / Technical Advisor"),
                "p2": ("Kenji Sato", "kenji.sato@tokyo-retail.jp", "+81 3 5555 0143", "Client / Head of Infrastructure"),
                "offset_h": 42.0, "dur": 60, "auth": "ACCEPTED",
                "notes": "Simulating 250,000 req/sec peak checkout throughput on Redis caches.",
                "loc": "Zoom (zoom.us/j/8839201948)"
            },

            # 11 to 15
            {
                "id": "MF-BK-1011",
                "purpose": "Autonomous Vehicle Perception Stack Edge Inference Review",
                "p1": ("Samantha Wu", "samantha.wu@synthetica.ai", "+1 (555) 234-7719", "Host / AI Fellow"),
                "p2": ("Maximilian Weber", "m.weber@bavaria-autonomy.de", "+49 89 2020 4040", "Client / Chief Systems Engineer"),
                "offset_h": 48.0, "dur": 45, "auth": "PENDING",
                "notes": "FP8 quantization benchmark on embedded automotive tensor cores.",
                "loc": "Google Meet (meet.google.com/ai-auto-edge)"
            },
            {
                "id": "MF-BK-1012",
                "purpose": "Supply Chain ESG & Carbon Accounting Verification",
                "p1": ("Claire Beaumont", "claire.b@strataforge.fr", "+33 1 42 68 55 00", "Host / Sustainability Officer"),
                "p2": ("Chloe Dubois", "cdubois@montrealgreen.ca", "+1 (514) 555-0199", "Client / Scope-3 Auditor"),
                "offset_h": 53.0, "dur": 30, "auth": "ACCEPTED",
                "notes": "Maritime freight fuel emissions telemetry and supplier certifications.",
                "loc": "Google Meet (meet.google.com/esg-carb-verify)"
            },
            {
                "id": "MF-BK-1013",
                "purpose": "Renewable Energy Grid Interconnection Technical Feasibility",
                "p1": ("David K. O'Connor", "doconnor@neurometric.org", "+1 (555) 612-4402", "Host / Energy Consultant"),
                "p2": ("Henrik Vanger", "hvanger@nordicpower.no", "+47 22 33 44 55", "Client / Grid Systems Director"),
                "offset_h": 58.0, "dur": 60, "auth": "REJECTED",
                "notes": "Grid frequency regulation modeling rejected due to pending substation permit.",
                "loc": "Microsoft Teams (teams.microsoft.com/l/grid-connect)"
            },
            {
                "id": "MF-BK-1014",
                "purpose": "Cross-Border Tax Harmonization & Transfer Pricing Strategy",
                "p1": ("Jordan Hayes", "jordan.h@fintechflow.net", "+1 (555) 887-5521", "Host / Financial Controller"),
                "p2": ("Beatriz Silva", "bsilva@lisbon-advisory.pt", "+351 21 345 6789", "Client / Managing Director"),
                "offset_h": 64.0, "dur": 45, "auth": "PENDING",
                "notes": "OECD Pillar Two global minimum corporate tax compliance alignment.",
                "loc": "Google Meet (meet.google.com/tax-global-align)"
            },
            {
                "id": "MF-BK-1015",
                "purpose": "Bioinformatics Genomic Sequencing Data Pipeline Optimization",
                "p1": ("Dr. Aris Vance", "aris.vance@blackmesa-health.org", "+1 (555) 349-8812", "Host / Bioinformatics Lead"),
                "p2": ("Liam Gallagher", "lgallagher@celticgenomics.ie", "+353 1 496 0123", "Client / Chief Science Officer"),
                "offset_h": 70.0, "dur": 60, "auth": "ACCEPTED",
                "notes": "Accelerating Nextflow variant calling pipelines on GPU clusters.",
                "loc": "Zoom (zoom.us/j/7729103841)"
            },

            # 16 to 20
            {
                "id": "MF-BK-1016",
                "purpose": "Retail Omnichannel Point of Sale POS Hardware Upgrade",
                "p1": ("Elena Vance", "e.vance@hyperion.vc", "+1 (555) 301-4401", "Host / Operations Lead"),
                "p2": ("Giulia Rossi", "giulia.rossi@milano-retail.it", "+39 02 8765 4321", "Client / Store Technology VP"),
                "offset_h": 76.0, "dur": 45, "auth": "PENDING",
                "notes": "EMV Level-3 contactless readers and inventory sync terminals.",
                "loc": "Google Meet (meet.google.com/pos-retail-sync)"
            },
            {
                "id": "MF-BK-1017",
                "purpose": "Decentralized Key Management & Zero-Knowledge Cryptography",
                "p1": ("Vikram Patel", "vpatel@quantumsol.com", "+1 (555) 923-4411", "Host / Chief Cryptographer"),
                "p2": ("Mateo Fernandez", "mateo@buenosaires-zk.ar", "+54 11 4321 8765", "Client / Protocol Architect"),
                "offset_h": 82.0, "dur": 60, "auth": "ACCEPTED",
                "notes": "Evaluating recursive SNARK proof generation benchmarks in WASM runtimes.",
                "loc": "Google Meet (meet.google.com/zk-crypto-arch)"
            },
            {
                "id": "MF-BK-1018",
                "purpose": "Telecommunications 5G Open-RAN Radio Unit Interoperability",
                "p1": ("Claire Beaumont", "claire.b@strataforge.fr", "+33 1 42 68 55 00", "Host / Telecom Partner"),
                "p2": ("Hanna Korhonen", "h.korhonen@helsinki-telecom.fi", "+358 9 1234 5678", "Client / RF Engineering Lead"),
                "offset_h": 88.0, "dur": 60, "auth": "PENDING",
                "notes": "Option 7.2x split fronthaul conformance and CPRI encapsulation.",
                "loc": "Microsoft Teams (teams.microsoft.com/l/5g-oran-sync)"
            },
            {
                "id": "MF-BK-1019",
                "purpose": "Legal Compliance Review: AI Copyright & Fair Use Doctrine",
                "p1": ("Samantha Wu", "samantha.wu@synthetica.ai", "+1 (555) 234-7719", "Host / General Counsel"),
                "p2": ("Nathalie Leroy", "nleroy@parislaw.fr", "+33 1 55 44 33 22", "Client / Senior Partner"),
                "offset_h": 94.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "Training dataset attribution, opt-out crawler standards, and risk mitigation.",
                "loc": "Zoom (zoom.us/j/3321908472)"
            },
            {
                "id": "MF-BK-1020",
                "purpose": "Commercial Real Estate PropTech IoT Energy Automation",
                "p1": ("David K. O'Connor", "doconnor@neurometric.org", "+1 (555) 612-4402", "Host / IoT Solutions VP"),
                "p2": ("Sean MacBride", "smacbride@sydneyproperty.com.au", "+61 2 9876 5432", "Client / Facilities VP"),
                "offset_h": 100.0, "dur": 30, "auth": "REJECTED",
                "notes": "Cancelled after client selected alternate HVAC BACnet vendor.",
                "loc": "Google Meet (meet.google.com/prop-iot-energy)"
            },

            # 21 to 25
            {
                "id": "MF-BK-1021",
                "purpose": "AgTech Drone Multispectral Soil Moisture Analysis Briefing",
                "p1": ("Dr. Aris Vance", "aris.vance@blackmesa-health.org", "+1 (555) 349-8812", "Host / AgTech Director"),
                "p2": ("Daan Van Der Meer", "daan@rotterdam-agri.nl", "+31 10 234 5678", "Client / Chief Agronomist"),
                "offset_h": 106.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "NDVI spectral index calibrations and precision drip-irrigation maps.",
                "loc": "Google Meet (meet.google.com/ag-spectral-soil)"
            },
            {
                "id": "MF-BK-1022",
                "purpose": "Robotics Process Automation RPA Bot Fleet Orchestration",
                "p1": ("Jordan Hayes", "jordan.h@fintechflow.net", "+1 (555) 887-5521", "Host / Operations Lead"),
                "p2": ("Camila Duarte", "cduarte@saopaulo-bpo.br", "+55 11 3456 7890", "Client / BPO Automation Lead"),
                "offset_h": 112.0, "dur": 60, "auth": "PENDING",
                "notes": "Invoice optical character recognition and automated ERP ledger entries.",
                "loc": "Zoom (zoom.us/j/5549012384)"
            },
            {
                "id": "MF-BK-1023",
                "purpose": "Medical Device FDA 510(k) Pre-Submission Clearance Review",
                "p1": ("Dr. Aris Vance", "aris.vance@blackmesa-health.org", "+1 (555) 349-8812", "Host / Regulatory Specialist"),
                "p2": ("Dr. Ingrid Bergman", "ibergman@stockholm-medtech.se", "+46 8 8765 4321", "Client / Chief Medical Officer"),
                "offset_h": 118.0, "dur": 90, "auth": "ACCEPTED",
                "notes": "Substantial equivalence predicate comparison for Class-II monitor.",
                "loc": "Google Meet (meet.google.com/fda-510k-med)"
            },
            {
                "id": "MF-BK-1024",
                "purpose": "B2B SaaS Growth Marketing Funnel & Customer Acquisition Cost",
                "p1": ("Elena Vance", "e.vance@hyperion.vc", "+1 (555) 301-4401", "Host / Growth Advisor"),
                "p2": ("Oliver Queen", "oliver.queen@starlingtech.io", "+1 (555) 909-1234", "Client / VP Marketing"),
                "offset_h": 124.0, "dur": 45, "auth": "PENDING",
                "notes": "Evaluating LTV/CAC ratios across paid acquisition and outbound SDR channels.",
                "loc": "Google Meet (meet.google.com/b2b-growth-funnel)"
            },
            {
                "id": "MF-BK-1025",
                "purpose": "Aerospace Satellite Constellation Downlink Telemetry Review",
                "p1": ("Vikram Patel", "vpatel@quantumsol.com", "+1 (555) 923-4411", "Host / Aerospace Architect"),
                "p2": ("Astrid Lindgren", "astrid@oslo-aerospace.no", "+47 21 55 66 77", "Client / Mission Director"),
                "offset_h": 130.0, "dur": 60, "auth": "REJECTED",
                "notes": "Meeting cancelled due to launch window orbital rescheduling.",
                "loc": "Microsoft Teams (teams.microsoft.com/l/satellite-downlink)"
            },

            # 26 to 30
            {
                "id": "MF-BK-1026",
                "purpose": "Decentralized Identity DID W3C Verifiable Credentials Sync",
                "p1": ("Claire Beaumont", "claire.b@strataforge.fr", "+33 1 42 68 55 00", "Host / Standards Lead"),
                "p2": ("Kenzo Tanaka", "ktanaka@kyoto-identity.jp", "+81 75 123 4567", "Client / Research Fellow"),
                "offset_h": 136.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "Implementing selective disclosure JWT credentials with BBS+ signatures.",
                "loc": "Google Meet (meet.google.com/did-w3c-sync)"
            },
            {
                "id": "MF-BK-1027",
                "purpose": "Quantum Computing Qubit Coherence Error Mitigation Briefing",
                "p1": ("Samantha Wu", "samantha.wu@synthetica.ai", "+1 (555) 234-7719", "Host / Quantum Fellow"),
                "p2": ("Dr. Rajesh Koothrappali", "rkooth@pasadena-quantum.edu", "+1 (555) 445-6789", "Client / Lead Physicist"),
                "offset_h": 142.0, "dur": 60, "auth": "PENDING",
                "notes": "Surface code stabilizer measurements and cryogenic control wire latency.",
                "loc": "Zoom (zoom.us/j/9901234857)"
            },
            {
                "id": "MF-BK-1028",
                "purpose": "EdTech Adaptive Learning Algorithm Efficacy Assessment",
                "p1": ("David K. O'Connor", "doconnor@neurometric.org", "+1 (555) 612-4402", "Host / Learning Scientist"),
                "p2": ("Fatima Al-Zahra", "fatima@doha-edu.qa", "+974 4455 6677", "Client / Curriculum Director"),
                "offset_h": 148.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "Bayesian knowledge tracing and student engagement retention models.",
                "loc": "Google Meet (meet.google.com/ed-adaptive-learn)"
            },
            {
                "id": "MF-BK-1029",
                "purpose": "Logistics Cold-Chain Pharmaceutical IoT Temperature Auditing",
                "p1": ("Jordan Hayes", "jordan.h@fintechflow.net", "+1 (555) 887-5521", "Host / Solutions Architect"),
                "p2": ("Klaus Mueller", "kmueller@frankfurt-logistics.de", "+49 69 9876 5432", "Client / Quality VP"),
                "offset_h": 154.0, "dur": 45, "auth": "PENDING",
                "notes": "Continuous -80C dry ice vaccine storage telemetry and tamper-evident logs.",
                "loc": "Microsoft Teams (teams.microsoft.com/l/cold-chain-audit)"
            },
            {
                "id": "MF-BK-1030",
                "purpose": "Digital Health Wearable PPG Sensor Firmware Calibration",
                "p1": ("Dr. Aris Vance", "aris.vance@blackmesa-health.org", "+1 (555) 349-8812", "Host / Biomedical Engineer"),
                "p2": ("Zoe Kravitz", "zkravitz@austin-wearables.com", "+1 (555) 667-8901", "Client / Hardware VP"),
                "offset_h": 160.0, "dur": 60, "auth": "ACCEPTED",
                "notes": "Photoplethysmography noise cancellation algorithms during vigorous motion.",
                "loc": "Google Meet (meet.google.com/wear-ppg-firmware)"
            },

            # 31 to 35
            {
                "id": "MF-BK-1031",
                "purpose": "Venture Debt Facility Structuring & Covenant Negotiations",
                "p1": ("Elena Vance", "e.vance@hyperion.vc", "+1 (555) 301-4401", "Host / Finance Partner"),
                "p2": ("Arthur Pendelton", "apendelton@london-credit.co.uk", "+44 20 7123 4567", "Client / Credit Managing Partner"),
                "offset_h": 166.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "Review minimum cash reserves, debt amortization, and equity warrant coverage.",
                "loc": "Zoom (zoom.us/j/7788990011)"
            },
            {
                "id": "MF-BK-1032",
                "purpose": "Microservices Service Mesh Envoy Proxy Security hardening",
                "p1": ("Vikram Patel", "vpatel@quantumsol.com", "+1 (555) 923-4411", "Host / Cloud Architect"),
                "p2": ("Sergey Kozlov", "sergey@vilnius-systems.lt", "+370 5 123 4567", "Client / Lead SRE"),
                "offset_h": 172.0, "dur": 60, "auth": "PENDING",
                "notes": "Mutual TLS mTLS certificate rotation policies and SPIFFE/SPIRE integrations.",
                "loc": "Google Meet (meet.google.com/envoy-mesh-sec)"
            },
            {
                "id": "MF-BK-1033",
                "purpose": "CleanTech Hydrogen Electrolyzer Membrane Degradation Review",
                "p1": ("Claire Beaumont", "claire.b@strataforge.fr", "+33 1 42 68 55 00", "Host / Material Scientist"),
                "p2": ("Anika Larson", "alarson@copenhagen-h2.dk", "+45 33 12 34 56", "Client / Chief Chemist"),
                "offset_h": 178.0, "dur": 60, "auth": "REJECTED",
                "notes": "Cancelled after laboratory test batch contaminated during synthesis.",
                "loc": "Microsoft Teams (teams.microsoft.com/l/h2-membrane-test)"
            },
            {
                "id": "MF-BK-1034",
                "purpose": "Enterprise Search Vector Embeddings HNSW Index Latency Tuning",
                "p1": ("Samantha Wu", "samantha.wu@synthetica.ai", "+1 (555) 234-7719", "Host / Search Fellow"),
                "p2": ("Pradeep Nair", "pnair@bangalore-ai.in", "+91 80 2345 6789", "Client / Search Architect"),
                "offset_h": 184.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "Benchmarking pgvector and Milvus for 100M 1536-dimensional vectors.",
                "loc": "Google Meet (meet.google.com/vec-hnsw-tune)"
            },
            {
                "id": "MF-BK-1035",
                "purpose": "Commercial Drone Fleet BVLOS FAA Part 107 Waiver Submission",
                "p1": ("David K. O'Connor", "doconnor@neurometric.org", "+1 (555) 612-4402", "Host / Aviation Advisor"),
                "p2": ("Garrett Walker", "gwalker@denver-drones.com", "+1 (555) 778-9012", "Client / Flight Operations VP"),
                "offset_h": 190.0, "dur": 45, "auth": "PENDING",
                "notes": "Beyond Visual Line of Sight detect-and-avoid radar redundancy documentation.",
                "loc": "Zoom (zoom.us/j/4455667788)"
            },

            # 36 to 40
            {
                "id": "MF-BK-1036",
                "purpose": "InsurTech Automated Parametric Weather Claim Payout Triggers",
                "p1": ("Jordan Hayes", "jordan.h@fintechflow.net", "+1 (555) 887-5521", "Host / Product VP"),
                "p2": ("Valerie Dubois", "vdubois@zurich-insure.ch", "+41 44 123 4567", "Client / Underwriting Director"),
                "offset_h": 196.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "Oracle integration with NOAA satellite precipitation data feeds.",
                "loc": "Google Meet (meet.google.com/insur-weather-payout)"
            },
            {
                "id": "MF-BK-1037",
                "purpose": "Semiconductor EUV Photolithography Yield Optimization Sync",
                "p1": ("Vikram Patel", "vpatel@quantumsol.com", "+1 (555) 923-4411", "Host / Semiconductor Fellow"),
                "p2": ("Chao-Wei Huang", "cwhuang@hsinchu-semicon.tw", "+886 3 567 8901", "Client / Fab Director"),
                "offset_h": 202.0, "dur": 60, "auth": "PENDING",
                "notes": "Extreme ultraviolet pellicle degradation and line-edge roughness reduction.",
                "loc": "Microsoft Teams (teams.microsoft.com/l/euv-litho-yield)"
            },
            {
                "id": "MF-BK-1038",
                "purpose": "Hospital Electronic Health Records FHIR API Interoperability",
                "p1": ("Dr. Aris Vance", "aris.vance@blackmesa-health.org", "+1 (555) 349-8812", "Host / Health Informatics Lead"),
                "p2": ("Miriam Stern", "mstern@chicago-health.org", "+1 (555) 889-0123", "Client / Chief Information Officer"),
                "offset_h": 208.0, "dur": 45, "auth": "ACCEPTED",
                "notes": "HL7 FHIR Release-4 RESTful endpoints for patient record synchronization.",
                "loc": "Google Meet (meet.google.com/fhir-hl7-ehealth)"
            },
            {
                "id": "MF-BK-1039",
                "purpose": "Virtual Reality Spatial Audio Raytracing Acoustic Simulation",
                "p1": ("Samantha Wu", "samantha.wu@synthetica.ai", "+1 (555) 234-7719", "Host / Spatial Media Fellow"),
                "p2": ("Felix Baumgartner", "fbaum@vienna-audio.at", "+43 1 234 5678", "Client / Lead Acoustic Engineer"),
                "offset_h": 214.0, "dur": 45, "auth": "REJECTED",
                "notes": "Meeting cancelled due to licensing re-evaluation of HRTF algorithms.",
                "loc": "Zoom (zoom.us/j/2233445566)"
            },
            {
                "id": "MF-BK-1040",
                "purpose": "Executive Leadership Q4 Board Briefing & 2027 Strategic Goals",
                "p1": ("Elena Vance", "e.vance@hyperion.vc", "+1 (555) 301-4401", "Host / Board Chair"),
                "p2": ("Alexander Wright", "awright@apexglobal.com", "+1 (555) 990-1234", "Client / Executive Director"),
                "offset_h": 220.0, "dur": 60, "auth": "ACCEPTED",
                "notes": "Consolidated governance review, audit committee sign-off, and annual budget approval.",
                "loc": "Google Meet (meet.google.com/exec-board-q4)"
            }
        ]

        mock_records = []
        for r in raw_data:
            mock_records.append({
                "booking_id": r["id"],
                "p1_name": r["p1"][0],
                "p1_email": r["p1"][1],
                "p1_phone": r["p1"][2],
                "p1_role": r["p1"][3],
                "p2_name": r["p2"][0],
                "p2_email": r["p2"][1],
                "p2_phone": r["p2"][2],
                "p2_role": r["p2"][3],
                "purpose": r["purpose"],
                "start_time": now + timedelta(hours=r["offset_h"]),
                "duration_minutes": r["dur"],
                "location": r["loc"],
                "notes": r["notes"],
                "initial_auth": r["auth"],
                "auth_note": f"Initial state: {r['auth']}. {r['notes']}"
            })

        return mock_records

    @classmethod
    def sync_to_database(cls):
        """
        Fetches scheduled meeting details from the external booking module and persists them.
        Imports or updates meetings.
        """
        import secrets
        from reminders.models import Meeting
        from reminders.services.scheduler import sync_reminders_for_meeting

        mock_data = cls.get_mock_scheduled_meetings()
        stats = {"created": 0, "updated": 0, "total": len(mock_data)}

        for idx, item in enumerate(mock_data):
            initial_auth = item.get("initial_auth", "PENDING")
            
            # Map dual participant status
            resched_dt = None
            resched_reason = ""
            resched_by = ""

            if initial_auth == "ACCEPTED":
                p1_status = Meeting.ParticipantAuth.ACCEPTED
                p2_status = Meeting.ParticipantAuth.ACCEPTED
                overall = Meeting.OverallStatus.CONFIRMED
            elif initial_auth == "REJECTED":
                p1_status = Meeting.ParticipantAuth.REJECTED
                p2_status = Meeting.ParticipantAuth.PENDING
                overall = Meeting.OverallStatus.REJECTED
            else:
                if idx % 3 == 0:
                    p1_status = Meeting.ParticipantAuth.ACCEPTED
                    p2_status = Meeting.ParticipantAuth.PENDING
                    overall = Meeting.OverallStatus.PENDING
                elif idx % 7 == 0:
                    p1_status = Meeting.ParticipantAuth.RESCHEDULE_REQUESTED
                    p2_status = Meeting.ParticipantAuth.PENDING
                    overall = Meeting.OverallStatus.RESCHEDULE_REQUESTED
                    resched_dt = item["start_time"] + timedelta(days=2, hours=3)
                    resched_reason = "Client requested later afternoon slot due to travel conflict."
                    resched_by = f"{item['p2_name']} (Client)"
                else:
                    p1_status = Meeting.ParticipantAuth.PENDING
                    p2_status = Meeting.ParticipantAuth.PENDING
                    overall = Meeting.OverallStatus.PENDING

            meeting, created = Meeting.objects.update_or_create(
                booking_id=item["booking_id"],
                defaults={
                    "p1_name": item["p1_name"],
                    "p1_email": item["p1_email"],
                    "p1_phone": item["p1_phone"],
                    "p1_role": item.get("p1_role", "Host / Organizer"),
                    "p1_auth_status": p1_status,
                    "p2_name": item["p2_name"],
                    "p2_email": item["p2_email"],
                    "p2_phone": item["p2_phone"],
                    "p2_role": item.get("p2_role", "Client / Invitee"),
                    "p2_auth_status": p2_status,
                    "overall_status": overall,
                    "rescheduled_date_time": resched_dt,
                    "reschedule_reason": resched_reason,
                    "rescheduled_by": resched_by,
                    "purpose": item["purpose"],
                    "start_time": item["start_time"],
                    "duration_minutes": item.get("duration_minutes", 45),
                    "location": item.get("location", "Google Meet"),
                    "notes": item.get("notes", ""),
                    "timing_authorization": "ACCEPTED" if overall == Meeting.OverallStatus.CONFIRMED else ("REJECTED" if overall == Meeting.OverallStatus.REJECTED else "PENDING"),
                    "authorization_note": item.get("auth_note", ""),
                    "authorization_updated_at": timezone.now() if overall != Meeting.OverallStatus.PENDING else None
                }
            )

            if not meeting.p1_token:
                meeting.p1_token = secrets.token_urlsafe(32)
            if not meeting.p2_token:
                meeting.p2_token = secrets.token_urlsafe(32)
            meeting.save()

            if created:
                stats["created"] += 1
            else:
                stats["updated"] += 1

            # Sync reminders according to dual-participant confirmation rules
            sync_reminders_for_meeting(meeting)

        return stats
