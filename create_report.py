from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

def add_heading(doc, text, level):
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)
        run.font.name = 'Times New Roman'
    return heading

def add_paragraph(doc, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False):
    p = doc.add_paragraph()
    p.alignment = align
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.bold = bold
    return p

def add_bullet_point(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    return p

doc = Document()

# Define styles
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(12)

# --- COVER PAGE ---
doc.add_paragraph("\n\n\n")
p = doc.add_paragraph("INTERNSHIP REPORT", style='Title')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in p.runs:
    run.font.name = 'Times New Roman'
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.bold = True

doc.add_paragraph("\n")
p = doc.add_paragraph("On", style='Heading 1')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph("\n")
p = add_paragraph(doc, "PayProof AI – AI-Powered Payment Risk Analysis and Fraud Review System", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
p.runs[0].font.size = Pt(18)
doc.add_paragraph("\n")

add_paragraph(doc, "Submitted by:", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
add_paragraph(doc, "[STUDENT NAME]\n[REGISTRATION NUMBER]", align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph("\n")
add_paragraph(doc, "Under the Guidance of:", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
add_paragraph(doc, "[PROJECT GUIDE NAME]", align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph("\n")
add_paragraph(doc, "Internship Organization:", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
add_paragraph(doc, "Smart City Research Center (SCRC)\nInternational Institute of Information Technology Hyderabad (IIIT Hyderabad)", align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph("\n\n")
add_paragraph(doc, "Submitted in partial fulfillment for the award of degree of Bachelor of Technology in Information Technology.", align=WD_ALIGN_PARAGRAPH.CENTER)

doc.add_page_break()

# --- CERTIFICATE ---
add_heading(doc, "CERTIFICATE", 1)
add_paragraph(doc, "This is to certify that the internship report entitled \"PayProof AI – AI-Powered Payment Risk Analysis and Fraud Review System\" is a bonafide work carried out by [STUDENT NAME] (Reg. No. [REGISTRATION NUMBER]) under my guidance and supervision at Smart City Research Center (SCRC), IIIT Hyderabad.")
add_paragraph(doc, "The report is submitted towards the partial fulfillment of the requirements for the award of the degree of Bachelor of Technology in Information Technology. This work has not been submitted anywhere else for the award of any other degree or diploma.")
doc.add_paragraph("\n\n\n")
table = doc.add_table(rows=1, cols=3)
table.cell(0, 0).text = "____________________\n[PROJECT GUIDE NAME]\nProject Guide"
table.cell(0, 1).text = "____________________\n[INTERNSHIP COORDINATOR]\nInternship Coordinator"
table.cell(0, 2).text = "____________________\n[HOD NAME]\nHead of Department"
doc.add_page_break()

# --- ACKNOWLEDGEMENT ---
add_heading(doc, "ACKNOWLEDGEMENT", 1)
add_paragraph(doc, "I would like to express my profound gratitude to the Smart City Research Center (SCRC) at the International Institute of Information Technology Hyderabad (IIIT Hyderabad) for providing me with the opportunity to undertake this internship. The research environment and practical technology exposure have been invaluable to my professional development.")
add_paragraph(doc, "I am deeply thankful to my guide, [PROJECT GUIDE NAME], for their continuous support, expert guidance, and encouragement throughout the project. Their insights into software development and intelligent systems were instrumental in the successful completion of this work.")
add_paragraph(doc, "I would also like to thank [INTERNSHIP COORDINATOR] for organizing the internship program and [HOD NAME] and [PRINCIPAL NAME] for their administrative support and for fostering an environment conducive to learning.")
add_paragraph(doc, "Finally, I express my heartfelt thanks to my family, friends, and peers who have directly or indirectly contributed to this endeavor.")
doc.add_paragraph("\n\n")
add_paragraph(doc, "[STUDENT NAME]\n[REGISTRATION NUMBER]", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True)
doc.add_page_break()

# --- ABSTRACT ---
add_heading(doc, "ABSTRACT", 1)
add_paragraph(doc, "The rapid growth of digital transactions has made payment fraud and risk review a critical challenge for modern businesses. Traditional manual review processes are often slow, difficult to manage, and prone to error when handling complex, contradictory evidence. There is a strong need for organized case analysis that seamlessly integrates automated risk checks with intelligent decision support.")
add_paragraph(doc, "PayProof AI is a web-based AI-assisted payment risk analysis and fraud review system designed to streamline this process. The system provides a structured environment for reviewers to create and manage payment-related risk cases, examine available evidence, and assess claims. It employs deterministic rule-based checks to instantly identify possible risk indicators, ensuring a reliable safety baseline. In addition, the platform leverages the OpenRouter API to provide explainable AI-assisted analysis, offering contextual insights and supporting reasoning based on the provided evidence.")
add_paragraph(doc, "Crucially, PayProof AI follows a human-in-the-loop approach. Rather than relying on autonomous final fraud detection, the AI functions as a decision-support tool. A human reviewer examines the case details, rule flags, and AI analysis before making the final decision. Every significant action and status transition is immutably recorded in a secure audit log, ensuring complete traceability and accountability.")
add_paragraph(doc, "Built using a modern technology stack, the frontend is developed with React, TypeScript, Vite, and Tailwind CSS and hosted on Vercel. The backend is a robust REST API developed in Python using FastAPI, leveraging PostgreSQL and SQLAlchemy for structured data management, and deployed on Render. Overall, PayProof AI demonstrates the practical application of full-stack web development and AI integration in creating a transparent, explainable, and highly auditable payment risk review platform.")
add_paragraph(doc, "\nKeywords: PayProof AI, Payment Risk Analysis, Fraud Review, Artificial Intelligence, AI-Assisted Analysis, Human-in-the-Loop, Risk Assessment, Rule-Based Analysis, FastAPI, React, PostgreSQL, OpenRouter, REST API, Audit Log, Web Application.", bold=True)
doc.add_page_break()

# --- INDEX ---
add_heading(doc, "INDEX", 1)
index_entries = [
    ("1. Organization Information", "1"),
    ("2. Programmes and Opportunities", "2"),
    ("3. Introduction", "3"),
    ("4. Learning / Internship Objectives", "5"),
    ("5. Methodology", "6"),
    ("6. Analysis", "7"),
    ("   6.1 Requirement Analysis", "7"),
    ("   6.2 Feasibility Study", "8"),
    ("7. Requirement Specifications", "9"),
    ("   7.1 Software Requirements", "9"),
    ("   7.2 Hardware Requirements", "9"),
    ("   7.3 Functionalities", "10"),
    ("8. Technology", "11"),
    ("9. System Architecture", "13"),
    ("10. Demonstration", "15"),
    ("11. Testing", "18"),
    ("12. Benefits to the Institution", "19"),
    ("13. Conclusion", "20"),
    ("14. Bibliography", "21")
]
for text, page in index_entries:
    p = doc.add_paragraph()
    p.add_run(text).bold = ('   ' not in text)
    p.add_run(f"\t\t\t\t\t\t{page}") # simple tab alignment
doc.add_page_break()

# --- LIST OF FIGURES ---
add_heading(doc, "LIST OF FIGURES", 1)
figures = [
    ("Fig 1 – PayProof AI Landing/Dashboard Page", "15"),
    ("Fig 2 – Case Creation Page", "15"),
    ("Fig 3 – Case List / Case Management Page", "16"),
    ("Fig 4 – Case Details and Evidence Page", "16"),
    ("Fig 5 – Rule Flags / Risk Analysis Page", "17"),
    ("Fig 6 – AI-Assisted Analysis Page", "17"),
    ("Fig 7 – Human Review / Decision Page", "18"),
    ("Fig 8 – Audit Log / Case Lifecycle Page", "18")
]
for text, page in figures:
    p = doc.add_paragraph()
    p.add_run(text)
    p.add_run(f"\t\t\t\t\t{page}")
doc.add_page_break()

# --- WEEKLY LOG ---
add_heading(doc, "WEEKLY INTERNSHIP LOG (4 WEEKS)", 1)
log_table = doc.add_table(rows=5, cols=2)
log_table.style = 'Table Grid'
log_table.cell(0, 0).text = "Week / Date"
log_table.cell(0, 1).text = "Activities Performed"
log_table.cell(1, 0).text = "Week 1\n[DATE] to [DATE]"
log_table.cell(1, 1).text = "Requirement Analysis and System Design. Understanding the need for structured payment risk analysis and planning the full-stack architecture of PayProof AI."
log_table.cell(2, 0).text = "Week 2\n[DATE] to [DATE]"
log_table.cell(2, 1).text = "Backend and Database Development. Setting up FastAPI, PostgreSQL, and SQLAlchemy to handle case management, evidence storage, and audit logging via REST APIs."
log_table.cell(3, 0).text = "Week 3\n[DATE] to [DATE]"
log_table.cell(3, 1).text = "Frontend, Risk Analysis and AI Integration. Developing the React and TypeScript frontend. Implementing deterministic rule checks and integrating the OpenRouter API for AI-assisted case analysis."
log_table.cell(4, 0).text = "Week 4\n[DATE] to [DATE]"
log_table.cell(4, 1).text = "Human Review, Testing, Debugging and Deployment. Finalizing the human-in-the-loop review interface. Conducting controlled scenario testing, debugging APIs, and deploying to Vercel and Render."
doc.add_page_break()

# --- 1. ORGANIZATION INFORMATION ---
add_heading(doc, "1. ORGANIZATION INFORMATION", 1)
add_paragraph(doc, "The Smart City Research Center (SCRC) is a specialized research center associated with the International Institute of Information Technology Hyderabad (IIIT Hyderabad). The center is dedicated to creating a smart-city and technology-oriented research environment, focusing on developing intelligent systems to solve real-world problems.")
add_paragraph(doc, "SCRC aims to bridge the gap between academic research and practical technology deployment. The research environment focuses on software development, data integration, intelligent systems, and interdisciplinary technology development. It provides an innovative ecosystem where researchers, professionals, and students work together to develop scalable software solutions that improve urban living, resource management, and digital infrastructure.")
add_paragraph(doc, "For interns and students, SCRC offers an excellent opportunity to gain exposure to professional and research environments. Working within the center provides hands-on experience in modern software engineering practices and exposure to real-world technology projects, equipping individuals with the skills necessary to excel in the technology industry.")
doc.add_page_break()

# --- 2. PROGRAMMES AND OPPORTUNITIES ---
add_heading(doc, "2. PROGRAMMES AND OPPORTUNITIES", 1)
add_paragraph(doc, "The internship at SCRC provides extensive opportunities for professional development within a highly research-oriented environment. The center is uniquely positioned to offer practical technology exposure, allowing interns to interact with cutting-edge software development environments.")
add_paragraph(doc, "Key opportunities provided during the internship include:")
add_bullet_point(doc, "Exposure to smart-city technology and intelligent systems development.")
add_bullet_point(doc, "Opportunities to learn through real-world projects that demand scalable and robust software architecture.")
add_bullet_point(doc, "Engagement with AI integrations and intelligent decision-support mechanisms in practical scenarios.")
add_bullet_point(doc, "Professional development through the application of modern development practices, including version control, RESTful API design, and cloud deployment.")
add_paragraph(doc, "This environment significantly enhances the understanding of how theoretical computer science concepts translate into applied, intelligent web applications.")
doc.add_page_break()

# --- 3. INTRODUCTION ---
add_heading(doc, "3. INTRODUCTION", 1)
add_paragraph(doc, "Payment risk review is an essential operational requirement for modern e-commerce and digital platforms. As digital transactions increase, so does the complexity of resolving payment disputes, chargebacks, and potential fraud. Manual review of these cases is a significant challenge; reviewers often have to sift through fragmented data, leading to slow processing times and human error.")
add_paragraph(doc, "There is a pressing need for a system that provides structured case information, allowing reviewers to clearly organize and analyze evidence, claims, and transaction histories. While automated rules can help flag basic contradictions, and artificial intelligence can provide advanced context, these technologies are most effective when they support human intelligence rather than completely replacing it.")
add_paragraph(doc, "PayProof AI is a web-based AI-assisted payment risk analysis and fraud review system developed to meet these needs. The system acts as a comprehensive platform where evidence is collected, rule-based checks are applied to flag immediate risk indicators, and AI-assisted analysis evaluates complex or contradictory information. The core philosophy of PayProof AI is a human-in-the-loop approach. The AI provides explainable analysis and risk insights, but the human reviewer always makes the final decision. To ensure transparency and accountability, every action is tracked in an immutable audit log.")
add_paragraph(doc, "The project's overall objective was to build a complete, full-stack solution utilizing modern web technologies. The frontend provides a responsive interface for reviewers, while the backend API manages complex business logic, database operations, and AI integration, demonstrating a practical and robust software architecture.")
doc.add_page_break()

# --- 4. LEARNING / INTERNSHIP OBJECTIVES ---
add_heading(doc, "4. LEARNING / INTERNSHIP OBJECTIVES", 1)
add_paragraph(doc, "The primary objectives of the internship and the development of the PayProof AI project were:")
add_bullet_point(doc, "Understanding the complete software development life cycle (SDLC) from requirement analysis to deployment.")
add_bullet_point(doc, "Learning modern frontend development using React, TypeScript, Vite, and Tailwind CSS.")
add_bullet_point(doc, "Understanding backend API development and request handling using Python and FastAPI.")
add_bullet_point(doc, "Understanding relational database integration, schema design, and operations using PostgreSQL and SQLAlchemy.")
add_bullet_point(doc, "Learning to design, develop, and test scalable REST APIs.")
add_bullet_point(doc, "Understanding AI API integration (using OpenRouter) to provide intelligent decision support.")
add_bullet_point(doc, "Learning how to implement structured risk-analysis workflows and rule-based logic in software.")
add_bullet_point(doc, "Understanding the architectural requirements of human-in-the-loop review systems.")
add_bullet_point(doc, "Improving software engineering practices, including modular code design and state management.")
add_bullet_point(doc, "Learning comprehensive testing and debugging strategies for full-stack applications.")
add_bullet_point(doc, "Understanding the importance and implementation of strict audit logging for system accountability.")
add_bullet_point(doc, "Understanding application deployment processes using cloud platforms like Render and Vercel.")
add_bullet_point(doc, "Gaining practical experience by solving a real-world software engineering problem.")
add_bullet_point(doc, "Improving analytical problem-solving skills in a professional technology environment.")
doc.add_page_break()

# --- 5. METHODOLOGY ---
add_heading(doc, "5. METHODOLOGY", 1)
add_paragraph(doc, "The development of PayProof AI followed a structured methodology to ensure a robust and maintainable software product. The workflow was divided into sequential stages:")
add_bullet_point(doc, "Requirement Analysis: Identifying the core needs of a payment risk review system, including case management, evidence tracking, and the need for human-in-the-loop AI assistance.")
add_bullet_point(doc, "System Design: Planning the architecture, database schema for cases and audit logs, and defining the REST API contracts between the frontend and backend.")
add_bullet_point(doc, "Database Integration: Setting up PostgreSQL and configuring SQLAlchemy models to ensure data integrity and structured storage.")
add_bullet_point(doc, "Backend/API Development: Developing the FastAPI server to handle business logic, routing, and data processing.")
add_bullet_point(doc, "Frontend Development: Creating the user interface using React and Tailwind CSS, focusing on usability and clear presentation of complex case data.")
add_bullet_point(doc, "Rule-Based Risk Analysis: Implementing deterministic logic to instantly flag common risk indicators and evidence contradictions.")
add_bullet_point(doc, "AI Integration: Connecting the OpenRouter API to allow the system to analyze case data and provide supportive reasoning without making final autonomous decisions.")
add_bullet_point(doc, "Human Review Workflow: Designing the interface and logic for human reviewers to evaluate the AI's suggestions and record their final decisions.")
add_bullet_point(doc, "Testing and Debugging: Using controlled testing scenarios to verify frontend functionality, API communication, and the accuracy of state transitions.")
add_bullet_point(doc, "Deployment: Hosting the backend API on Render and deploying the frontend application on Vercel for public access.")
doc.add_page_break()

# --- 6. ANALYSIS ---
add_heading(doc, "6. ANALYSIS", 1)
add_heading(doc, "6.1 Requirement Analysis", 2)
add_paragraph(doc, "Functional Requirements:", bold=True)
add_bullet_point(doc, "The system must allow users to create and manage payment-related risk cases.")
add_bullet_point(doc, "The system must support adding and managing evidence and claims for each case.")
add_bullet_point(doc, "The system must perform rule-based checks and display risk indicators (rule flags).")
add_bullet_point(doc, "The system must perform AI-assisted analysis to support the review process.")
add_bullet_point(doc, "The system must provide an interface for human review, decision-making, and case escalation.")
add_bullet_point(doc, "The system must manage case lifecycle and status transitions.")
add_bullet_point(doc, "The system must maintain a comprehensive audit log of all significant actions.")
add_paragraph(doc, "\nNon-Functional Requirements:", bold=True)
add_bullet_point(doc, "Usability: The interface must present complex information clearly to the reviewer.")
add_bullet_point(doc, "Reliability: The system must fall back gracefully to rule-based checks if the AI service is temporarily unavailable.")
add_bullet_point(doc, "Maintainability: The codebase must be modular and well-documented.")
add_bullet_point(doc, "Security & Traceability: All decisions must be traceable via the immutable audit log.")
add_bullet_point(doc, "Performance: The web interface must be highly responsive.")
add_bullet_point(doc, "Data Management: Data must be strictly structured and relational.")

add_heading(doc, "6.2 Feasibility Study", 2)
add_paragraph(doc, "Technical Feasibility: The project relies on proven, widely-adopted technologies (React, FastAPI, PostgreSQL). Integrating the OpenRouter API via standard HTTP requests is technically straightforward and well-supported by Python libraries.")
add_paragraph(doc, "Economic Feasibility: The project utilizes open-source frameworks and free-tier or low-cost deployment platforms (Vercel, Render), making it highly cost-effective to develop and host.")
add_paragraph(doc, "Operational Feasibility: The human-in-the-loop design ensures that operational staff can use the system without needing to trust a \"black-box\" AI entirely. The structured presentation of evidence and rule flags aligns closely with standard risk-analysis workflows.")
add_paragraph(doc, "Schedule Feasibility: The scope of the project, focusing on core case management and API integration, is well-defined and can be completed within the internship timeline using agile development practices.")
doc.add_page_break()

# --- 7. REQUIREMENT SPECIFICATIONS ---
add_heading(doc, "7. REQUIREMENT SPECIFICATIONS", 1)

add_heading(doc, "7.1 Software Requirements", 2)
add_bullet_point(doc, "Operating System: Windows or Linux")
add_bullet_point(doc, "Frontend Framework: React, Vite")
add_bullet_point(doc, "Frontend Language: TypeScript")
add_bullet_point(doc, "Styling: Tailwind CSS")
add_bullet_point(doc, "Backend Framework: FastAPI")
add_bullet_point(doc, "Backend Language: Python")
add_bullet_point(doc, "Database: PostgreSQL")
add_bullet_point(doc, "ORM: SQLAlchemy")
add_bullet_point(doc, "AI Integration: OpenRouter API")
add_bullet_point(doc, "API Architecture: REST APIs")
add_bullet_point(doc, "Backend Hosting: Render")
add_bullet_point(doc, "Frontend Hosting: Vercel")
add_bullet_point(doc, "Browser: Modern web browser (Chrome, Edge, Firefox)")

add_heading(doc, "7.2 Hardware Requirements", 2)
add_bullet_point(doc, "Processor: Intel Core i3 or higher")
add_bullet_point(doc, "RAM: 8 GB or higher")
add_bullet_point(doc, "Storage: 256 GB SSD or higher")
add_bullet_point(doc, "Network: Stable internet connection")

add_heading(doc, "7.3 Functionalities", 2)
table = doc.add_table(rows=1, cols=2)
table.style = 'Table Grid'
hdr_cells = table.rows[0].cells
hdr_cells[0].text = 'Functionality'
hdr_cells[1].text = 'Description'
funcs = [
    ("Case Management", "Create, organize, and manage payment-related risk cases in a structured format."),
    ("Evidence Management", "Add and manage evidence files and logs related to a specific case for review."),
    ("Claims Management", "Store claims related to a case, allowing them to move through appropriate review states."),
    ("Rule Flags", "Apply deterministic rule-based checks to identify possible risk indicators and display them to the reviewer."),
    ("AI-Assisted Analysis", "Use the OpenRouter integration to provide supportive reasoning and analyze case information (not autonomous final detection)."),
    ("Human Review", "Allow a reviewer to examine the case, evidence, rule flags, and AI analysis to make the final informed decision."),
    ("Lifecycle Management", "Track and move cases through defined lifecycle and status stages (e.g., pending, reviewed, escalated)."),
    ("Audit Log", "Record important case actions, system checks, and human decisions to maintain traceability and accountability."),
    ("Testing / Scenario Validation", "Support controlled testing using deterministic mock scenarios to validate system logic without external dependencies.")
]
for f_name, f_desc in funcs:
    row_cells = table.add_row().cells
    row_cells[0].text = f_name
    row_cells[1].text = f_desc
doc.add_page_break()

# --- 8. TECHNOLOGY ---
add_heading(doc, "8. TECHNOLOGY", 1)

add_paragraph(doc, "React:", bold=True)
add_paragraph(doc, "React is a popular open-source JavaScript library for building user interfaces. It is used in PayProof AI to create a dynamic, single-page application that provides reviewers with a responsive and interactive dashboard for managing cases.")

add_paragraph(doc, "TypeScript:", bold=True)
add_paragraph(doc, "TypeScript is a strongly typed programming language that builds on JavaScript. It is used in the frontend to catch errors early during development and provide robust type definitions for the complex case data structures received from the backend.")

add_paragraph(doc, "Vite:", bold=True)
add_paragraph(doc, "Vite is a modern frontend build tool that significantly improves the frontend development experience. It is used to bundle and serve the React application quickly, ensuring fast hot-module replacement and optimized production builds.")

add_paragraph(doc, "Tailwind CSS:", bold=True)
add_paragraph(doc, "Tailwind CSS is a utility-first CSS framework. It is used in this project to rapidly style the user interface, ensuring the dashboard looks clean, professional, and is fully responsive without writing custom CSS files.")

add_paragraph(doc, "Python:", bold=True)
add_paragraph(doc, "Python is a versatile, high-level programming language. It serves as the primary language for the backend, chosen for its readability, vast ecosystem, and excellent support for AI integration and data manipulation.")

add_paragraph(doc, "FastAPI:", bold=True)
add_paragraph(doc, "FastAPI is a modern, fast web framework for building APIs with Python. It is used to create the REST API layer of PayProof AI, providing high performance, automatic data validation, and easy routing for frontend requests.")

add_paragraph(doc, "REST APIs:", bold=True)
add_paragraph(doc, "REST (Representational State Transfer) is an architectural style for APIs. PayProof AI utilizes REST APIs as the communication bridge between the React frontend and the FastAPI backend, allowing for scalable, stateless data exchange.")

add_paragraph(doc, "PostgreSQL:", bold=True)
add_paragraph(doc, "PostgreSQL is a powerful, open-source object-relational database system. It is used as the primary database in PayProof AI to store cases, evidence, audit logs, and claims securely and reliably.")

add_paragraph(doc, "SQLAlchemy:", bold=True)
add_paragraph(doc, "SQLAlchemy is the Python SQL toolkit and Object Relational Mapper (ORM). It is used to interact with the PostgreSQL database using Python objects, streamlining database operations and preventing SQL injection vulnerabilities.")

add_paragraph(doc, "OpenRouter API:", bold=True)
add_paragraph(doc, "OpenRouter provides a unified interface to access various Large Language Models. It is used in the system to power the AI-assisted analysis feature, generating supportive reasoning and insights based on case evidence.")

add_paragraph(doc, "Render:", bold=True)
add_paragraph(doc, "Render is a unified cloud platform for hosting applications. It is used to deploy and host the FastAPI backend and PostgreSQL database, making the API accessible over the internet.")

add_paragraph(doc, "Vercel:", bold=True)
add_paragraph(doc, "Vercel is a cloud platform optimized for frontend frameworks. It is used to deploy the React frontend application, providing fast global content delivery and continuous integration.")
doc.add_page_break()

# --- 9. SYSTEM ARCHITECTURE ---
add_heading(doc, "9. SYSTEM ARCHITECTURE", 1)
add_paragraph(doc, "PayProof AI employs a modern, decoupled client-server architecture. The system workflow ensures data is securely passed from the user interface through the business logic layer down to the database.")
add_paragraph(doc, "The fundamental architecture flow is as follows:")
add_paragraph(doc, "User (Human Reviewer)\n  ↓ interacts with\nReact + TypeScript + Vite Frontend (UI Dashboard)\n  ↓ sends HTTP requests to\nFastAPI REST API (Backend Server)\n  ↓ processes data via\nBusiness Logic / Rule-Based Risk Analysis\n  ↓ reads/writes data to\nPostgreSQL Database through SQLAlchemy", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)

add_paragraph(doc, "\nFor AI-assisted analysis, the flow extends as follows:")
add_paragraph(doc, "FastAPI Backend\n  ↓ formats case evidence and sends prompt to\nOpenRouter API\n  ↓ returns reasoning and suggestions to\nAI-Assisted Analysis Module (FastAPI)\n  ↓ serves insights to frontend for Human Review", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)

add_paragraph(doc, "\nSystem Workflow:", bold=True)
add_paragraph(doc, "1. Case Creation: New cases are initialized in the system via the REST API.")
add_paragraph(doc, "2. Evidence Collection: Relevant evidence and claims are attached to the case.")
add_paragraph(doc, "3. Rule-Based Checks: The backend evaluates the evidence against deterministic rules, generating rule flags.")
add_paragraph(doc, "4. AI-Assisted Analysis: The backend requests analysis from the OpenRouter API to provide contextual insights.")
add_paragraph(doc, "5. Human Review: The React frontend displays the case details, flags, and AI insights to the reviewer.")
add_paragraph(doc, "6. Decision / Escalation: The human reviewer takes action (e.g., approve, decline, escalate).")
add_paragraph(doc, "7. Audit Log Update: Every state transition and decision is permanently logged in the PostgreSQL database.")
doc.add_page_break()

# --- 10. DEMONSTRATION ---
add_heading(doc, "10. DEMONSTRATION", 1)
add_paragraph(doc, "The following sections demonstrate the primary user interface screens and features of the PayProof AI application.")

add_paragraph(doc, "Figure 1 – PayProof AI Landing/Dashboard Page", bold=True)
add_paragraph(doc, "[INSERT PAYPROOF AI LANDING/DASHBOARD SCREENSHOT HERE]", align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph(doc, "The landing page presents the user with an overview of the system. It provides immediate access to active cases, recent audit activities, and overall system metrics, acting as the central hub for the human reviewer.")

add_paragraph(doc, "Figure 2 – Case Creation Page", bold=True)
add_paragraph(doc, "[INSERT PAYPROOF AI CASE CREATION SCREENSHOT HERE]", align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph(doc, "Reviewers navigate here to create a new payment-risk case. They input initial transaction details, customer identifiers, and the primary claim context, which initializes the case in the PostgreSQL database.")

add_paragraph(doc, "Figure 3 – Case List / Case Management Page", bold=True)
add_paragraph(doc, "[INSERT PAYPROOF AI CASE LIST SCREENSHOT HERE]", align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph(doc, "This page displays a structured table of all pending and resolved cases. Reviewers can filter and sort cases based on lifecycle status, priority, or creation date to efficiently manage their workload.")

add_paragraph(doc, "Figure 4 – Case Details and Evidence Page", bold=True)
add_paragraph(doc, "[INSERT PAYPROOF AI CASE DETAILS SCREENSHOT HERE]", align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph(doc, "Upon opening a specific case, the reviewer is presented with detailed transaction data. This section allows the reviewer to examine uploaded evidence files, logs, and specific customer claims centrally.")

add_paragraph(doc, "Figure 5 – Rule Flags / Risk Analysis Page", bold=True)
add_paragraph(doc, "[INSERT PAYPROOF AI RULE FLAGS SCREENSHOT HERE]", align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph(doc, "This section highlights the deterministic rule-based risk indicators. Any logical contradictions or rule violations detected by the FastAPI backend are flagged here in clear English for the reviewer's immediate attention.")

add_paragraph(doc, "Figure 6 – AI-Assisted Analysis Page", bold=True)
add_paragraph(doc, "[INSERT PAYPROOF AI ANALYSIS SCREENSHOT HERE]", align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph(doc, "Here, the reviewer can review the explainable analysis generated via the OpenRouter API. The AI provides a summary of the evidence, highlights concerns, and suggests a recommended action, acting strictly as a support tool.")

add_paragraph(doc, "Figure 7 – Human Review / Decision Page", bold=True)
add_paragraph(doc, "[INSERT PAYPROOF AI DECISION SCREENSHOT HERE]", align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph(doc, "This is the core human-in-the-loop interface. The reviewer evaluates the evidence, rule flags, and AI suggestions, and then selects the final decision (e.g., approve, decline, or escalate). The AI cannot override this human action.")

add_paragraph(doc, "Figure 8 – Audit Log / Case Lifecycle Page", bold=True)
add_paragraph(doc, "[INSERT PAYPROOF AI AUDIT LOG SCREENSHOT HERE]", align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph(doc, "Finally, this section displays the immutable history of the case. It records exactly when the case was created, when evidence was added, when the AI was consulted, and the identity and timestamp of the final human decision.")
doc.add_page_break()

# --- 11. TESTING ---
add_heading(doc, "11. TESTING", 1)
add_paragraph(doc, "Rigorous testing was conducted to ensure the reliability and stability of PayProof AI. The system was systematically tested for:")
add_bullet_point(doc, "Frontend Functionality: Ensuring React components render correctly, state is managed properly, and currency/amount displays are formatted accurately.")
add_bullet_point(doc, "API Communication: Validating that the Vite frontend correctly sends and receives data from the FastAPI REST endpoints.")
add_bullet_point(doc, "Database Operations: Testing SQLAlchemy ORM models for accurate case creation, evidence handling, and audit logging.")
add_bullet_point(doc, "Risk Analysis Logic: Verifying that rule flags correctly trigger when contradictory evidence is submitted.")
add_bullet_point(doc, "AI-Assisted Analysis: Ensuring the system properly formats prompts for the OpenRouter API and correctly parses the returned reasoning.")
add_bullet_point(doc, "Human Review Workflow: Validating lifecycle/status transitions to ensure cases move through the correct operational stages upon human decision.")
add_paragraph(doc, "\nControlled Scenarios:", bold=True)
add_paragraph(doc, "The project utilizes 15 controlled testing scenarios/rotations to validate the system's behavior across various dispute edge cases. Furthermore, a deterministic mock verification mode (MOCK_VERIFIER) is implemented. This mode allows for robust, controlled testing of the system pipeline without relying on external API tool calls, ensuring the backend logic can be tested consistently and rapidly.")
doc.add_page_break()

# --- 12. BENEFITS TO THE INSTITUTION ---
add_heading(doc, "12. BENEFITS TO THE COMPANY / INSTITUTION THROUGH YOUR REPORT", 1)
add_paragraph(doc, "The development of PayProof AI serves as a comprehensive demonstration of applied software engineering and modern system design. Through this report and project, several key benefits are demonstrated:")
add_bullet_point(doc, "Practical Software Development: The project showcases the ability to architect, develop, and deploy a complete, scalable full-stack web application from scratch.")
add_bullet_point(doc, "Human-in-the-Loop Systems: It demonstrates an understanding of how to responsibly integrate artificial intelligence. By designing an AI-assisted decision support system rather than an autonomous decision-maker, it highlights a mature approach to risk analysis.")
add_bullet_point(doc, "Structured Data & Auditability: The robust implementation of PostgreSQL and SQLAlchemy emphasizes the critical importance of data integrity, relational database management, and the necessity of immutable audit logs in enterprise software.")
add_bullet_point(doc, "REST API Best Practices: The use of FastAPI demonstrates modern, fast, and type-safe API development, showcasing skills highly relevant to the current technology industry.")
add_bullet_point(doc, "Real-World Problem Solving: The project tackles a genuine industry challenge—payment risk review—proving that the theoretical knowledge gained can be effectively applied to create functional, valuable software solutions.")
doc.add_page_break()

# --- 13. CONCLUSION ---
add_heading(doc, "13. CONCLUSION", 1)
add_paragraph(doc, "PayProof AI successfully demonstrates the integration of modern web development, REST APIs, robust database management, and intelligent APIs to solve the complex problem of payment risk analysis. By combining React on the frontend and FastAPI on the backend, the system provides a fast, reliable, and user-friendly platform for organizing case information and evidence.")
add_paragraph(doc, "The implementation of deterministic rule-based checks alongside OpenRouter's AI-assisted analysis creates a powerful hybrid review environment. Crucially, the system is fundamentally designed to support reviewers by organizing information and providing contextual reasoning, rather than replacing human decision-making entirely. The strict human-in-the-loop workflow, backed by comprehensive audit logging, ensures that all decisions remain transparent, explainable, and accountable.")
add_paragraph(doc, "Overall, developing PayProof AI provided immense practical learning value. It bridged the gap between academic theory and real-world software engineering, resulting in a complete, deployed system that effectively addresses a significant challenge in digital transaction management.")
doc.add_page_break()

# --- 14. BIBLIOGRAPHY ---
add_heading(doc, "14. BIBLIOGRAPHY", 1)
add_bullet_point(doc, "React Documentation. (n.d.). React – A JavaScript library for building user interfaces. Retrieved from https://react.dev/")
add_bullet_point(doc, "TypeScript Documentation. (n.d.). TypeScript: JavaScript With Syntax For Types. Retrieved from https://www.typescriptlang.org/")
add_bullet_point(doc, "Vite Documentation. (n.d.). Vite | Next Generation Frontend Tooling. Retrieved from https://vitejs.dev/")
add_bullet_point(doc, "Tailwind CSS Documentation. (n.d.). Tailwind CSS - Rapidly build modern websites. Retrieved from https://tailwindcss.com/")
add_bullet_point(doc, "Python Software Foundation. (n.d.). Python Language Reference. Retrieved from https://docs.python.org/3/")
add_bullet_point(doc, "FastAPI Documentation. (n.d.). FastAPI. Retrieved from https://fastapi.tiangolo.com/")
add_bullet_point(doc, "PostgreSQL Global Development Group. (n.d.). PostgreSQL: The World's Most Advanced Open Source Relational Database. Retrieved from https://www.postgresql.org/docs/")
add_bullet_point(doc, "SQLAlchemy Documentation. (n.d.). SQLAlchemy - The Database Toolkit for Python. Retrieved from https://docs.sqlalchemy.org/")
add_bullet_point(doc, "OpenRouter API Documentation. (n.d.). OpenRouter: A unified API for LLMs. Retrieved from https://openrouter.ai/docs")
add_bullet_point(doc, "Render Documentation. (n.d.). Render · Cloud Hosting for Developers. Retrieved from https://render.com/docs")
add_bullet_point(doc, "Vercel Documentation. (n.d.). Vercel Documentation. Retrieved from https://vercel.com/docs")

doc.save('PayProof_AI_SCRC_Internship_Report.docx')
print("Document generated successfully.")
