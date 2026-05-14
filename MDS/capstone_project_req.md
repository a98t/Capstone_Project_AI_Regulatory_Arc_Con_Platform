1. Use Case Scenarios

Select one of the following scenarios for your capstone project:


🧑‍💻
Personal Knowledge Assistant
Multi-agent system combining document RAG with web search fallback via MCP.

Research Agent indexes personal documents, Web Agent handles live queries, Synthesis Agent combines results and provides coherent responses to user questions.

📝
Code Documentation Generator
Analyzer Agent reads GitHub repositories via MCP, RAG Agent retrieves similar code patterns from documentation corpus, Writer Agent generates comprehensive documentation.

System should handle multiple programming languages and documentation formats.

📈
Financial News Analyst
Data Agent fetches market data from various sources, News Agent scrapes financial news and reports, Analysis Agent combines RAG-retrieved historical patterns with current data to provide investment insights and market analysis.

🎓
Learning Companion
Content Agent manages educational materials via RAG, Quiz Agent generates personalized questions based on learning progress, Progress Agent tracks learning milestones and adapts difficulty.

System should support multiple subjects and learning styles.

🍳
Recipe Recommendation System
Ingredient Agent processes user dietary preferences and available ingredients, Recipe Agent searches recipe database via RAG, Nutrition Agent adds nutritional information and health considerations.

Should handle dietary restrictions and cultural preferences.

🎤
Meeting Assistant
Transcript Agent processes meeting recordings and converts to text, Action Agent extracts tasks and decisions via RAG pattern matching, Follow-up Agent generates summaries and schedules follow-up actions.

Must handle multiple speakers and meeting formats.

🛍️
Product Research Helper
Search Agent finds products across multiple e-commerce platforms, Review Agent analyzes customer sentiment using RAG, Compare Agent creates detailed comparison reports.

Should identify fake reviews and price manipulation.

📰
Content Curation Bot
Collector Agent aggregates content from RSS feeds and social platforms, Filter Agent uses RAG for relevance scoring and quality assessment, Curator Agent creates themed collections and newsletters.

Must handle content freshness and duplicate detection.

✈️
Travel Planner Assistant
Location Agent fetches destination data and points of interest, Weather Agent provides weather forecasts via MCP, Itinerary Agent uses RAG for travel patterns to create optimal trip plans.

Should consider seasonality, budget, and travel preferences.

💊
Health Data Tracker
Input Agent processes health metrics from various sources, Pattern Agent uses RAG for trend analysis and anomaly detection, Advice Agent suggests actions based on health knowledge base.

Must include appropriate medical disclaimers and emergency detection.

Scenario of your choice
A student may propose a custom project topic. The student must discuss and get approval for the idea from the course team before starting work. The proposal may be approved if the idea and complexity level correspond to the example scenarios above and allow demonstration of all required skills and knowledge. The final decision on approval rests with the review committee.

The custom scenario must meet the following general requirements:

Multi-agent architecture: at least 3 agents with clearly defined, distinct roles and responsibilities
RAG pipeline: meaningful retrieval-augmented generation over a domain-specific knowledge base or document corpus
MCP integration: at least one external data source or tool connected via MCP protocol
Real-world applicability: the system must solve a tangible, clearly articulated problem
Inter-agent communication: agents must collaborate, delegate tasks, or share context — not operate in complete isolation
Testability: the use case must support both positive and negative test scenarios, including edge cases and adversarial inputs
Demonstrability: the system must be presentable in a 2–5 minute video demo showing end-to-end functionality

2. Non-Functional Requirements

