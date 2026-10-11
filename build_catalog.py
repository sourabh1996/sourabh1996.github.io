"""Builds the course catalog (markdown + JSON) from one structured spec.

Each module lists topics; every topic becomes one in-depth Article (the site is
text only). Labs are listed explicitly. Every course opens
with a "Start Here" module. Items marked ADDED are not in the bootcamp syllabus.
"""
import json, os, re, sys

OUT = sys.argv[1]
ADD = "➕ "  # marks topics added beyond the syllabus

HOURS = {"Article": 0.4, "Lab": 0.75}

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

# (track, [courses]); course = (title, level, syllabus_modules, card, [modules])
# module = (title, [topics], [labs])
TRACKS = [
("Track 1 · Python and Data Foundations", [
 ("Python Fundamentals", "Beginner", [1],
  "Learn Python from zero: values, operators, control flow, strings, collections, functions and generators.",
  [("Getting Started with Python", ["What is Python and Why Use It?", "Python vs Other Languages", "Numbers, Booleans and Strings"], ["Lab: Set up Python and run your first script"]),
   ("Core Language Concepts", ["Containers and Mutability", "Operators and Precedence"], ["Lab: Build a unit converter"]),
   ("Control Flow", ["if, elif and else", "for and while Loops", "break, continue and range()"], ["Lab: Number guessing game"]),
   ("Strings and Data Structures", ["Working with Strings", "Lists and Tuples", "Sets", "Dictionaries and Dictionary Views", "List and Dictionary Comprehensions"], ["Lab: Word frequency counter"]),
   ("Functions and Iterators", ["Functions and Parameter Passing", "Iterators and Generators", "Lambda, map and Functional Style"], ["Lab: Build a tiny text-processing toolkit"])]),
 ("Advanced Python Programming", "Intermediate", [2],
  "Write reusable, robust Python with OOP, decorators, file handling, modules and proper error handling.",
  [("Object-Oriented Programming", ["Classes and Objects", "Inheritance and Polymorphism", "Encapsulation and Abstraction", "Decorators, classmethod and staticmethod", "Dunder Methods"], ["Lab: Model a library system with classes"]),
   ("File Handling", ["Reading and Writing Files", "Buffered I/O and Other File Methods"], ["Lab: Log file analyser"]),
   ("Modules and Exceptions", ["Importing and Managing Modules", "try/except and Custom Exceptions", "Error Handling Best Practices"], []),
   (ADD + "Concurrency for AI Apps", [ADD + "Threads, Processes and Async", ADD + "async and await for API Calls"], [ADD + "Lab: Call 10 APIs concurrently"])]),
 ("Numerical Computing and Data Analysis", "Beginner", [3, 4],
  "Process data fast with NumPy arrays and pandas DataFrames: indexing, transforming, dates, text and statistics.",
  [("NumPy Essentials", ["What is a NumPy Array?", "Creating, Indexing and Slicing Arrays", "Data Types and Array Attributes", "Broadcasting and Iterating over Arrays", "Array Manipulation and Arithmetic", "Statistical, Sorting, Searching and Counting Functions", "Binary and String Functions", "The Matrix Library, Copies and Views"], ["Lab: Image as a NumPy array"]),
   ("pandas Core", ["Series, DataFrames (and the Retired Panel)", "Selecting, Sorting and Indexing Data", "Reindexing and Iteration"], ["Lab: Explore a sales dataset"]),
   ("Text, Dates and Categories in pandas", ["Working with Text Data", "Dates, Times and Timedeltas", "Categorical Data"], []),
   ("Statistics and Plots in pandas", ["Descriptive Statistics in pandas", "Quick Visualisation with pandas"], ["Lab: Clean and summarise a messy CSV"])]),
 ("Data Visualization with Matplotlib and Seaborn", "Beginner", [5],
  "Turn data into clear charts: Matplotlib basics, Seaborn statistical plots and visual storytelling.",
  [("Matplotlib", ["How Matplotlib Thinks: Figures and Axes", "Creating and Customising Plots"], ["Lab: Recreate a published chart"]),
   ("Seaborn and Storytelling", ["Statistical Plots with Seaborn", "Histograms, Pair Plots and Heatmaps", "Styling Charts for Communication"], ["Lab: Build a one-page visual report"])]),
 ("Databases: SQL and NoSQL", "Beginner", [6],
  "Store and query data with PostgreSQL on Supabase and documents in MongoDB Atlas.",
  [("Relational Databases and SQL", ["What is a Relational Database?", "Writing SQL Queries", "Primary and Foreign Keys", "Joins and Unions"], []),
   ("PostgreSQL on Supabase", ["Setting Up Supabase", "Querying Supabase from Python"], ["Lab: Build a Supabase-backed notes database"]),
   ("NoSQL with MongoDB Atlas", ["What is a Document Database?", "Databases and Collections", "Insert, Find, Query and Sort", "Update, Delete and Drop"], ["Lab: Store chat history in MongoDB"])]),
 ("Interactive Data Apps with Streamlit", "Beginner", [7],
  "Turn Python scripts into interactive web apps with widgets, session state and async.",
  [("Streamlit Basics", ["What is Streamlit?", "Widgets and Layout"], ["Lab: Your first dashboard"]),
   ("State and Responsiveness", ["Session State", "async and await in Streamlit"], ["Lab: Build a chat UI shell for an LLM app"])]),
]),
("Track 2 · Statistics", [
 ("Statistics Foundations", "Beginner", [8],
  "The core ideas behind all data science: data types, averages, spread, probability, distributions and estimation.",
  [("Introduction to Statistics", ["What is Statistics?", "Descriptive vs Inferential Statistics", "Types of Data and Levels of Measurement"], []),
   ("Central Tendency and Dispersion", ["Mean, Median and Mode", "Range, Variance and Standard Deviation"], ["Lab: Summarise a dataset by hand and in code"]),
   ("Data Behaviour and Relationships", ["Skewness and Kurtosis", "Covariance and Correlation", "Random Variables and Sets"], []),
   ("Probability", ["Probability Basics", "PDF, PMF and CDF"], []),
   ("Distributions", ["Bernoulli, Binomial and Poisson", "Normal and Uniform Distributions", "Real-World Normal Distributions", "Z-Statistics and the Central Limit Theorem"], ["Lab: Simulate the Central Limit Theorem"]),
   ("Estimation", ["Population vs Sample", "Confidence Intervals"], [])]),
 ("Inferential Statistics", "Intermediate", [9],
  "Make decisions with data: hypothesis tests, p-values, Bayes' theorem and chi-square tests.",
  [("Hypothesis Testing", ["How Hypothesis Testing Works", "p-Values and Significance", "Confidence Levels and Decision Rules"], ["Lab: A/B test a website change"]),
   ("Bayesian Thinking", ["Bayes' Theorem", "Bayes in the Real World"], []),
   ("Chi-Square Tests", ["The Chi-Square Distribution", "Goodness-of-Fit and Independence Tests"], ["Lab: Chi-square tests in Python"])]),
]),
("Track 3 · Machine Learning", [
 ("Feature Engineering and EDA", "Intermediate", [10, 11],
  "Get data, explore it and prepare it for models: imputation, outliers, scaling, encoding, pipelines, PCA and real case studies.",
  [("Getting Data", ["Framing a Machine Learning Problem", "Loading CSV, JSON and SQL Data", "Fetching Data from APIs", "Web Scraping for Datasets"], ["Lab: Build a dataset from an API"]),
   ("Exploratory Data Analysis", ["What EDA Is and Why It Matters", "First Questions to Ask Your Data", "Univariate Analysis", "Bivariate and Multivariate Analysis", "Visualising Patterns and Relationships", "Automated EDA with Profiling Reports"], []),
   ("Data Cleaning", ["Handling Missing Data", "Complete Case Analysis", "Mean, Median and Arbitrary Value Imputation", "Imputing Missing Categories", "Missing Indicators and Random Sample Imputation", "KNN Imputer", "Iterative Imputer (MICE)", "Imbalanced Datasets", "Outliers", "Outliers with Z-Scores, IQR and Winsorisation"], ["Lab: Compare imputation strategies"]),
   ("Feature Scaling and Encoding", ["Normalisation vs Standardisation", "Encoding Categorical Variables", "One-Hot Encoding", "ColumnTransformer", "scikit-learn Pipelines"], ["Lab: One pipeline from raw data to model"]),
   ("Feature Transformation and Selection", ["Function and Power Transformers (Log, Box-Cox, Yeo-Johnson)", "Binning and Binarisation", "Mixed Variables", "Date and Time Features", "Feature Construction and Splitting", "Forward and Backward Selection", "Correlation for Feature Selection"], ["Lab: Feature-engineer a housing dataset"]),
   ("Dimensionality Reduction", ["The Curse of Dimensionality", "PCA: The Intuition", "PCA: The Maths Step by Step", "PCA in Practice"], ["Lab: Compress MNIST with PCA"]),
   ("EDA Case Studies", ["Case Study: Movie Review Sentiment", "Case Study: Wine Quality", "Case Study: Stock and Commodity Prices"], ["Lab: Full EDA report on a dataset of your choice"])]),
 ("Machine Learning Fundamentals", "Intermediate", [12],
  "Understand and implement the core supervised learning algorithms from scratch and learn how to evaluate and tune them.",
  [("What is Machine Learning?", ["AI vs ML vs DL vs Data Science", "Supervised, Unsupervised, Semi-Supervised and Reinforcement Learning", "Batch vs Online Learning", "Instance-Based vs Model-Based Learning", "Challenges in Machine Learning", "The Machine Learning Development Life Cycle", "Data Science and ML Job Roles", "Tensors: How Data Is Represented", "Setting Up Your ML Environment: Anaconda, Jupyter and Colab"], []),
   ("Regression", ["Simple and Multiple Linear Regression", "MSE, MAE, RMSE and R²", "Assumptions of Linear Regression", "Polynomial Regression", "The Bias-Variance Tradeoff"], ["Lab: Linear regression from scratch"]),
   ("Gradient Descent and Regularisation", ["Gradient Descent", "Batch, Stochastic and Mini-Batch Gradient Descent", "Ridge and Lasso Regularisation", "Elastic Net"], ["Lab: Gradient descent variants side by side"]),
   ("Classification", ["The Perceptron Trick", "Logistic Regression", "Sigmoid and Log Loss", "Softmax for Multiclass Problems", "Confusion Matrix, Precision, Recall and F1", "ROC Curves and AUC"], ["Lab: Spam classifier"]),
   ("More Supervised Algorithms", ["Support Vector Machines and Kernels", "Naive Bayes", "K-Nearest Neighbours", "Decision Trees", "Entropy, Gini and Information Gain", "Regression Trees"], ["Lab: Compare five classifiers on one dataset"]),
   ("Model Selection and Tuning", ["Train, Validation and Test Splits", "Data Leakage", "Cross-Validation", "Grid Search and Randomized Search", "Bayesian Optimisation with Optuna"], ["Lab: Tune a model without overfitting the test set"])]),
 ("Ensembles and Unsupervised Learning", "Intermediate", [13],
  "Boost accuracy with voting, bagging, random forests, AdaBoost, gradient boosting, XGBoost and stacking, then learn clustering.",
  [("Ensemble Learning", ["What is Ensemble Learning?", "Voting Ensembles", "Bagging vs Boosting", "Random Forests and Out-of-Bag Evaluation", "Feature Importance"], []),
   ("Boosting", ["AdaBoost", "Gradient Boosting", "XGBoost", "Stacking and Blending"], ["Lab: Win a mini Kaggle-style challenge with XGBoost"]),
   ("Unsupervised Learning", ["What is Clustering?", "K-Means", "K-Means from Scratch", "Hierarchical Clustering", "DBSCAN"], ["Lab: Customer segmentation"])]),
 ("MLOps with MLflow", "Advanced", [15],
  "Manage the ML lifecycle: track experiments, register models and serve them in production.",
  [("MLflow Fundamentals", ["What is MLflow?", "Installing and Setting Up MLflow"], []),
   ("Experiment Tracking", ["Logging Params, Metrics and Artifacts", "Artifact Management", "Autologging", "Analysing and Visualising Runs"], ["Lab: Track 20 experiments"]),
   ("Model Management", ["Model Registry", "Model Packaging", "Lifecycle Stages and Transitions"], []),
   ("Serving and Deployment", ["Real-Time Serving and Local Deployment", "Containerisation", "Cloud and Orchestration"], ["Lab: Serve a registered model"])]),
]),
("Track 4 · Production Engineering and Big Data", [
 ("Production APIs with FastAPI", "Intermediate", [14],
  "Build production-grade APIs with FastAPI: endpoints, Pydantic validation, serving ML models, Docker and AWS deployment.",
  [("APIs and FastAPI Fundamentals", ["What is an API?", "Why Machine Learning Needs APIs", "What is FastAPI and Why Use It?", "Sync vs Async in FastAPI", "Project Structure and Hello World", "HTTP Methods: GET, POST, PUT, DELETE"], ["Lab: Your first API"]),
   ("Endpoints in Depth", ["Path and Query Parameters", "Request Bodies and POST Endpoints", "Update and Delete Endpoints"], ["Lab: A complete CRUD API"]),
   ("Validation and Schemas", ["Pydantic Models", "Pydantic Field Validators and Computed Fields", "Response Models", "Handling Validation Errors"], []),
   ("Production Considerations", ["Errors and Status Codes", "Configuration and Environment Variables", "Dependency Injection and Routers", "OpenAPI and Swagger Docs", "Health Checks and API Versioning"], []),
   ("Serving Machine Learning Models", ["Serving a Trained Model with FastAPI", "A Streamlit Front End for Your API"], ["Lab: Wrap an ML model in an API"]),
   ("Docker and Cloud Deployment", ["Docker Fundamentals", "Dockerising a FastAPI App", "Deploying to AWS EC2"], ["Lab: Ship your ML API to AWS"])]),
 ("Big Data with PySpark", "Advanced", [17],
  "Process data that won't fit in memory with Spark: architecture, DataFrames, Spark SQL and optimisation.",
  [("The Big Data Problem", ["Why Single Machines Fail", "Distributed Computing and Spark", "Driver, Executors and Cluster Manager"], []),
   ("PySpark DataFrames and SQL", ["From pandas to PySpark", "Filters, Aggregations and Joins", "Spark SQL", "Complex Data Types"], ["Lab: Analyse a 10 GB dataset"]),
   ("Optimisation", ["Lazy Evaluation: Transformations vs Actions", "Reading the Spark UI", "Spot Instances and Cost"], [])]),
]),
("Track 5 · Deep Learning and NLP", [
 ("NLP for Machine Learning", "Intermediate", [16],
  "Turn text into features and predictions: the NLP pipeline, preprocessing, POS tagging, TF-IDF, Word2Vec and text classification.",
  [("Introduction to NLP", ["What is NLP?", "NLP Terminology and Roadmap", "The End-to-End NLP Pipeline", "Data Acquisition for NLP"], []),
   ("Text Preprocessing", ["Tokenisation", "Stemming, Lemmatisation and Stopwords", "POS Tagging and Named Entity Recognition", "Hidden Markov Models and the Viterbi Algorithm"], ["Lab: Preprocess a corpus with NLTK"]),
   ("Text Representation", ["Common Terms: Corpus, Vocabulary, Document", "One-Hot, Bag of Words and N-Grams", "TF-IDF"], ["Lab: TF-IDF search engine"]),
   ("Word Embeddings", ["What are Word Vectors?", "The Distributional Hypothesis", "Word2Vec", "CBOW and Skip-Gram"], ["Lab: Train Word2Vec on your own text"]),
   ("Text Classification", ["Text Classification Pipelines", "Classic ML vs Embeddings for Text Classification", "Deploying NLP Systems"], ["Project: Quora Duplicate Question Detection"])]),
 ("Deep Learning Foundations", "Intermediate", [18],
  "How neural networks really work: perceptrons, backpropagation, activations, losses, optimisers, Keras and PyTorch.",
  [("Introduction to Deep Learning", ["What is Deep Learning?", "Why Deep Learning Took Off"], []),
   ("Neural Networks", ["The Perceptron", "Artificial Neural Networks", "Forward and Backward Propagation", "The Chain Rule in Backprop"], ["Lab: A neural network from scratch in NumPy"]),
   ("Training Challenges", ["Vanishing and Exploding Gradients", "Activation Functions", "Loss Functions", "Optimisers"], []),
   ("Regularisation and Stability", ["Weight Initialisation", "Dropout", "Batch Normalisation"], []),
   ("Frameworks", ["Keras Fundamentals", "PyTorch Fundamentals", "Visualising Network Architecture and Training"], ["Lab: Same model in Keras and PyTorch"])]),
 ("Deep Learning with PyTorch", "Intermediate", ["PyTorch"],
  "Go hands-on with PyTorch: tensors, autograd, training loops, DataLoaders, GPUs, CNNs, transfer learning, RNNs and LSTMs.",
  [("PyTorch Basics", ["Why PyTorch? History, Features and Ecosystem", "PyTorch vs TensorFlow and Other Frameworks", "Tensors in PyTorch", "Tensor Operations", "Autograd: Automatic Differentiation"], ["Lab: Gradients by hand vs autograd"]),
   ("The Training Pipeline", ["A Training Loop from Scratch", "The torch.nn Module", "torch.optim and Loss Functions", "Dataset and DataLoader"], ["Lab: Rebuild the training loop with nn and DataLoader"]),
   ("Building and Improving Networks", ["Building an ANN for Fashion-MNIST", "Training on a GPU", "Reducing Overfitting: Dropout, Batch Norm and Weight Decay", "Hyperparameter Tuning with Optuna"], ["Lab: Push Fashion-MNIST accuracy from 83% to 89%"]),
   ("CNNs and Transfer Learning", ["Convolutional Neural Networks in PyTorch", "Transfer Learning"], ["Lab: CNN for Fashion-MNIST", "Lab: Fine-tune a pretrained model"]),
   ("Sequence Models in PyTorch", ["RNNs in PyTorch", "LSTMs in PyTorch"], ["Lab: Question answering with an RNN", "Lab: Next-word prediction with an LSTM"])]),
 ("Sequence Models, Attention and Transformers", "Advanced", [19],
  "From RNNs to Transformers: LSTMs, GRUs, attention, self-attention, BERT and GPT.",
  [("Sequence Models", ["Recurrent Neural Networks", "Sequence Modelling and Context"], []),
   ("Memory-Based Architectures", ["LSTMs", "GRUs"], ["Lab: Sentiment with an LSTM"]),
   ("Attention", ["What is Attention?", "Encoder-Decoder Models", "Self-Attention"], []),
   ("Transformers", ["The Transformer Architecture", "BERT", "GPT"], ["Lab: Fine-tune BERT for classification"])]),
]),
("Track 6 · Generative AI", [
 ("Generative AI and LLM Foundations", "Beginner", [20],
  "What generative AI is, how LLMs work, and how to use them well: foundation models, tokens, prompting and structured output.",
  [("Fundamentals of Generative AI", ["What is Generative AI?", "How Generative Models Work", "Generative vs Discriminative Models", "The GenAI Roadmap: Builder vs User", "Foundation Models"], []),
   (ADD + "How LLMs Work", [ADD + "What is a Large Language Model?", ADD + "Tokens and Context Windows", ADD + "Temperature and Model Settings", ADD + "Where LLMs Fail"], [ADD + "Lab: Your first LLM API call"]),
   (ADD + "Prompting and Structured Output", [ADD + "Prompting Fundamentals", ADD + "System Prompts and Roles", ADD + "Structured JSON Output"], [ADD + "Lab: Reliable JSON extraction"]),
   ("Advances and Applications", ["Recent Breakthroughs in GenAI", "GenAI Applications Across Industries", "The GenAI Project Lifecycle"], [])]),
 ("Vector Databases for AI", "Intermediate", [21],
  "Embeddings, similarity search and the vector databases behind RAG: Chroma, FAISS, Qdrant, Pinecone and LanceDB.",
  [("Introduction to Vector Databases", ["Embeddings and Similarity Search", "Semantic Search Explained", "Vector vs SQL vs NoSQL Databases"], []),
   ("Architecture", ["Storage and Indexing (HNSW, IVF)", "In-Memory, On-Disk and Cloud Vector DBs"], []),
   ("Tools", ["Chroma", "FAISS", "Qdrant", "Pinecone", "LanceDB"], ["Lab: Same search in three vector DBs"]),
   ("Integrations", ["Vector Search in MongoDB and Cassandra", "Embedding-Based Retrieval Pipelines"], ["Lab: Semantic search over your notes"])]),
 ("LangChain Complete Guide", "Intermediate", [22],
  "Build LLM apps with LangChain: models, prompts, structured output, parsers, chains, runnables, tools, tool calling and agents.",
  [("LangChain Foundations", ["What is LangChain?", "LangChain Components", "Data Connectors and API Integrations", "Setting Up a LangChain Project and API Keys"], []),
   ("Models", ["LLMs vs Chat Models", "Chat Models", "Embedding Models", "Open-Source Models with Hugging Face"], []),
   ("Prompts", ["Static vs Dynamic Prompts", "Prompt Templates", "ChatPromptTemplate and Messages", "MessagesPlaceholder and Chat History"], ["Lab: A prompt-templated assistant"]),
   ("Structured Output and Output Parsers", ["Why Structured Output Matters", "Structured Output with TypedDict", "Structured Output with Pydantic and JSON Schema", "StrOutputParser", "JsonOutputParser and StructuredOutputParser", "PydanticOutputParser"], ["Lab: Extract structured data from reviews"]),
   ("Chains and Runnables", ["Chains, LCEL and Runnables", "Sequential, Parallel and Conditional Chains", "Why Runnables Exist", "RunnableSequence, Parallel, Passthrough, Lambda and Branch", "Synthetic Data Generation", "Memory Management"], ["Lab: Multi-step LCEL pipeline"]),
   ("Tools and Tool Calling", ["Tools and Toolkits", "Built-in Tools", "Custom Tools: @tool, StructuredTool and BaseTool", "Tool Calling with bind_tools", "Injected Tool Arguments"], ["Lab: Currency converter with tool calling"]),
   ("Agents, Monitoring and Deployment", ["LangChain Agents", "ReAct Agents with AgentExecutor", "LangSmith Monitoring", "LangServe Deployment"], ["Lab: Deploy a chain with LangServe"])]),
 ("Retrieval-Augmented Generation (RAG)", "Intermediate", [23],
  "Ground LLMs in your own data: loaders, splitters, vector stores, retrievers, the RAG pipeline, hybrid search, reranking and multimodal RAG.",
  [("Introduction to RAG", ["What is RAG?", "RAG vs Fine-Tuning vs Prompting", "The RAG Pipeline End to End"], [ADD + "Lab: RAG from scratch, no framework"]),
   ("RAG Building Blocks in LangChain", ["Document Loaders", "PDF, Web, CSV and Directory Loaders", "load() vs lazy_load()", "Text Splitters", "Vector Stores in LangChain", "Retrievers", "MMR, Multi-Query and Contextual Compression Retrievers"], []),
   ("Implementing RAG", ["RAG with LangChain and a Vector DB", ADD + "Chunking Strategies", "Retrieval Methods", "Hybrid Search", "Reranking"], ["Lab: Chat with a PDF", "Project: Chat with Any YouTube Video"]),
   ("Advanced RAG", ["Memory in RAG Systems", "Multimodal RAG"], ["Lab: RAG over images and text"])]),
 ("Enterprise LLM Systems", "Advanced", [24],
  "Run LLM systems at scale: RAG evaluation with Ragas, observability with LangSmith and Opik, vectorless RAG and LLM gateways.",
  [("RAG Evaluation", ["The RAG Triad Metrics", "LLM-as-a-Judge", "Turn-Based Evaluation with Ragas"], ["Lab: Evaluate your RAG app with Ragas"]),
   ("Observability", ["Traces and Spans", "LangSmith Setup and Zero-Code Tracing", "Intermediate Outputs and Analytics", "Feedback and Annotation Loops", "Prompt Optimisation Pipelines", "Low-Code Agent Tracing"], ["Lab: Trace an app in LangSmith and Opik"]),
   ("Vectorless RAG", ["Limits of Vector RAG", "PageIndex and Chunk-Free Segmentation", "The Document Tree Model", "The Iterative Search Loop", "Deterministic Page Referencing"], []),
   ("LLM Gateways", ["What is an LLM Gateway?", "OpenAI-Compatible Routing with Bifrost", "Drop-In SDK Replacement", "Automated Structured Fallbacks"], ["Lab: Add a gateway with automatic fallback"]),
   (ADD + "Guardrails and Security", [ADD + "Prompt Injection Explained", ADD + "Input and Output Guardrails"], [ADD + "Lab: Attack and defend your own app"])]),
]),
("Track 7 · Agentic AI", [
 ("Agentic AI Fundamentals", "Beginner", [25],
  "What AI agents are, how the agent loop works, and how to build one from scratch before touching a framework.",
  [("Understanding Agents", ["What is an AI Agent?", "Agentic AI vs Traditional AI Agents", "Agentic AI vs Generative AI", "Agentic AI Use Cases"], []),
   (ADD + "The Agent Loop", [ADD + "The Agent Loop: Decide, Act, Observe", ADD + "Workflows vs Agents", ADD + "Anatomy of an Agent"], [ADD + "Lab: Agent loop with a pretend model"]),
   (ADD + "Tools and Function Calling", [ADD + "What is a Tool?", ADD + "Function Calling Step by Step", ADD + "Designing Good Tools"], [ADD + "Lab: Tool-using agent from scratch"]),
   (ADD + "Reasoning Patterns", [ADD + "ReAct", ADD + "Planning and Reflection"], []),
   ("Multi-Agent Systems and the Ecosystem", ["What are Multi-Agent Systems?", "Overview of Agentic Frameworks", "Trends in Multi-Agent AI"], [])]),
 ("LangGraph Fundamentals", "Intermediate", [26],
  "Build agent workflows as graphs: core concepts, sequential, parallel, conditional and looping workflows, chatbots, persistence, tools and subgraphs.",
  [("Getting Started", ["LangChain vs LangGraph: Why LangGraph Exists", "What is LangGraph?", "Graphs, Nodes, Edges and State", "The LangGraph Execution Model", "Simple Graphs and Node Connections", "LangGraph Studio"], ["Lab: Your first graph"]),
   ("Workflow Patterns in LangGraph", ["Sequential Workflows and Prompt Chaining", "Parallel Workflows", "Conditional Workflows", "Iterative (Looping) Workflows"], ["Lab: Essay evaluator with parallel graders", "Lab: Post generator with an evaluator loop"]),
   ("Workflows and Agents", ["Chains in LangGraph", "Routers", "Building Agents", "Agents with Memory", "Tools in LangGraph: ToolNode and tools_condition", "Using MCP Tools in LangGraph", "RAG Inside a LangGraph Agent"], ["Lab: Rebuild your scratch agent in LangGraph"]),
   ("Chatbots and Persistence", ["Building a Chatbot with LangGraph", "Persistence and Checkpointers", "Threads, Fault Tolerance and Resuming", "Persistent Storage with SQLite"], ["Lab: Chatbot UI with Streamlit, streaming and saved chats"]),
   ("Subgraphs", ["What are Subgraphs?", "Shared vs Different State in Subgraphs"], ["Lab: Translation workflow with a subgraph"]),
   ("Deployment and Observability", ["Deploying and Running LangGraph Apps", "LangSmith Observability for LangGraph"], [])]),
 ("LangGraph State and Memory", "Intermediate", [27],
  "Master LangGraph's state system: schemas, reducers, multiple schemas, and trimming messages to save context.",
  [("State Fundamentals", ["The LangGraph State System", "State Schemas and Data Flow"], []),
   ("Advanced State", ["State Reducers", "Multiple Schemas"], ["Lab: A multi-schema agent"]),
   ("Optimising Memory", ["Trimming and Filtering Messages", ADD + "Summarising Long Conversations", "Long-Term Memory with Stores"], ["Lab: Keep a long chat under budget"])]),
 ("Human-in-the-Loop with LangGraph", "Intermediate", [28],
  "Make agents interactive and controllable: streaming, interrupts, breakpoints, human edits to state and time travel.",
  [("Interactive Workflows", ["Streaming Real-Time Updates", "Breakpoints"], []),
   ("Human Feedback", ["Pausing with interrupt and Resuming with Command", "Editing State with Human Input", "Dynamic Breakpoints"], ["Lab: Approval step before a risky tool"]),
   ("Debugging", ["Time Travel: Rewind and Replay"], ["Lab: Debug an agent with time travel"])]),
 ("Agentic RAG Systems", "Advanced", [29],
  "Let agents decide how to retrieve: Adaptive RAG, Corrective RAG and Self-RAG, locally and with vector DBs.",
  [("Adaptive RAG", ["What is Adaptive RAG?", "Adaptive RAG with Cohere", "Running Adaptive RAG Locally"], ["Lab: Adaptive RAG end to end"]),
   ("Agentic RAG Architectures", ["Agents in RAG Pipelines", "Corrective RAG (CRAG)"], []),
   ("Self-RAG", ["How Self-RAG Works", "Self-RAG with a Vector DB", "Deploying Self-RAG Locally"], ["Lab: Build Self-RAG"])]),
 ("Model Context Protocol (MCP)", "Intermediate", [30],
  "The standard way to plug tools and data into AI apps: why MCP exists, its architecture and lifecycle, and building local and remote servers and clients.",
  [("Understanding MCP", ["Why MCP Exists: The Fragmentation Problem", "What is MCP?", "Hosts, Clients and Servers", "MCP Primitives: Tools, Resources and Prompts"], []),
   ("How MCP Components Talk", ["Data Flow in MCP", "The Data Layer: JSON-RPC Messages", "The Transport Layer: stdio and Streamable HTTP", "Using MCP in Claude Desktop and Cursor"], []),
   ("The MCP Lifecycle", ["Initialisation: Version and Capability Negotiation", "Operation and Shutdown"], []),
   ("Building with MCP", ["Open MCP Registries (Smithery)", "Building a Local MCP Server with FastMCP", "Building and Deploying a Remote MCP Server", "Building an MCP Client", "Building MCP Servers with LangChain", "Docker MCP Catalog and Toolkit", ADD + "Agent-to-Agent (A2A) Protocol"], ["Lab: Build and connect your own MCP server", "Lab: Expense tracker MCP server"])]),
 ("Multi-Agent Research System (Capstone)", "Advanced", [31],
  "Build and ship a multi-agent system that researches, analyses and writes reports, with CI/CD on AWS.",
  [("Architecting Multi-Agent Systems", ["Introduction to Agentic AI and Multi-Agent Architectures", "Designing Specialised Agents: Search, Reader, Analyst, Generator, Coordinator"], []),
   ("Collaboration and Control", ["Shared Memory and Communication State", "Prompting for Multi-Turn Collaboration", "Human Feedback Checkpoints"], []),
   ("Tools and Workflow", ["Connecting arXiv, Search and Paper Parsers", "LangGraph Agent Workflows", "Adding RAG for External Knowledge"], ["Lab: Build the research team"]),
   ("Deployment and Automation", ["FastAPI Backend for Agents", "UI for Logs, Graphs and Reports", "CI/CD with GitHub Actions", "Docker and AWS EC2 Deployment"], ["Lab: Ship it to AWS"])]),
]),
("Track 8 · Projects", [
 ("End-to-End AI Projects", "Advanced", ["Projects"],
  "Portfolio projects across data engineering, ML, deep learning, GenAI and agentic AI, each deployed with CI/CD.",
  [("Python and Data Engineering", [], ["Project: Review Scraper End to End", "Project: Supabase and Streamlit Database App"]),
   ("Machine Learning", [], ["Project: Network Intrusion Detection System", "Project: Insurance Premium Predictor API"]),
   ("Deep Learning", [], ["Project: Text Summarisation", "Project: Machine Translation", "Project: Question Answering"]),
   ("Generative AI and RAG", [], ["Project: RAG Q&A System with CI/CD"]),
   ("Agentic AI", [], ["Project: AI Newsletter Generator with MCP", "Project: Multi-Agent Research Analysis and Generation"])]),
]),
]


