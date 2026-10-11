# Agentic AI Platform: Course Catalog (Draft v4)

> Built from the *Ultimate Data Science & GenAI Bootcamp V3.0* syllabus Sourabh shared, laid out like the DataVidhya Learn section.
> Every topic in the syllabus is mapped to a lesson; see [syllabus-coverage.md](syllabus-coverage.md). Topics marked ➕ are additions beyond the syllabus.
> Every topic gets a short **Video** followed by a **(Deep Dive) Article**, with **Labs** where the reader builds something. Hours are estimates (video 15 min, article 20 min, lab 45 min).
> Each course lists the courses to finish first, and each module links to the exact earlier modules it builds on.

**30 courses · 142 modules · 716 lessons · ~248 hours**

## Track 1 · Python and Data Foundations

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 1 | [Python Fundamentals](courses/01-python-fundamentals/course.md) | Beginner | 1 | 6 | 38 | 14 | Nothing, start here |
| 2 | [Advanced Python Programming](courses/02-advanced-python-programming/course.md) | Intermediate | 2 | 5 | 28 | 10 | [Python Fundamentals](courses/01-python-fundamentals/course.md) |
| 3 | [Numerical Computing and Data Analysis](courses/03-numerical-computing-and-data-analysis/course.md) | Beginner | 3, 4 | 5 | 36 | 12 | [Python Fundamentals](courses/01-python-fundamentals/course.md) |
| 4 | [Data Visualization with Matplotlib and Seaborn](courses/04-data-visualization-with-matplotlib-and-seaborn/course.md) | Beginner | 5 | 3 | 13 | 5 | [Numerical Computing and Data Analysis](courses/03-numerical-computing-and-data-analysis/course.md) |
| 5 | [Databases: SQL and NoSQL](courses/05-databases-sql-and-nosql/course.md) | Beginner | 6 | 4 | 23 | 8 | [Python Fundamentals](courses/01-python-fundamentals/course.md) |
| 6 | [Interactive Data Apps with Streamlit](courses/06-interactive-data-apps-with-streamlit/course.md) | Beginner | 7 | 3 | 11 | 4 | [Python Fundamentals](courses/01-python-fundamentals/course.md), [Numerical Computing and Data Analysis](courses/03-numerical-computing-and-data-analysis/course.md) |

- **Python Fundamentals:** Learn Python from zero: values, operators, control flow, strings, collections, functions and generators.
- **Advanced Python Programming:** Write reusable, robust Python with OOP, decorators, file handling, modules and proper error handling.
- **Numerical Computing and Data Analysis:** Process data fast with NumPy arrays and pandas DataFrames: indexing, transforming, dates, text and statistics.
- **Data Visualization with Matplotlib and Seaborn:** Turn data into clear charts: Matplotlib basics, Seaborn statistical plots and visual storytelling.
- **Databases: SQL and NoSQL:** Store and query data with PostgreSQL on Supabase and documents in MongoDB Atlas.
- **Interactive Data Apps with Streamlit:** Turn Python scripts into interactive web apps with widgets, session state and async.

## Track 2 · Statistics

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 7 | [Statistics Foundations](courses/07-statistics-foundations/course.md) | Beginner | 8 | 7 | 35 | 11 | [Numerical Computing and Data Analysis](courses/03-numerical-computing-and-data-analysis/course.md) |
| 8 | [Inferential Statistics](courses/08-inferential-statistics/course.md) | Intermediate | 9 | 4 | 17 | 6 | [Statistics Foundations](courses/07-statistics-foundations/course.md) |

- **Statistics Foundations:** The core ideas behind all data science: data types, averages, spread, probability, distributions and estimation.
- **Inferential Statistics:** Make decisions with data: hypothesis tests, p-values, Bayes' theorem and chi-square tests.

## Track 3 · Machine Learning

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 9 | [Feature Engineering and EDA](courses/09-feature-engineering-and-eda/course.md) | Intermediate | 10, 11 | 5 | 27 | 9 | [Numerical Computing and Data Analysis](courses/03-numerical-computing-and-data-analysis/course.md), [Data Visualization with Matplotlib and Seaborn](courses/04-data-visualization-with-matplotlib-and-seaborn/course.md), [Statistics Foundations](courses/07-statistics-foundations/course.md) |
| 10 | [Machine Learning Fundamentals](courses/10-machine-learning-fundamentals/course.md) | Intermediate | 12 | 5 | 28 | 10 | [Feature Engineering and EDA](courses/09-feature-engineering-and-eda/course.md), [Statistics Foundations](courses/07-statistics-foundations/course.md) |
| 11 | [Ensembles and Unsupervised Learning](courses/11-ensembles-and-unsupervised-learning/course.md) | Intermediate | 13 | 4 | 15 | 5 | [Machine Learning Fundamentals](courses/10-machine-learning-fundamentals/course.md) |
| 12 | [MLOps with MLflow](courses/12-mlops-with-mlflow/course.md) | Advanced | 15 | 5 | 27 | 9 | [Machine Learning Fundamentals](courses/10-machine-learning-fundamentals/course.md) |

