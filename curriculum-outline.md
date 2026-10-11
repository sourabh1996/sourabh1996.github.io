# Agentic AI Platform: Course Catalog (Draft v4)

> Built from the *Ultimate Data Science & GenAI Bootcamp V3.0* syllabus Sourabh shared, laid out like the DataVidhya Learn section.
> Every topic in the syllabus is mapped to a lesson; see [syllabus-coverage.md](syllabus-coverage.md). Topics marked ➕ are additions beyond the syllabus.
> The platform is text only: every topic is one in-depth **Article**, with **Labs** where the reader builds something. Hours are estimates (article 25 min, lab 45 min).
> Each course lists the courses to finish first, and each module links to the exact earlier modules it builds on.

**31 courses · 165 modules · 599 lessons · ~276 hours**

## Track 1 · Python and Data Foundations

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 1 | [Python Fundamentals](courses/python-fundamentals/course.md) | Beginner | 1 | 6 | 22 | 11 | Nothing, start here |
| 2 | [Advanced Python Programming](courses/advanced-python-programming/course.md) | Intermediate | 2 | 5 | 16 | 7 | [Python Fundamentals](courses/python-fundamentals/course.md) |
| 3 | [Numerical Computing and Data Analysis](courses/numerical-computing-and-data-analysis/course.md) | Beginner | 3, 4 | 5 | 20 | 9 | [Python Fundamentals](courses/python-fundamentals/course.md) |
| 4 | [Data Visualization with Matplotlib and Seaborn](courses/data-visualization-with-matplotlib-and-seaborn/course.md) | Beginner | 5 | 3 | 8 | 4 | [Numerical Computing and Data Analysis](courses/numerical-computing-and-data-analysis/course.md) |
| 5 | [Databases: SQL and NoSQL](courses/databases-sql-and-nosql/course.md) | Beginner | 6 | 4 | 13 | 6 | [Python Fundamentals](courses/python-fundamentals/course.md) |
| 6 | [Interactive Data Apps with Streamlit](courses/interactive-data-apps-with-streamlit/course.md) | Beginner | 7 | 3 | 7 | 4 | [Python Fundamentals](courses/python-fundamentals/course.md), [Numerical Computing and Data Analysis](courses/numerical-computing-and-data-analysis/course.md) |

- **Python Fundamentals:** Learn Python from zero: values, operators, control flow, strings, collections, functions and generators.
- **Advanced Python Programming:** Write reusable, robust Python with OOP, decorators, file handling, modules and proper error handling.
- **Numerical Computing and Data Analysis:** Process data fast with NumPy arrays and pandas DataFrames: indexing, transforming, dates, text and statistics.
- **Data Visualization with Matplotlib and Seaborn:** Turn data into clear charts: Matplotlib basics, Seaborn statistical plots and visual storytelling.
- **Databases: SQL and NoSQL:** Store and query data with PostgreSQL on Supabase and documents in MongoDB Atlas.
- **Interactive Data Apps with Streamlit:** Turn Python scripts into interactive web apps with widgets, session state and async.

## Track 2 · Statistics

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 7 | [Statistics Foundations](courses/statistics-foundations/course.md) | Beginner | 8 | 7 | 19 | 8 | [Numerical Computing and Data Analysis](courses/numerical-computing-and-data-analysis/course.md) |
| 8 | [Inferential Statistics](courses/inferential-statistics/course.md) | Intermediate | 9 | 4 | 10 | 5 | [Statistics Foundations](courses/statistics-foundations/course.md) |

- **Statistics Foundations:** The core ideas behind all data science: data types, averages, spread, probability, distributions and estimation.
- **Inferential Statistics:** Make decisions with data: hypothesis tests, p-values, Bayes' theorem and chi-square tests.

## Track 3 · Machine Learning

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 9 | [Feature Engineering and EDA](courses/feature-engineering-and-eda/course.md) | Intermediate | 10, 11 | 8 | 46 | 20 | [Numerical Computing and Data Analysis](courses/numerical-computing-and-data-analysis/course.md), [Data Visualization with Matplotlib and Seaborn](courses/data-visualization-with-matplotlib-and-seaborn/course.md), [Statistics Foundations](courses/statistics-foundations/course.md) |
| 10 | [Machine Learning Fundamentals](courses/machine-learning-fundamentals/course.md) | Intermediate | 12 | 7 | 41 | 18 | [Feature Engineering and EDA](courses/feature-engineering-and-eda/course.md), [Statistics Foundations](courses/statistics-foundations/course.md) |
| 11 | [Ensembles and Unsupervised Learning](courses/ensembles-and-unsupervised-learning/course.md) | Intermediate | 13 | 4 | 17 | 8 | [Machine Learning Fundamentals](courses/machine-learning-fundamentals/course.md) |
| 12 | [MLOps with MLflow](courses/mlops-with-mlflow/course.md) | Advanced | 15 | 5 | 15 | 7 | [Machine Learning Fundamentals](courses/machine-learning-fundamentals/course.md) |