def clean(s):
    return s.replace(ADD, "")

catalog = []
n = 0
for track, courses in TRACKS:
    for title, level, mods, card, modules in courses:
        n += 1
        out_modules = [{"title": "Start Here", "lessons": [{"title": "How This Course Works", "type": "Article", "added": False}]}]
        for mtitle, topics, labs in modules:
            lessons = []
            for t in topics:
                added = t.startswith(ADD)
                lessons.append({"title": clean(t), "type": "Article", "added": added})
            for l in labs:
                lessons.append({"title": clean(l), "type": "Lab", "added": l.startswith(ADD)})
            out_modules.append({"title": clean(mtitle), "added": mtitle.startswith(ADD), "lessons": lessons})
        nl = sum(len(m["lessons"]) for m in out_modules)
        hrs = round(sum(HOURS[l["type"]] for m in out_modules for l in m["lessons"]))
        catalog.append({"id": n, "slug": slug(title), "track": track, "title": title, "level": level,
                        "syllabus_modules": mods, "description": card, "modules": out_modules,
                        "module_count": len(out_modules), "lesson_count": nl, "hours": max(hrs, 1)})

# ---------------------------------------------------------------------------
# Prerequisites. Course-level: what to finish first. Module-level: the exact
# earlier modules a module builds on. Both must point backwards in the catalog.
# ---------------------------------------------------------------------------
PY, ADVPY, NUM, VIZ, DB, ST = ("Python Fundamentals", "Advanced Python Programming", "Numerical Computing and Data Analysis",
    "Data Visualization with Matplotlib and Seaborn", "Databases: SQL and NoSQL", "Interactive Data Apps with Streamlit")
