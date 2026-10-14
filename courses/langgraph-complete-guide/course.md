# LangGraph Complete Guide

**Intermediate · 10 modules · 51 lessons · ~24 hrs**  
Track 7 · Agentic AI · Bootcamp syllabus module(s): 26, 27, 28

Build agents as graphs, from your first node to production: workflow patterns, state and reducers, tools, persistence, memory, human-in-the-loop, time travel and subgraphs.

**Finish first:** [Agentic AI Fundamentals](../agentic-ai-fundamentals/course.md), [LangChain Complete Guide](../langchain-complete-guide/course.md)  
**Unlocks:** [Agentic RAG Systems](../agentic-rag-systems/course.md), [Context Engineering and Agent Memory](../context-engineering-and-agent-memory/course.md), [Agent Frameworks and SDKs](../agent-frameworks-and-sdks/course.md), [Multi-Agent Research System (Capstone)](../multi-agent-research-system-capstone/course.md)

## Course content

<a id="m1"></a>
### 1. Start Here (1 lesson)
- [How This Course Works](01-start-here/how-this-course-works.md) · Article ✍️ *written*

<a id="m2"></a>
### 2. Getting Started (7 lessons)
> **Before you start:** [Agentic AI Fundamentals › The Agent Loop](../agentic-ai-fundamentals/course.md#m3), [LangChain Complete Guide › Chains and Runnables](../langchain-complete-guide/course.md#m6)

- [LangChain vs LangGraph: Why LangGraph Exists](02-getting-started/langchain-vs-langgraph-why-langgraph-exists.md) · Article ✍️ *written*
- [What is LangGraph?](02-getting-started/what-is-langgraph.md) · Article ✍️ *written*
- [Graphs, Nodes, Edges and State](02-getting-started/graphs-nodes-edges-and-state.md) · Article ✍️ *written*
- [The LangGraph Execution Model](02-getting-started/the-langgraph-execution-model.md) · Article ✍️ *written*
- [Simple Graphs and Node Connections](02-getting-started/simple-graphs-and-node-connections.md) · Article ✍️ *written*
- [LangGraph Studio](02-getting-started/langgraph-studio.md) · Article ✍️ *written*
- [Lab: Your first graph](02-getting-started/lab-your-first-graph.md) · Lab ✍️ *written*

<a id="m3"></a>
### 3. Workflow Patterns in LangGraph (6 lessons)
- [Sequential Workflows and Prompt Chaining](03-workflow-patterns-in-langgraph/sequential-workflows-and-prompt-chaining.md) · Article ✍️ *written*
- [Parallel Workflows](03-workflow-patterns-in-langgraph/parallel-workflows.md) · Article ✍️ *written*
- [Conditional Workflows](03-workflow-patterns-in-langgraph/conditional-workflows.md) · Article ✍️ *written*
- [Iterative (Looping) Workflows](03-workflow-patterns-in-langgraph/iterative-looping-workflows.md) · Article ✍️ *written*
- [Lab: Essay evaluator with parallel graders](03-workflow-patterns-in-langgraph/lab-essay-evaluator-with-parallel-graders.md) · Lab ✍️ *written*
- [Lab: Post generator with an evaluator loop](03-workflow-patterns-in-langgraph/lab-post-generator-with-an-evaluator-loop.md) · Lab ✍️ *written*

<a id="m4"></a>
### 4. State in Depth (5 lessons)
- The LangGraph State System · Article
- State Schemas and Data Flow · Article
- State Reducers · Article
- Multiple Schemas · Article
- Lab: A multi-schema agent · Lab

<a id="m5"></a>
### 5. Workflows and Agents (10 lessons)
> **Before you start:** [Agentic AI Fundamentals › Tools and Function Calling](../agentic-ai-fundamentals/course.md#m4), [Agentic AI Fundamentals › Reasoning Patterns](../agentic-ai-fundamentals/course.md#m5)

- [Chains in LangGraph](05-workflows-and-agents/chains-in-langgraph.md) · Article ✍️ *written*
- [Routers](05-workflows-and-agents/routers.md) · Article ✍️ *written*
- LangChain Agents · Article
- ReAct Agents with AgentExecutor · Article
- [Building Agents](05-workflows-and-agents/building-agents.md) · Article ✍️ *written*
- [Agents with Memory](05-workflows-and-agents/agents-with-memory.md) · Article ✍️ *written*
- [Tools in LangGraph: ToolNode and tools_condition](05-workflows-and-agents/tools-in-langgraph-toolnode-and-tools-condition.md) · Article ✍️ *written*
- [Using MCP Tools in LangGraph](05-workflows-and-agents/using-mcp-tools-in-langgraph.md) · Article ✍️ *written*
- [RAG Inside a LangGraph Agent](05-workflows-and-agents/rag-inside-a-langgraph-agent.md) · Article ✍️ *written*
- [Lab: Rebuild your scratch agent in LangGraph](05-workflows-and-agents/lab-rebuild-your-scratch-agent-in-langgraph.md) · Lab ✍️ *written*

<a id="m6"></a>
### 6. Chatbots and Persistence (5 lessons)
> **Before you start:** [APIs and Apps: FastAPI, Streamlit and Docker › Streamlit Basics](../apis-and-apps-fastapi-streamlit-and-docker/course.md#m6)

- [Building a Chatbot with LangGraph](06-chatbots-and-persistence/building-a-chatbot-with-langgraph.md) · Article ✍️ *written*
- [Persistence and Checkpointers](06-chatbots-and-persistence/persistence-and-checkpointers.md) · Article ✍️ *written*
- [Threads, Fault Tolerance and Resuming](06-chatbots-and-persistence/threads-fault-tolerance-and-resuming.md) · Article ✍️ *written*
- [Persistent Storage with SQLite](06-chatbots-and-persistence/persistent-storage-with-sqlite.md) · Article ✍️ *written*
- [Lab: Chatbot UI with Streamlit, streaming and saved chats](06-chatbots-and-persistence/lab-chatbot-ui-with-streamlit-streaming-and-saved-chats.md) · Lab ✍️ *written*

<a id="m7"></a>
### 7. Memory (4 lessons)
> **Before you start:** [Generative AI and LLM Foundations › How LLMs Work](../generative-ai-and-llm-foundations/course.md#m3)

- Trimming and Filtering Messages · Article
- Summarising Long Conversations · Article ➕
- Long-Term Memory with Stores · Article
- Lab: Keep a long chat under budget · Lab

<a id="m8"></a>
### 8. Human-in-the-Loop and Debugging (8 lessons)
- Streaming Real-Time Updates · Article
- Breakpoints · Article
- Pausing with interrupt and Resuming with Command · Article
- Editing State with Human Input · Article
- Dynamic Breakpoints · Article
- Time Travel: Rewind and Replay · Article
- Lab: Approval step before a risky tool · Lab
- Lab: Debug an agent with time travel · Lab

<a id="m9"></a>
### 9. Subgraphs (3 lessons)
- [What are Subgraphs?](09-subgraphs/what-are-subgraphs.md) · Article ✍️ *written*
- [Shared vs Different State in Subgraphs](09-subgraphs/shared-vs-different-state-in-subgraphs.md) · Article ✍️ *written*
- [Lab: Translation workflow with a subgraph](09-subgraphs/lab-translation-workflow-with-a-subgraph.md) · Lab ✍️ *written*

<a id="m10"></a>
### 10. Deployment and Observability (2 lessons)
- [Deploying and Running LangGraph Apps](10-deployment-and-observability/deploying-and-running-langgraph-apps.md) · Article ✍️ *written*
- [LangSmith Observability for LangGraph](10-deployment-and-observability/langsmith-observability-for-langgraph.md) · Article ✍️ *written*