- **Feature Engineering and EDA:** Get data, explore it and prepare it for models: imputation, outliers, scaling, encoding, pipelines, PCA and real case studies.
- **Machine Learning Fundamentals:** Understand and implement the core supervised learning algorithms from scratch and learn how to evaluate and tune them.
- **Ensembles and Unsupervised Learning:** Boost accuracy with voting, bagging, random forests, AdaBoost, gradient boosting, XGBoost and stacking, then learn clustering.
- **MLOps with MLflow:** Manage the ML lifecycle: track experiments, register models and serve them in production.

## Track 4 · Production Engineering and Big Data

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 13 | [Production APIs with FastAPI](courses/production-apis-with-fastapi/course.md) | Intermediate | 14 | 7 | 28 | 13 | [Advanced Python Programming](courses/advanced-python-programming/course.md) |
| 14 | [Big Data with PySpark](courses/big-data-with-pyspark/course.md) | Advanced | 17 | 4 | 12 | 5 | [Numerical Computing and Data Analysis](courses/numerical-computing-and-data-analysis/course.md), [Databases: SQL and NoSQL](courses/databases-sql-and-nosql/course.md) |

- **Production APIs with FastAPI:** Build production-grade APIs with FastAPI: endpoints, Pydantic validation, serving ML models, Docker and AWS deployment.
- **Big Data with PySpark:** Process data that won't fit in memory with Spark: architecture, DataFrames, Spark SQL and optimisation.

## Track 5 · Deep Learning and NLP

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 15 | [NLP for Machine Learning](courses/nlp-for-machine-learning/course.md) | Intermediate | 16 | 6 | 23 | 11 | [Machine Learning Fundamentals](courses/machine-learning-fundamentals/course.md) |
| 16 | [Deep Learning Foundations](courses/deep-learning-foundations/course.md) | Intermediate | 18 | 6 | 19 | 8 | [Machine Learning Fundamentals](courses/machine-learning-fundamentals/course.md) |
| 17 | [Deep Learning with PyTorch](courses/deep-learning-with-pytorch/course.md) | Intermediate | PyTorch | 6 | 25 | 12 | [Deep Learning Foundations](courses/deep-learning-foundations/course.md) |
| 18 | [Sequence Models, Attention and Transformers](courses/sequence-models-attention-and-transformers/course.md) | Advanced | 19 | 5 | 13 | 6 | [Deep Learning Foundations](courses/deep-learning-foundations/course.md), [NLP for Machine Learning](courses/nlp-for-machine-learning/course.md) |

- **NLP for Machine Learning:** Turn text into features and predictions: the NLP pipeline, preprocessing, POS tagging, TF-IDF, Word2Vec and text classification.
- **Deep Learning Foundations:** How neural networks really work: perceptrons, backpropagation, activations, losses, optimisers, Keras and PyTorch.
- **Deep Learning with PyTorch:** Go hands-on with PyTorch: tensors, autograd, training loops, DataLoaders, GPUs, CNNs, transfer learning, RNNs and LSTMs.
- **Sequence Models, Attention and Transformers:** From RNNs to Transformers: LSTMs, GRUs, attention, self-attention, BERT and GPT.

## Track 6 · Generative AI

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 19 | [Generative AI and LLM Foundations](courses/generative-ai-and-llm-foundations/course.md) | Beginner | 20 | 5 | 18 | 8 | [Sequence Models, Attention and Transformers](courses/sequence-models-attention-and-transformers/course.md), [Advanced Python Programming](courses/advanced-python-programming/course.md) |
| 20 | [Vector Databases for AI](courses/vector-databases-for-ai/course.md) | Intermediate | 21 | 5 | 15 | 7 | [Generative AI and LLM Foundations](courses/generative-ai-and-llm-foundations/course.md), [Databases: SQL and NoSQL](courses/databases-sql-and-nosql/course.md) |
| 21 | [LangChain Complete Guide](courses/langchain-complete-guide/course.md) | Intermediate | 22 | 8 | 39 | 17 | [Generative AI and LLM Foundations](courses/generative-ai-and-llm-foundations/course.md) |
| 22 | [Retrieval-Augmented Generation (RAG)](courses/retrieval-augmented-generation-rag/course.md) | Intermediate | 23 | 5 | 22 | 10 | [Vector Databases for AI](courses/vector-databases-for-ai/course.md), [LangChain Complete Guide](courses/langchain-complete-guide/course.md) |
| 23 | [Enterprise LLM Systems](courses/enterprise-llm-systems/course.md) | Advanced | 24 | 6 | 25 | 11 | [Retrieval-Augmented Generation (RAG)](courses/retrieval-augmented-generation-rag/course.md) |