STATS, INF = "Statistics Foundations", "Inferential Statistics"
FE, ML, ENS, MLF = "Feature Engineering and EDA", "Machine Learning Fundamentals", "Ensembles and Unsupervised Learning", "MLOps with MLflow"
API, SPARK = "Production APIs with FastAPI", "Big Data with PySpark"
NLP, DL, SEQ = "NLP for Machine Learning", "Deep Learning Foundations", "Sequence Models, Attention and Transformers"
TORCH = "Deep Learning with PyTorch"
GEN, VDB, LC, RAG, ENT = ("Generative AI and LLM Foundations", "Vector Databases for AI", "LangChain Complete Guide",
    "Retrieval-Augmented Generation (RAG)", "Enterprise LLM Systems")
AG, LG, LGS, HITL, ARAG, MCP, CAP = ("Agentic AI Fundamentals", "LangGraph Fundamentals", "LangGraph State and Memory",
    "Human-in-the-Loop with LangGraph", "Agentic RAG Systems", "Model Context Protocol (MCP)", "Multi-Agent Research System (Capstone)")
PROJ = "End-to-End AI Projects"

PREREQ_COURSES = {
    ADVPY: [PY], NUM: [PY], VIZ: [NUM], DB: [PY], ST: [PY, NUM],
    STATS: [NUM], INF: [STATS],
    FE: [NUM, VIZ, STATS], ML: [FE, STATS], ENS: [ML], MLF: [ML],
    API: [ADVPY], SPARK: [NUM, DB],
    NLP: [ML], DL: [ML], TORCH: [DL], SEQ: [DL, NLP],
    GEN: [SEQ, ADVPY], VDB: [GEN, DB], LC: [GEN], RAG: [VDB, LC], ENT: [RAG],
    AG: [GEN], LG: [AG, LC], LGS: [LG], HITL: [LGS], ARAG: [RAG, LG], MCP: [AG, LC],
    CAP: [HITL, ARAG, MCP, API, ENT],
}