📊
Observability & Monitoring
LLM Tracing: Track all agent interactions, token usage, and response quality
Performance Metrics: Monitor response times, success rates, and system throughput
Error Tracking: Comprehensive logging of failures and system errors
User Feedback: Implement rating systems for response quality assessment
Resource Usage: Track memory, CPU, and API quota consumption
🔒
Security & Safety
Input Validation: Sanitize all user inputs and API responses
Content Filtering: Implement guardrails against harmful or inappropriate content
Privacy Protection: PII detection and data anonymization capabilities
Access Control: Implement authentication and authorization mechanisms
Rate Limiting: Prevent abuse and manage resource consumption
✓
RAG Quality Assurance
Retrieval Accuracy: Measure precision and recall of document retrieval
Answer Relevance: Evaluate semantic similarity and factual correctness
Source Attribution: Ensure proper citation and traceability
Hallucination Detection: Identify and flag potentially false information
Bias Assessment: Monitor for unfair or discriminatory outputs
💰
Cost & Resource Management
Local-First Architecture: Minimize cloud dependencies and external costs
Free Tier Optimization: Stay within API limits and free service quotas
Efficient Processing: Implement caching and optimize resource usage
Scalability: Support concurrent users without performance degradation
Data Management: Implement retention policies and storage optimization
⚖️
Compliance & Ethics
Industry Standards: Implement domain-specific compliance requirements
Transparency: Provide clear information about system capabilities and limitations
Consent Management: Handle user data with appropriate permissions
Audit Trail: Maintain logs for accountability and debugging
Graceful Degradation: Handle service failures with appropriate fallbacks

3. Success Criteria

Base Requirements (70 Points - Pass Threshold)
Working Application: Functional multi-agent system demonstrated in video
Code Delivery: Complete codebase with clear structure and comments
LLM Behavior Tests: Both positive and negative test scenarios
Normal user flow validation
Edge case and adversarial prompt handling
Video Demo: 2-5 minute demonstration showing:
Live system operation
Test execution (positive & negative cases)
Self-review with code commentary

Excellence Bonuses (30 Points Total)
+10 Points: UX & Presentation: Polished UI, smooth UX, investor-ready demo quality
+10 Points: Data Quality: Well-prepared datasets, proper data handling, quality validation
+10 Points: Code Excellence: Clean architecture, software engineering best practices, thoughtful design patterns (AI-generated code is fine, but show you understand it)

Deliverables
Architecture Blueprint: Complete system design with technology stack and rationale
Video Demo: 2-5 minutes with voiceover explaining functionality and code choices
Code Repository: Well-structured project with README and setup instructions
Test Suite: Automated tests demonstrating LLM behavior validation
Self-Review: Code commentary addressing architecture decisions and trade-offs
Executive Summary: A concise 1-2 page overview of the project's objectives, key findings, and business value

4. Step-by-Step Implementation Guide

Phase 1: Planning & Setup (2-3 hours)
Choose use case and define core problem
Use GenAI with internet access (Perplexity, ChatGPT with browsing, or similar) to:
Research current best practices and technology trends
Compare agent frameworks and select optimal one
Identify suitable LLM providers and data sources
Design system architecture with latest patterns
Create architecture blueprint documenting:
System components and agent roles
Technology stack (frameworks, models, databases)
Data flow and integration points
MCP tool selections and rationale
Set up project structure with observability tools

Phase 2: Core Agent Development (10-15 hours)
Implement first agent with basic RAG pipeline
Add MCP integrations for external data
Build inter-agent communication layer
Test individual agent behaviors

Phase 3: Multi-Agent Orchestration (8-10 hours)
Connect agents with task delegation logic
Implement state management and error handling
Add monitoring and tracing
Iterative testing and refinement

Phase 4: Testing & Validation (5-8 hours)
Write positive test scenarios (expected behavior)
Write negative test scenarios (edge cases, adversarial)
Implement automated test suite
Manual testing and bug fixes

Phase 5: Polish & Documentation (5-7 hours)
Refine UI/UX if applicable
Clean up code and add comments
Write README with setup instructions (do not commit credentials!)
Prepare demo script and talking points

Phase 6: Video Production (3-5 hours)
Record 10-15 min live coding session (optional bonus content)
Record 2-5 min polished demo:
App walkthrough
Test execution (positive & negative)
Code self-review with commentary
Edit and finalize video

Phase 7: Executive Summary (1-2 hours)
Write a concise 1-2 page overview covering:
Problem statement and project objectives (why this project exists)
Key technical decisions and architecture highlights
Results, findings, and business value
Lessons learned and potential next steps
Target audience: People not involved in the details — review committee, management, investors.
The reader should go through this section only and walk away with a full understanding of what matters most — without reading the rest of the document
💡
Tips for Success
Short iterations: Build incrementally, test often
AI pair programming: Use GitHub Copilot or similar tools
Focus on core value: Prioritize working system over perfect code
Document trade-offs: Show understanding of decisions made
Practice demo: Rehearse before recording