- **Feature Engineering and EDA:** Prepare data for models and explore it properly: cleaning, scaling, encoding, selection and real case studies.
- **Machine Learning Fundamentals:** Understand and implement the core supervised learning algorithms and how to evaluate them.
- **Ensembles and Unsupervised Learning:** Boost accuracy with bagging, random forests, gradient boosting and XGBoost, then meet clustering.
- **MLOps with MLflow:** Manage the ML lifecycle: track experiments, register models and serve them in production.

## Track 4 · Production Engineering and Big Data

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 13 | [Production APIs with FastAPI](courses/13-production-apis-with-fastapi/course.md) | Intermediate | 14 | 4 | 21 | 7 | [Advanced Python Programming](courses/02-advanced-python-programming/course.md) |
| 14 | [Big Data with PySpark](courses/14-big-data-with-pyspark/course.md) | Advanced | 17 | 4 | 22 | 7 | [Numerical Computing and Data Analysis](courses/03-numerical-computing-and-data-analysis/course.md), [Databases: SQL and NoSQL](courses/05-databases-sql-and-nosql/course.md) |

- **Production APIs with FastAPI:** Build production-grade APIs with FastAPI, Pydantic validation, routers, error handling and OpenAPI docs.
- **Big Data with PySpark:** Process data that won't fit in memory with Spark: architecture, DataFrames, Spark SQL and optimisation.

## Track 5 · Deep Learning and NLP

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 15 | [NLP for Machine Learning](courses/15-nlp-for-machine-learning/course.md) | Intermediate | 16 | 5 | 21 | 7 | [Machine Learning Fundamentals](courses/10-machine-learning-fundamentals/course.md) |
| 16 | [Deep Learning Foundations](courses/16-deep-learning-foundations/course.md) | Intermediate | 18 | 6 | 35 | 11 | [Machine Learning Fundamentals](courses/10-machine-learning-fundamentals/course.md) |
| 17 | [Sequence Models, Attention and Transformers](courses/17-sequence-models-attention-and-transformers/course.md) | Advanced | 19 | 5 | 23 | 8 | [Deep Learning Foundations](courses/16-deep-learning-foundations/course.md), [NLP for Machine Learning](courses/15-nlp-for-machine-learning/course.md) |

- **NLP for Machine Learning:** Turn text into features: tokenisation, lemmatisation, POS tagging, NER, bag of words, TF-IDF and Word2Vec.
- **Deep Learning Foundations:** How neural networks really work: perceptrons, backpropagation, activations, losses, optimisers, Keras and PyTorch.
- **Sequence Models, Attention and Transformers:** From RNNs to Transformers: LSTMs, GRUs, attention, self-attention, BERT and GPT.

## Track 6 · Generative AI

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 18 | [Generative AI and LLM Foundations](courses/18-generative-ai-and-llm-foundations/course.md) | Beginner | 20 | 5 | 29 | 10 | [Sequence Models, Attention and Transformers](courses/17-sequence-models-attention-and-transformers/course.md), [Advanced Python Programming](courses/02-advanced-python-programming/course.md) |
| 19 | [Vector Databases for AI](courses/19-vector-databases-for-ai/course.md) | Intermediate | 21 | 5 | 25 | 8 | [Generative AI and LLM Foundations](courses/18-generative-ai-and-llm-foundations/course.md), [Databases: SQL and NoSQL](courses/05-databases-sql-and-nosql/course.md) |
| 20 | [LangChain Complete Guide](courses/20-langchain-complete-guide/course.md) | Intermediate | 22 | 5 | 26 | 9 | [Generative AI and LLM Foundations](courses/18-generative-ai-and-llm-foundations/course.md) |
| 21 | [Retrieval-Augmented Generation (RAG)](courses/21-retrieval-augmented-generation-rag/course.md) | Intermediate | 23 | 4 | 22 | 8 | [Vector Databases for AI](courses/19-vector-databases-for-ai/course.md), [LangChain Complete Guide](courses/20-langchain-complete-guide/course.md) |
| 22 | [Enterprise LLM Systems](courses/22-enterprise-llm-systems/course.md) | Advanced | 24 | 6 | 43 | 15 | [Retrieval-Augmented Generation (RAG)](courses/21-retrieval-augmented-generation-rag/course.md) |

- **Generative AI and LLM Foundations:** What generative AI is, how LLMs work, and how to use them well: tokens, prompting and structured output.
- **Vector Databases for AI:** Embeddings, similarity search and the vector databases behind RAG: Chroma, FAISS, Qdrant, Pinecone and LanceDB.
- **LangChain Complete Guide:** Build LLM apps with LangChain: chat models, prompts, tools, LCEL chains, memory, LangSmith and LangServe.
- **Retrieval-Augmented Generation (RAG):** Ground LLMs in your own data: the RAG pipeline, chunking, hybrid search, reranking, memory and multimodal RAG.
- **Enterprise LLM Systems:** Run LLM systems at scale: RAG evaluation with Ragas, observability with LangSmith and Opik, vectorless RAG and LLM gateways.