PREREQ_MODULES = {
    (ADVPY, "Concurrency for AI Apps"): [(PY, "Functions and Iterators")],
    (NUM, "NumPy Essentials"): [(PY, "Strings and Data Structures")],
    (DB, "PostgreSQL on Supabase"): [(PY, "Functions and Iterators")],
    (ST, "State and Responsiveness"): [(ADVPY, "Concurrency for AI Apps")],
    (STATS, "Data Behaviour and Relationships"): [(NUM, "NumPy Essentials")],
    (STATS, "Estimation"): [(STATS, "Distributions")],
    (INF, "Hypothesis Testing"): [(STATS, "Distributions"), (STATS, "Estimation")],
    (INF, "Bayesian Thinking"): [(STATS, "Probability")],
    (FE, "Feature Transformation and Selection"): [(STATS, "Data Behaviour and Relationships")],
    (FE, "Exploratory Data Analysis"): [(VIZ, "Seaborn and Storytelling"), (NUM, "Statistics and Plots in pandas")],
    (ML, "Regression"): [(STATS, "Central Tendency and Dispersion"), (FE, "Feature Scaling and Encoding")],
    (ML, "Gradient Descent and Regularisation"): [(ML, "Regression")],
    (FE, "Dimensionality Reduction"): [(NUM, "NumPy Essentials")],
    (ML, "Classification"): [(STATS, "Probability")],
    (ML, "More Supervised Algorithms"): [(INF, "Bayesian Thinking")],
    (ENS, "Ensemble Learning"): [(ML, "More Supervised Algorithms")],
    (ENS, "Unsupervised Learning"): [(FE, "Feature Transformation and Selection")],
    (MLF, "Experiment Tracking"): [(ML, "Regression")],
    (API, "Validation and Schemas"): [(ADVPY, "Object-Oriented Programming")],
    (API, "Production Considerations"): [(ADVPY, "Modules and Exceptions")],
    (SPARK, "PySpark DataFrames and SQL"): [(NUM, "pandas Core"), (DB, "Relational Databases and SQL")],
    (NLP, "Text Representation"): [(FE, "Feature Transformation and Selection")],
    (NLP, "Word Embeddings"): [(NUM, "NumPy Essentials"), (STATS, "Data Behaviour and Relationships")],
    (DL, "Neural Networks"): [(ML, "Regression"), (ML, "Classification")],
    (TORCH, "PyTorch Basics"): [(DL, "Frameworks")],
    (SEQ, "Sequence Models"): [(DL, "Neural Networks"), (NLP, "Word Embeddings")],
    (GEN, "How LLMs Work"): [(SEQ, "Transformers")],
    (GEN, "Prompting and Structured Output"): [(API, "Validation and Schemas")],
    (VDB, "Introduction to Vector Databases"): [(NLP, "Word Embeddings"), (DB, "Relational Databases and SQL")],
    (VDB, "Integrations"): [(DB, "NoSQL with MongoDB Atlas")],
    (LC, "Structured Output and Output Parsers"): [(GEN, "Prompting and Structured Output"), (API, "Validation and Schemas")],
    (LC, "Agents, Monitoring and Deployment"): [(API, "APIs and FastAPI Fundamentals")],
    (RAG, "Introduction to RAG"): [(VDB, "Introduction to Vector Databases"), (GEN, "How LLMs Work")],
    (RAG, "Implementing RAG"): [(LC, "Chains and Runnables"), (VDB, "Tools")],
    (RAG, "Advanced RAG"): [(LC, "Chains and Runnables")],
    (ENT, "RAG Evaluation"): [(RAG, "Implementing RAG")],
    (ENT, "Observability"): [(LC, "Agents, Monitoring and Deployment")],
    (ENT, "Vectorless RAG"): [(RAG, "Implementing RAG")],
    (ENT, "LLM Gateways"): [(API, "Production Considerations")],
    (ENT, "Guardrails and Security"): [(LC, "Agents, Monitoring and Deployment")],
    (AG, "Understanding Agents"): [(GEN, "How LLMs Work")],
    (AG, "Tools and Function Calling"): [(GEN, "Prompting and Structured Output")],
    (AG, "Multi-Agent Systems and the Ecosystem"): [(LC, "Agents, Monitoring and Deployment")],
    (LG, "Getting Started"): [(AG, "The Agent Loop"), (LC, "Chains and Runnables")],
    (LG, "Chatbots and Persistence"): [(ST, "Streamlit Basics")],
    (LG, "Workflows and Agents"): [(AG, "Tools and Function Calling")],
    (LGS, "State Fundamentals"): [(LG, "Workflows and Agents")],
    (LGS, "Optimising Memory"): [(GEN, "How LLMs Work")],
    (HITL, "Interactive Workflows"): [(LGS, "State Fundamentals")],
    (HITL, "Human Feedback"): [(ENT, "Guardrails and Security")],
    (ARAG, "Adaptive RAG"): [(RAG, "Implementing RAG"), (LG, "Workflows and Agents")],
    (ARAG, "Agentic RAG Architectures"): [(AG, "Reasoning Patterns")],
    (ARAG, "Self-RAG"): [(VDB, "Tools"), (ENT, "RAG Evaluation")],
    (MCP, "Understanding MCP"): [(AG, "Tools and Function Calling")],
    (MCP, "Building with MCP"): [(LC, "Tools and Tool Calling"), (API, "Docker and Cloud Deployment")],
    (CAP, "Architecting Multi-Agent Systems"): [(AG, "Multi-Agent Systems and the Ecosystem")],
    (CAP, "Collaboration and Control"): [(LGS, "Advanced State"), (HITL, "Human Feedback")],
    (CAP, "Tools and Workflow"): [(MCP, "Building with MCP"), (ARAG, "Agentic RAG Architectures")],
    (CAP, "Deployment and Automation"): [(API, "Production Considerations"), (ST, "Streamlit Basics"), (MLF, "Serving and Deployment")],
    (PROJ, "Python and Data Engineering"): [(DB, "PostgreSQL on Supabase"), (ST, "State and Responsiveness")],
    (PROJ, "Machine Learning"): [(ENS, "Boosting"), (MLF, "Serving and Deployment")],
    (PROJ, "Deep Learning"): [(SEQ, "Transformers")],
    (PROJ, "Generative AI and RAG"): [(RAG, "Advanced RAG"), (ENT, "RAG Evaluation")],
    (PROJ, "Agentic AI"): [(CAP, "Deployment and Automation")],
}