- **Generative AI and LLM Foundations:** What generative AI is, how LLMs work, and how to use them well: foundation models, tokens, prompting and structured output.
- **Vector Databases for AI:** Embeddings, similarity search and the vector databases behind RAG: Chroma, FAISS, Qdrant, Pinecone and LanceDB.
- **LangChain Complete Guide:** Build LLM apps with LangChain: models, prompts, structured output, parsers, chains, runnables, tools, tool calling and agents.
- **Retrieval-Augmented Generation (RAG):** Ground LLMs in your own data: loaders, splitters, vector stores, retrievers, the RAG pipeline, hybrid search, reranking and multimodal RAG.
- **Enterprise LLM Systems:** Run LLM systems at scale: RAG evaluation with Ragas, observability with LangSmith and Opik, vectorless RAG and LLM gateways.

## Track 7 · Agentic AI

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 24 | [Agentic AI Fundamentals](courses/agentic-ai-fundamentals/course.md) | Beginner | 25 | 6 | 18 | 8 | [Generative AI and LLM Foundations](courses/generative-ai-and-llm-foundations/course.md) |
| 25 | [LangGraph Fundamentals](courses/langgraph-fundamentals/course.md) | Intermediate | 26 | 7 | 32 | 15 | [Agentic AI Fundamentals](courses/agentic-ai-fundamentals/course.md), [LangChain Complete Guide](courses/langchain-complete-guide/course.md) |
| 26 | [LangGraph State and Memory](courses/langgraph-state-and-memory/course.md) | Intermediate | 27 | 4 | 10 | 5 | [LangGraph Fundamentals](courses/langgraph-fundamentals/course.md) |
| 27 | [Human-in-the-Loop with LangGraph](courses/human-in-the-loop-with-langgraph/course.md) | Intermediate | 28 | 4 | 9 | 4 | [LangGraph State and Memory](courses/langgraph-state-and-memory/course.md) |
| 28 | [Agentic RAG Systems](courses/agentic-rag-systems/course.md) | Advanced | 29 | 4 | 11 | 5 | [Retrieval-Augmented Generation (RAG)](courses/retrieval-augmented-generation-rag/course.md), [LangGraph Fundamentals](courses/langgraph-fundamentals/course.md) |
| 29 | [Model Context Protocol (MCP)](courses/model-context-protocol-mcp/course.md) | Intermediate | 30 | 5 | 20 | 9 | [Agentic AI Fundamentals](courses/agentic-ai-fundamentals/course.md), [LangChain Complete Guide](courses/langchain-complete-guide/course.md) |
| 30 | [Multi-Agent Research System (Capstone)](courses/multi-agent-research-system-capstone/course.md) | Advanced | 31 | 5 | 15 | 7 | [Human-in-the-Loop with LangGraph](courses/human-in-the-loop-with-langgraph/course.md), [Agentic RAG Systems](courses/agentic-rag-systems/course.md), [Model Context Protocol (MCP)](courses/model-context-protocol-mcp/course.md), [Production APIs with FastAPI](courses/production-apis-with-fastapi/course.md), [Enterprise LLM Systems](courses/enterprise-llm-systems/course.md) |

- **Agentic AI Fundamentals:** What AI agents are, how the agent loop works, and how to build one from scratch before touching a framework.
- **LangGraph Fundamentals:** Build agent workflows as graphs: core concepts, sequential, parallel, conditional and looping workflows, chatbots, persistence, tools and subgraphs.
- **LangGraph State and Memory:** Master LangGraph's state system: schemas, reducers, multiple schemas, and trimming messages to save context.
- **Human-in-the-Loop with LangGraph:** Make agents interactive and controllable: streaming, interrupts, breakpoints, human edits to state and time travel.
- **Agentic RAG Systems:** Let agents decide how to retrieve: Adaptive RAG, Corrective RAG and Self-RAG, locally and with vector DBs.
- **Model Context Protocol (MCP):** The standard way to plug tools and data into AI apps: why MCP exists, its architecture and lifecycle, and building local and remote servers and clients.
- **Multi-Agent Research System (Capstone):** Build and ship a multi-agent system that researches, analyses and writes reports, with CI/CD on AWS.

## Track 8 · Projects

| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |
|---|---|---|---|---|---|---|---|
| 31 | [End-to-End AI Projects](courses/end-to-end-ai-projects/course.md) | Advanced | Projects | 6 | 11 | 8 | Nothing, start here |

- **End-to-End AI Projects:** Portfolio projects across data engineering, ML, deep learning, GenAI and agentic AI, each deployed with CI/CD.

## Article template (every article follows this)

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
