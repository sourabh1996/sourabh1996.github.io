# Retrieval-Augmented Generation (RAG)

**Intermediate · 9 modules · 45 lessons · ~20 hrs**  
Track 6 · Generative AI · Bootcamp syllabus module(s): 23, 21, 24

Ground LLMs in your own data: embeddings and vector databases, loaders, splitters, retrievers, hybrid search, reranking, vectorless and multimodal RAG, and evaluating it all.

**Finish first:** [LangChain Complete Guide](../langchain-complete-guide/course.md), [Databases: SQL and NoSQL](../databases-sql-and-nosql/course.md)  
**Unlocks:** [Agentic RAG Systems](../agentic-rag-systems/course.md), [Agent Evals, Observability and Reliability](../agent-evals-observability-and-reliability/course.md), [Cloud Data Platforms](../cloud-data-platforms/course.md)

## Course content

<a id="m1"></a>
### 1. Start Here (1 lesson)
- [How This Course Works](01-start-here/how-this-course-works.md) · Article ✍️ *written*

<a id="m2"></a>
### 2. Introduction to RAG (4 lessons)
> **Before you start:** [Generative AI and LLM Foundations › How LLMs Work](../generative-ai-and-llm-foundations/course.md#m3)

- [What is RAG?](02-introduction-to-rag/what-is-rag.md) · Article ✍️ *written*
- [RAG vs Fine-Tuning vs Prompting](02-introduction-to-rag/rag-vs-fine-tuning-vs-prompting.md) · Article ✍️ *written*
- [The RAG Pipeline End to End](02-introduction-to-rag/the-rag-pipeline-end-to-end.md) · Article ✍️ *written*
- [Lab: RAG from scratch, no framework](02-introduction-to-rag/lab-rag-from-scratch-no-framework.md) · Lab ➕ ✍️ *written*

<a id="m3"></a>
### 3. Embeddings and Vector Databases (5 lessons)
> **Before you start:** [NLP for Machine Learning › Word Embeddings](../nlp-for-machine-learning/course.md#m5), [Databases: SQL and NoSQL › Relational Databases and SQL](../databases-sql-and-nosql/course.md#m2)

- Embeddings and Similarity Search · Article
- Semantic Search Explained · Article
- Vector vs SQL vs NoSQL Databases · Article
- Storage and Indexing (HNSW, IVF) · Article
- In-Memory, On-Disk and Cloud Vector DBs · Article

<a id="m4"></a>
### 4. Vector Database Tools (9 lessons)
> **Before you start:** [Databases: SQL and NoSQL › NoSQL with MongoDB Atlas](../databases-sql-and-nosql/course.md#m4)

- Chroma · Article
- FAISS · Article
- Qdrant · Article
- Pinecone · Article
- LanceDB · Article
- Vector Search in MongoDB and Cassandra · Article
- Embedding-Based Retrieval Pipelines · Article
- Lab: Same search in three vector DBs · Lab
- Lab: Semantic search over your notes · Lab

<a id="m5"></a>
### 5. RAG Building Blocks in LangChain (7 lessons)
> **Before you start:** [LangChain Complete Guide › Chains and Runnables](../langchain-complete-guide/course.md#m6)

- [Document Loaders](05-rag-building-blocks-in-langchain/document-loaders.md) · Article ✍️ *written*
- [PDF, Web, CSV and Directory Loaders](05-rag-building-blocks-in-langchain/pdf-web-csv-and-directory-loaders.md) · Article ✍️ *written*
- [load() vs lazy_load()](05-rag-building-blocks-in-langchain/load-vs-lazy-load.md) · Article ✍️ *written*
- [Text Splitters](05-rag-building-blocks-in-langchain/text-splitters.md) · Article ✍️ *written*
- [Vector Stores in LangChain](05-rag-building-blocks-in-langchain/vector-stores-in-langchain.md) · Article ✍️ *written*
- [Retrievers](05-rag-building-blocks-in-langchain/retrievers.md) · Article ✍️ *written*
- [MMR, Multi-Query and Contextual Compression Retrievers](05-rag-building-blocks-in-langchain/mmr-multi-query-and-contextual-compression-retrievers.md) · Article ✍️ *written*

<a id="m6"></a>
### 6. Implementing RAG (7 lessons)
> **Before you start:** [LangChain Complete Guide › Chains and Runnables](../langchain-complete-guide/course.md#m6), [Vector Database Tools](#m4)

- [RAG with LangChain and a Vector DB](06-implementing-rag/rag-with-langchain-and-a-vector-db.md) · Article ✍️ *written*
- [Chunking Strategies](06-implementing-rag/chunking-strategies.md) · Article ➕ ✍️ *written*
- [Retrieval Methods](06-implementing-rag/retrieval-methods.md) · Article ✍️ *written*
- [Hybrid Search](06-implementing-rag/hybrid-search.md) · Article ✍️ *written*
- [Reranking](06-implementing-rag/reranking.md) · Article ✍️ *written*
- [Lab: Chat with a PDF](06-implementing-rag/lab-chat-with-a-pdf.md) · Lab ✍️ *written*
- [Project: Chat with Any YouTube Video](06-implementing-rag/project-chat-with-any-youtube-video.md) · Lab ✍️ *written*

<a id="m7"></a>
### 7. Advanced RAG (3 lessons)
- [Memory in RAG Systems](07-advanced-rag/memory-in-rag-systems.md) · Article ✍️ *written*
- [Multimodal RAG](07-advanced-rag/multimodal-rag.md) · Article ✍️ *written*
- [Lab: RAG over images and text](07-advanced-rag/lab-rag-over-images-and-text.md) · Lab ✍️ *written*

<a id="m8"></a>
### 8. Vectorless RAG (5 lessons)
- Limits of Vector RAG · Article
- PageIndex and Chunk-Free Segmentation · Article
- The Document Tree Model · Article
- The Iterative Search Loop · Article
- Deterministic Page Referencing · Article

<a id="m9"></a>
### 9. RAG Evaluation (4 lessons)
> **Before you start:** [Implementing RAG](#m6)

- The RAG Triad Metrics · Article
- LLM-as-a-Judge · Article
- Turn-Based Evaluation with Ragas · Article
- Lab: Evaluate your RAG app with Ragas · Lab