by_title = {c["title"]: c for c in catalog}
def mod_index(course, module):
    titles = [m["title"] for m in by_title[course]["modules"]]
    assert module in titles, f"unknown module {course} / {module}"
    return titles.index(module) + 1

errors = []
for c, reqs in PREREQ_COURSES.items():
    for r in reqs:
        if by_title[r]["id"] >= by_title[c]["id"]: errors.append(f"course {c} requires later {r}")
    by_title[c]["prerequisites"] = [{"course": r, "slug": by_title[r]["slug"]} for r in reqs]
for (c, m), reqs in PREREQ_MODULES.items():
    i = mod_index(c, m)
    out = []
    for rc, rm in reqs:
        j = mod_index(rc, rm)
        if (by_title[rc]["id"], j) >= (by_title[c]["id"], i): errors.append(f"{c}/{m} requires later {rc}/{rm}")
        out.append({"course": rc, "slug": by_title[rc]["slug"], "module": rm, "anchor": f"m{j}"})
    by_title[c]["modules"][i - 1]["prerequisites"] = out
assert not errors, "\n".join(errors)

# ---------------------------------------------------------------------------
# Syllabus coverage: every syllabus topic must map to lessons that exist.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from syllabus_coverage import COVERAGE
where = {}
for c in catalog:
    for i, m in enumerate(c["modules"], 1):
        for l in m["lessons"]:
            where.setdefault(l["title"], (c, i, m["title"]))