## Track 7 · Agentic AI

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 23 | [Agentic AI Fundamentals](courses/23-agentic-ai-fundamentals/course.md) | Beginner | 25 | 6 | 31 | 10 | [Generative AI and LLM Foundations](courses/18-generative-ai-and-llm-foundations/course.md) |
| 24 | [LangGraph Fundamentals](courses/24-langgraph-fundamentals/course.md) | Intermediate | 26 | 4 | 19 | 7 | [Agentic AI Fundamentals](courses/23-agentic-ai-fundamentals/course.md), [LangChain Complete Guide](courses/20-langchain-complete-guide/course.md) |
| 25 | [LangGraph State and Memory](courses/25-langgraph-state-and-memory/course.md) | Intermediate | 27 | 4 | 15 | 5 | [LangGraph Fundamentals](courses/24-langgraph-fundamentals/course.md) |
| 26 | [Human-in-the-Loop with LangGraph](courses/26-human-in-the-loop-with-langgraph/course.md) | Intermediate | 28 | 4 | 13 | 5 | [LangGraph State and Memory](courses/25-langgraph-state-and-memory/course.md) |
| 27 | [Agentic RAG Systems](courses/27-agentic-rag-systems/course.md) | Advanced | 29 | 4 | 19 | 7 | [Retrieval-Augmented Generation (RAG)](courses/21-retrieval-augmented-generation-rag/course.md), [LangGraph Fundamentals](courses/24-langgraph-fundamentals/course.md) |
| 28 | [Model Context Protocol (MCP)](courses/28-model-context-protocol-mcp/course.md) | Intermediate | 30 | 4 | 18 | 6 | [Agentic AI Fundamentals](courses/23-agentic-ai-fundamentals/course.md), [LangChain Complete Guide](courses/20-langchain-complete-guide/course.md) |
| 29 | [Multi-Agent Research System (Capstone)](courses/29-multi-agent-research-system-capstone/course.md) | Advanced | 31 | 5 | 27 | 9 | [Human-in-the-Loop with LangGraph](courses/26-human-in-the-loop-with-langgraph/course.md), [Agentic RAG Systems](courses/27-agentic-rag-systems/course.md), [Model Context Protocol (MCP)](courses/28-model-context-protocol-mcp/course.md), [Production APIs with FastAPI](courses/13-production-apis-with-fastapi/course.md), [Enterprise LLM Systems](courses/22-enterprise-llm-systems/course.md) |

- **Agentic AI Fundamentals:** What AI agents are, how the agent loop works, and how to build one from scratch before touching a framework.
- **LangGraph Fundamentals:** Build agent workflows as graphs: nodes, edges, chains, routers, agents with memory and LangGraph Studio.
- **LangGraph State and Memory:** Master LangGraph's state system: schemas, reducers, multiple schemas, and trimming messages to save context.
- **Human-in-the-Loop with LangGraph:** Make agents interactive and controllable: streaming, breakpoints, human edits to state and time travel.
- **Agentic RAG Systems:** Let agents decide how to retrieve: Adaptive RAG, Corrective RAG and Self-RAG, locally and with vector DBs.
- **Model Context Protocol (MCP):** The standard way to plug tools and data into AI apps: MCP architecture, clients, servers and the ecosystem.
- **Multi-Agent Research System (Capstone):** Build and ship a multi-agent system that researches, analyses and writes reports, with CI/CD on AWS.

## Track 8 · Projects

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 30 | [End-to-End AI Projects](courses/30-end-to-end-ai-projects/course.md) | Advanced | Projects | 6 | 9 | 6 | Nothing, start here |

- **End-to-End AI Projects:** Portfolio projects across data engineering, ML, deep learning, GenAI and agentic AI, each deployed with CI/CD.

## Article template (every Deep Dive follows this)

1. **Title:** "Topic? The Complete Guide"
2. **Before you start:** links to the earlier lessons this one builds on (from the module's prerequisites).
3. **Introduction:** a real-world hook, why the topic is misunderstood, what the reader will know by the end.
4. **Key Insight** callout: the one sentence to remember.
5. **Core Explanation:** H3 subsections, each with an everyday analogy, a hand-drawn style diagram and bold-lead bullets. Any term taught elsewhere links to its lesson.
6. **Try It Yourself:** an interactive playground embedded in the page (spec included in each article).
7. **Topic-specific section** (patterns, skills, when to use what).
8. **Real-World Examples:** two or three named, concrete stories.
9. **Common Misconceptions:** numbered, each corrected.
10. **Interview Relevance:** what interviewers ask and what a strong answer covers.
11. **Key Takeaways:** five to seven bullets, then **Up next**.
