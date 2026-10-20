# Retrieval-Augmented Generation (RAG)

**Intermediate · 9 modules · 45 lessons · ~20 hrs**  
Track 6 · Generative AI · Bootcamp syllabus module(s): 23, 21, 24

Ground LLMs in your own data: embeddings and vector databases, loaders, splitters, retrievers, hybrid search, reranking, vectorless and multimodal RAG, and evaluating it all.

**Finish first:** [LangChain Complete Guide](../langchain-complete-guide/course.md), [Databases: SQL and NoSQL](../databases-sql-and-nosql/course.md)  
**Unlocks:** [Agentic RAG Systems](../agentic-rag-systems/course.md), [Agent Evals, Observability and Reliability](../agent-evals-observability-and-reliability/course.md), [Cloud Data Platforms](../cloud-data-platforms/course.md)

## Course content

<a id="m1"></a>
### 1. Start Here (1 lesson)
- How This Course Works · Article

<a id="m2"></a>
### 2. Introduction to RAG (4 lessons)
> **Before you start:** [Generative AI and LLM Foundations › How LLMs Work](../generative-ai-and-llm-foundations/course.md#m3)

- What is RAG? · Article
- RAG vs Fine-Tuning vs Prompting · Article
- The RAG Pipeline End to End · Article
- Lab: RAG from scratch, no framework · Lab ➕

<a id="m3"></a>
### 3. Embeddings and Vector Databases (5 lessons)
> **Before you start:** [NLP for Machine Learning › Word Embeddings](../nlp-for-machine-learning/course.md#m5), [Databases: SQL and NoSQL › Relational Databases and SQL](../databases-sql-and-nosql/course.md#m2)

- [Embeddings and Similarity Search](03-embeddings-and-vector-databases/embeddings-and-similarity-search.md) · Article ✍️ *written*
- [Semantic Search Explained](03-embeddings-and-vector-databases/semantic-search-explained.md) · Article ✍️ *written*
- [Vector vs SQL vs NoSQL Databases](03-embeddings-and-vector-databases/vector-vs-sql-vs-nosql-databases.md) · Article ✍️ *written*
- [Storage and Indexing (HNSW, IVF)](03-embeddings-and-vector-databases/storage-and-indexing-hnsw-ivf.md) · Article ✍️ *written*
- [In-Memory, On-Disk and Cloud Vector DBs](03-embeddings-and-vector-databases/in-memory-on-disk-and-cloud-vector-dbs.md) · Article ✍️ *written*

<a id="m4"></a>
### 4. Vector Database Tools (9 lessons)
> **Before you start:** [Databases: SQL and NoSQL › NoSQL with MongoDB Atlas](../databases-sql-and-nosql/course.md#m4)

- [Chroma](04-vector-database-tools/chroma.md) · Article ✍️ *written*
- [FAISS](04-vector-database-tools/faiss.md) · Article ✍️ *written*
- [Qdrant](04-vector-database-tools/qdrant.md) · Article ✍️ *written*
- [Pinecone](04-vector-database-tools/pinecone.md) · Article ✍️ *written*
- [LanceDB](04-vector-database-tools/lancedb.md) · Article ✍️ *written*
- [Vector Search in MongoDB and Cassandra](04-vector-database-tools/vector-search-in-mongodb-and-cassandra.md) · Article ✍️ *written*
- [Embedding-Based Retrieval Pipelines](04-vector-database-tools/embedding-based-retrieval-pipelines.md) · Article ✍️ *written*
- [Lab: Same search in three vector DBs](04-vector-database-tools/lab-same-search-in-three-vector-dbs.md) · Lab ✍️ *written*
- [Lab: Semantic search over your notes](04-vector-database-tools/lab-semantic-search-over-your-notes.md) · Lab ✍️ *written*

<a id="m5"></a>
### 5. RAG Building Blocks in LangChain (7 lessons)
> **Before you start:** [LangChain Complete Guide › Chains and Runnables](../langchain-complete-guide/course.md#m6)

- Document Loaders · Article
- PDF, Web, CSV and Directory Loaders · Article
- load() vs lazy_load() · Article
- Text Splitters · Article
- Vector Stores in LangChain · Article
- Retrievers · Article
- MMR, Multi-Query and Contextual Compression Retrievers · Article

<a id="m6"></a>
### 6. Implementing RAG (7 lessons)
> **Before you start:** [LangChain Complete Guide › Chains and Runnables](../langchain-complete-guide/course.md#m6), [Vector Database Tools](#m4)

- RAG with LangChain and a Vector DB · Article
- Chunking Strategies · Article ➕
- Retrieval Methods · Article
- Hybrid Search · Article
- Reranking · Article
- Lab: Chat with a PDF · Lab
- Project: Chat with Any YouTube Video · Lab

<a id="m7"></a>
### 7. Advanced RAG (3 lessons)
- Memory in RAG Systems · Article
- Multimodal RAG · Article
- Lab: RAG over images and text · Lab

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