missing = [(mod, t, l) for mod, rows in COVERAGE.items() for t, ls in rows for l in ls if l not in where]
assert not missing, "\n".join(map(str, missing))
from reference_coverage import REFERENCES
missing = [(ref, t, l) for ref, rows in REFERENCES.items() for t, ls in rows for l in ls if l not in where]
assert not missing, "reference topics without a lesson:\n" + "\n".join(map(str, missing))

os.makedirs(OUT, exist_ok=True)
json.dump(catalog, open(os.path.join(OUT, "catalog.json"), "w"), indent=1, ensure_ascii=False)

def course_link(c, prefix=""):
    return f"[{c['title']}]({prefix}courses/{c['slug']}/course.md)"

# Overview
L = ["# Agentic AI Platform: Course Catalog (Draft v4)", "",
     "> Built from the *Ultimate Data Science & GenAI Bootcamp V3.0* syllabus Sourabh shared, laid out like the DataVidhya Learn section.",
     "> Every topic in the syllabus is mapped to a lesson; see [syllabus-coverage.md](syllabus-coverage.md). Topics marked ➕ are additions beyond the syllabus.",
     "> The platform is text only: every topic is one in-depth **Article**, with **Labs** where the reader builds something. Hours are estimates (article 25 min, lab 45 min).",
     "> Each course lists the courses to finish first, and each module links to the exact earlier modules it builds on.",
     ""]
tot_l = sum(c["lesson_count"] for c in catalog); tot_h = sum(c["hours"] for c in catalog)
L += [f"**{len(catalog)} courses · {sum(c['module_count'] for c in catalog)} modules · {tot_l} lessons · ~{tot_h} hours**", ""]
for track, _ in TRACKS:
    L += [f"## {track}", "", "| # | Course | Level | Syllabus modules | Modules | Lessons | Est. hrs | Finish first |", "|---|---|---|---|---|---|---|---|"]
    for c in catalog:
        if c["track"] == track:
            pre = ", ".join(course_link(by_title[p["course"]]) for p in c.get("prerequisites", [])) or "Nothing, start here"
            L.append(f"| {c['id']} | {course_link(c)} | {c['level']} | {', '.join(map(str, c['syllabus_modules']))} | {c['module_count']} | {c['lesson_count']} | {c['hours']} | {pre} |")
    L.append("")
    for c in catalog:
        if c["track"] == track:
            L.append(f"- **{c['title']}:** {c['description']}")
    L.append("")
L += ["## Article template (every article follows this)", "",
      "1. **Title:** \"Topic? The Complete Guide\"",
      "2. **Before you start:** links to the earlier lessons this one builds on (from the module's prerequisites).",
      "3. **Introduction:** a real-world hook, why the topic is misunderstood, what the reader will know by the end.",
      "4. **Key Insight** callout: the one sentence to remember.",
      "5. **Core Explanation:** H3 subsections, each with an everyday analogy, a hand-drawn style diagram and bold-lead bullets. Any term taught elsewhere links to its lesson.",
      "6. **Try It Yourself:** an interactive playground embedded in the page (spec included in each article).",
      "7. **Topic-specific section** (patterns, skills, when to use what).",
      "8. **Real-World Examples:** two or three named, concrete stories.",
      "9. **Common Misconceptions:** numbered, each corrected.",
      "10. **Interview Relevance:** what interviewers ask and what a strong answer covers.",
      "11. **Key Takeaways:** five to seven bullets, then **Up next**.", ""]
open(os.path.join(OUT, "curriculum-outline.md"), "w").write("\n".join(L))

# Coverage report
C = ["# Syllabus Coverage Check", "",
     "Every topic line from the *Ultimate Data Science & GenAI Bootcamp V3.0* syllabus, and the lesson(s) that teach it. "
     "The build script fails if any of these lessons is missing, so this list stays true.", ""]
total = 0
for mod, rows in COVERAGE.items():
    C += [f"## Syllabus module {mod}", "", "| Syllabus topic | Taught in |", "|---|---|"]
    for t, ls in rows:
        total += 1
        cells = []
        for l in ls:
            c, i, mt = where[l]
            cells.append(f"[{l}](courses/{c['slug']}/course.md#m{i}) ({c['title']} › {mt})")
        C.append(f"| {t} | {'<br>'.join(cells)} |")
    C.append("")
C.insert(3, f"\n**{total} syllabus topics checked, {total} covered, 0 missing.**\n")
open(os.path.join(OUT, "syllabus-coverage.md"), "w").write("\n".join(C))

R = ["# Reference Notes Coverage", "",
     "Topics from the reference course notes shared for this site (CampusX 100 Days of ML, NLP, PyTorch, FastAPI, "
     "LangChain, LangGraph and MCP), and the lesson(s) that teach each one. The build fails if a lesson is missing.", ""]
for ref, rows in REFERENCES.items():
    R += [f"## {ref}", "", "| Topic | Taught in |", "|---|---|"]
    for t, ls in rows:
        R.append(f"| {t} | " + "<br>".join(f"[{l}](courses/{where[l][0]['slug']}/course.md#m{where[l][1]}) ({where[l][0]['title']})" for l in ls) + " |")
    R.append("")
open(os.path.join(OUT, "reference-coverage.md"), "w").write("\n".join(R))

# Written lessons live at courses/<course>/<NN-module>/<lesson-slug>.md
written = {}
for c in catalog:
    base = os.path.join(OUT, "courses", c["slug"])
    for dp, _, files in os.walk(base):
        for f in files:
            if f.endswith(".md") and f != "course.md":
                written[(c["slug"], f[:-3])] = os.path.relpath(os.path.join(dp, f), base)
lesson_slugs = {(c["slug"], slug(l["title"])) for c in catalog for m in c["modules"] for l in m["lessons"]}
orphans = sorted(set(written) - lesson_slugs)
assert not orphans, f"written lessons not in the catalog: {orphans}"

# Every relative .md link in a written lesson must point at a file that exists (a written lesson or a
# course page). Forward references to lessons not written yet should link to course.md#m<N> instead.
broken = []
for (cs, _), rel in written.items():
    src = os.path.join(OUT, "courses", cs, rel)
    for target in re.findall(r"\]\(([^)#\s:]+\.md)(?:#[^)\s]*)?\)", open(src).read()):
        full = os.path.normpath(os.path.join(os.path.dirname(src), target))
        generated = os.path.basename(full) == "course.md" and os.path.basename(os.path.dirname(full)) in {c["slug"] for c in catalog}
        if not (generated or os.path.exists(full)):
            broken.append(f"{cs}/{rel} -> {target}")
assert not broken, "broken links:\n" + "\n".join(broken)

# Mermaid reads a node label that starts like "1. Text" as a Markdown list and draws
# "Unsupported markdown: list" instead of the label.
bad_labels = []
for (cs, _), rel in written.items():
    text = open(os.path.join(OUT, "courses", cs, rel)).read()
    for block in re.findall(r"```mermaid\n(.*?)```", text, re.S):
        bad_labels += [f"{cs}/{rel}: {m}" for m in re.findall(r'["\[(]\s*\d+\.\s', block)]
assert not bad_labels, "mermaid labels that render as lists:\n" + "\n".join(bad_labels)

# Per-course pages
for c in catalog:
    d = os.path.join(OUT, "courses", c["slug"]); os.makedirs(d, exist_ok=True)
    pre = ", ".join(f"[{p['course']}](../{p['slug']}/course.md)" for p in c.get("prerequisites", [])) or "Nothing, this is a starting point."
    nxt = [x for x in catalog if any(p["course"] == c["title"] for p in x.get("prerequisites", []))]
    P = [f"# {c['title']}", "", f"**{c['level']} · {c['module_count']} modules · {c['lesson_count']} lessons · ~{c['hours']} hrs**  ",
         f"{c['track']} · Bootcamp syllabus module(s): {', '.join(map(str, c['syllabus_modules']))}", "", c["description"], "",
         f"**Finish first:** {pre}  ",
         f"**Unlocks:** {', '.join(f'[{x['title']}](../{x['slug']}/course.md)' for x in nxt) or 'Nothing, this is a final course.'}", "",
         "## Course content", ""]
    for i, m in enumerate(c["modules"], 1):
        P.append(f'<a id="m{i}"></a>')
        P.append(f"### {i}. {m['title']}{' ➕' if m.get('added') else ''} ({len(m['lessons'])} lesson{'s' if len(m['lessons']) != 1 else ''})")
        if m.get("prerequisites"):
            links = []
            for p in m["prerequisites"]:
                href = f"#{p['anchor']}" if p["course"] == c["title"] else f"../{p['slug']}/course.md#{p['anchor']}"
                label = p["module"] if p["course"] == c["title"] else f"{p['course']} › {p['module']}"
                links.append(f"[{label}]({href})")
            P.append(f"> **Before you start:** {', '.join(links)}")
            P.append("")
        for l in m["lessons"]:
            mark = " ➕" if l["added"] else ""
            rel = written.get((c["slug"], slug(l["title"])))
            if rel:
                P.append(f"- [{l['title']}]({rel}) · {l['type']}{mark} ✍️ *written*")
            else:
                P.append(f"- {l['title']} · {l['type']}{mark}")
        P.append("")
    open(os.path.join(d, "course.md"), "w").write("\n".join(P))

print(len(catalog), "courses", tot_l, "lessons", tot_h, "hours;", total, "syllabus topics covered;",
      len(PREREQ_MODULES), "module prerequisite links")
