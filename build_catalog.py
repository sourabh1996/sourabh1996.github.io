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
('Programming Foundations', [
 (ADD + 'The Command Line and Linux Basics', 'Beginner', [],
  'Get comfortable in a terminal: files, paths, permissions, processes, pipes, environment variables and shell scripts.',
  [(ADD + 'Terminal Fundamentals', [ADD + 'What is a Terminal and a Shell?', ADD + 'Files, Folders and Paths', ADD + 'Viewing, Searching and Editing Files', ADD + 'Permissions and Users'], []),
   (ADD + 'Working Like a Developer', [ADD + 'Pipes, Redirection and grep', ADD + 'Processes, Ports and Environment Variables', ADD + 'Package Managers and Virtual Environments', ADD + 'Shell Scripts and cron', ADD + 'SSH and Remote Servers'], [ADD + 'Lab: Automate a daily data download'])]),
 ('Python Programming', 'Beginner', [1, 2],
  'Learn Python from zero to confident: values, control flow, collections, functions, classes, files, modules, errors and async code.',
  [('Getting Started with Python', ['What is Python and Why Use It?', 'Python vs Other Languages', 'Numbers, Booleans and Strings', 'Setting Up Your ML Environment: Anaconda, Jupyter and Colab'], ['Lab: Set up Python and run your first script']),
   ('Core Language Concepts', ['Containers and Mutability', 'Operators and Precedence'], ['Lab: Build a unit converter']),
   ('Control Flow', ['if, elif and else', 'for and while Loops', 'break, continue and range()'], ['Lab: Number guessing game']),
   ('Strings and Data Structures', ['Working with Strings', 'Lists and Tuples', 'Sets', 'Dictionaries and Dictionary Views', 'List and Dictionary Comprehensions'], ['Lab: Word frequency counter']),
   ('Functions and Iterators', ['Functions and Parameter Passing', 'Iterators and Generators', 'Lambda, map and Functional Style'], ['Lab: Build a tiny text-processing toolkit']),
   ('Object-Oriented Programming', ['Classes and Objects', 'Inheritance and Polymorphism', 'Encapsulation and Abstraction', 'Decorators, classmethod and staticmethod', 'Dunder Methods'], ['Lab: Model a library system with classes']),
   ('File Handling', ['Reading and Writing Files', 'Buffered I/O and Other File Methods'], ['Lab: Log file analyser']),
   ('Modules and Exceptions', ['Importing and Managing Modules', 'try/except and Custom Exceptions', 'Error Handling Best Practices'], []),
   (ADD + 'Concurrency for AI Apps', [ADD + 'Threads, Processes and Async', ADD + 'async and await for API Calls'], [ADD + 'Lab: Call 10 APIs concurrently'])]),
 (ADD + 'Git and GitHub: Zero to Pro', 'Beginner', [],
  'Everything about Git and GitHub: how Git works inside, branching, collaboration, Actions, Pages, Codespaces, Copilot and coding agents, security and open source.',
  [(ADD + 'Version Control from Scratch', [ADD + 'Why Version Control Exists', ADD + 'Installing and Configuring Git', ADD + 'The Three Areas: Working Tree, Staging and Repository', ADD + 'Reading History with log, show and diff', ADD + 'Writing Good Commit Messages', ADD + '.gitignore and What Never to Commit'], [ADD + 'Lab: Put a project under version control']),
   (ADD + 'How Git Works Inside', [ADD + 'Blobs, Trees, Commits and Tags', ADD + 'Hashes and Content Addressing', ADD + 'Refs, HEAD and Detached HEAD', ADD + 'The Reflog and Garbage Collection'], [ADD + 'Lab: Explore the .git folder by hand']),
   (ADD + 'Branching and Merging', [ADD + 'Branches Are Just Pointers', ADD + 'Fast-Forward and Three-Way Merges', ADD + 'Resolving Merge Conflicts', ADD + 'Rebase and Interactive Rebase', ADD + 'Merge vs Rebase', ADD + 'Undoing Things: restore, reset, revert and cherry-pick', ADD + 'Stash, Worktrees and bisect'], [ADD + 'Lab: Branching kata with conflicts']),
   (ADD + 'Remotes and GitHub Basics', [ADD + 'clone, fetch, pull and push', ADD + 'SSH Keys, Tokens and the GitHub CLI', ADD + 'Forks, Upstreams and Remotes', ADD + 'A Great README, LICENSE and Profile'], []),
   (ADD + 'Collaborating on GitHub', [ADD + 'Pull Requests End to End', ADD + 'Code Review that Helps', ADD + 'Issues, Labels, Milestones and Projects', ADD + 'GitHub Flow, Git Flow and Trunk-Based Development', ADD + 'Branch Protection, Rulesets and CODEOWNERS', ADD + 'Merge Strategies and Merge Queues'], [ADD + 'Lab: Team workflow with PRs and reviews']),
   (ADD + 'GitHub Actions', [ADD + 'Workflows, Jobs, Steps and Runners', ADD + 'Triggers and Events', ADD + 'Matrix Builds and Caching', ADD + 'Secrets, Variables and Environments', ADD + 'OIDC: Deploying to the Cloud without Stored Keys', ADD + 'Reusable Workflows and Composite Actions', ADD + 'Writing Your Own Action'], [ADD + 'Lab: CI that tests and lints a Python project']),
   (ADD + 'GitHub Pages, Codespaces and Packages', [ADD + 'Publishing a Site with GitHub Pages', ADD + 'Custom Domains and HTTPS', ADD + 'Codespaces and Dev Containers', ADD + 'Releases, Tags and GitHub Packages'], [ADD + 'Lab: Deploy a static site with Actions']),
   (ADD + 'Security and Supply Chain', [ADD + 'Dependabot Alerts and Updates', ADD + 'Code Scanning and Secret Scanning', ADD + 'Signed Commits and Artifact Attestations', ADD + 'Hardening Actions: Pinning and Least Privilege', ADD + 'Removing a Leaked Secret from History'], []),
   (ADD + 'Open Source and Advanced Git', [ADD + 'Contributing to Open Source', ADD + 'Licenses in Plain English', ADD + 'Maintaining a Project: Templates, Releases and Semver', ADD + 'Submodules, Subtrees and Monorepos', ADD + 'Git LFS for Large Files', ADD + 'Git Hooks and pre-commit'], []),
   (ADD + 'Git and GitHub Interview Prep', [ADD + 'Git Interview Questions Explained', ADD + 'Scenario Drills: Broken main, Leaked Secrets, Lost Work'], [])]),
]),
('Working with Data', [
 ('Data Analysis and Visualisation with Python', 'Beginner', [3, 4, 5],
  'Process and picture data: NumPy arrays, pandas DataFrames, text, dates and categories, then clear charts with Matplotlib and Seaborn.',
  [('NumPy Essentials', ['What is a NumPy Array?', 'Creating, Indexing and Slicing Arrays', 'Data Types and Array Attributes', 'Broadcasting and Iterating over Arrays', 'Array Manipulation and Arithmetic', 'Statistical, Sorting, Searching and Counting Functions', 'Binary and String Functions', 'The Matrix Library, Copies and Views'], ['Lab: Image as a NumPy array']),
   ('pandas Core', ['Series, DataFrames (and the Retired Panel)', 'Selecting, Sorting and Indexing Data', 'Reindexing and Iteration'], ['Lab: Explore a sales dataset']),
   ('Text, Dates and Categories in pandas', ['Working with Text Data', 'Dates, Times and Timedeltas', 'Categorical Data'], []),
   ('Statistics and Plots in pandas', ['Descriptive Statistics in pandas', 'Quick Visualisation with pandas'], ['Lab: Clean and summarise a messy CSV']),
   ('Matplotlib', ['How Matplotlib Thinks: Figures and Axes', 'Creating and Customising Plots'], ['Lab: Recreate a published chart']),
   ('Seaborn and Storytelling', ['Statistical Plots with Seaborn', 'Histograms, Pair Plots and Heatmaps', 'Styling Charts for Communication'], ['Lab: Build a one-page visual report'])]),
 ('Databases: SQL and NoSQL', 'Beginner', [6],
  'Store and query data with PostgreSQL on Supabase and documents in MongoDB Atlas.',
  [('Relational Databases and SQL', ['What is a Relational Database?', 'Writing SQL Queries', 'Primary and Foreign Keys', 'Joins and Unions'], []),
   ('PostgreSQL on Supabase', ['Setting Up Supabase', 'Querying Supabase from Python'], ['Lab: Build a Supabase-backed notes database']),
   ('NoSQL with MongoDB Atlas', ['What is a Document Database?', 'Databases and Collections', 'Insert, Find, Query and Sort', 'Update, Delete and Drop'], ['Lab: Store chat history in MongoDB'])]),
 ('Statistics for Data Science', 'Beginner', [8, 9],
  'The ideas behind every model and experiment: averages, spread, probability, distributions, estimation, hypothesis tests, Bayes and chi-square.',
  [('Introduction to Statistics', ['What is Statistics?', 'Descriptive vs Inferential Statistics', 'Types of Data and Levels of Measurement'], []),
   ('Central Tendency and Dispersion', ['Mean, Median and Mode', 'Range, Variance and Standard Deviation'], ['Lab: Summarise a dataset by hand and in code']),
   ('Data Behaviour and Relationships', ['Skewness and Kurtosis', 'Covariance and Correlation', 'Random Variables and Sets'], []),
   ('Probability', ['Probability Basics', 'PDF, PMF and CDF'], []),
   ('Distributions', ['Bernoulli, Binomial and Poisson', 'Normal and Uniform Distributions', 'Real-World Normal Distributions', 'Z-Statistics and the Central Limit Theorem'], ['Lab: Simulate the Central Limit Theorem']),
   ('Estimation', ['Population vs Sample', 'Confidence Intervals'], []),
   ('Hypothesis Testing', ['How Hypothesis Testing Works', 'p-Values and Significance', 'Confidence Levels and Decision Rules'], ['Lab: A/B test a website change']),
   ('Bayesian Thinking', ["Bayes' Theorem", 'Bayes in the Real World'], []),
   ('Chi-Square Tests', ['The Chi-Square Distribution', 'Goodness-of-Fit and Independence Tests'], ['Lab: Chi-square tests in Python'])]),
]),
('Machine Learning', [
 ('Machine Learning Foundations: Data, EDA and Features', 'Intermediate', [12, 10, 11],
  'Start machine learning the right way: what ML is, getting and exploring data, cleaning it, and turning raw columns into good features.',
  [('What is Machine Learning?', ['AI vs ML vs DL vs Data Science', 'Supervised, Unsupervised, Semi-Supervised and Reinforcement Learning', 'Batch vs Online Learning', 'Instance-Based vs Model-Based Learning', 'Challenges in Machine Learning', 'The Machine Learning Development Life Cycle', 'Data Science and ML Job Roles', 'Tensors: How Data Is Represented', 'Train, Validation and Test Splits'], []),
   ('Getting Data', ['Framing a Machine Learning Problem', 'Loading CSV, JSON and SQL Data', 'Fetching Data from APIs', 'Web Scraping for Datasets'], ['Lab: Build a dataset from an API']),
   ('Exploratory Data Analysis', ['What EDA Is and Why It Matters', 'First Questions to Ask Your Data', 'Univariate Analysis', 'Bivariate and Multivariate Analysis', 'Visualising Patterns and Relationships', 'Automated EDA with Profiling Reports'], []),
   ('Data Cleaning', ['Handling Missing Data', 'Complete Case Analysis', 'Mean, Median and Arbitrary Value Imputation', 'Imputing Missing Categories', 'Missing Indicators and Random Sample Imputation', 'KNN Imputer', 'Iterative Imputer (MICE)', 'Imbalanced Datasets', 'Outliers', 'Outliers with Z-Scores, IQR and Winsorisation'], ['Lab: Compare imputation strategies']),
   ('Feature Scaling and Encoding', ['Normalisation vs Standardisation', 'Encoding Categorical Variables', 'One-Hot Encoding', 'ColumnTransformer', 'scikit-learn Pipelines'], ['Lab: One pipeline from raw data to model']),
   ('Feature Transformation and Selection', ['Function and Power Transformers (Log, Box-Cox, Yeo-Johnson)', 'Binning and Binarisation', 'Mixed Variables', 'Date and Time Features', 'Feature Construction and Splitting', 'Forward and Backward Selection', 'Correlation for Feature Selection'], ['Lab: Feature-engineer a housing dataset']),
   ('EDA Case Studies', ['Case Study: Movie Review Sentiment', 'Case Study: Wine Quality', 'Case Study: Stock and Commodity Prices'], ['Lab: Full EDA report on a dataset of your choice'])]),
 ('Supervised Learning', 'Intermediate', [12],
  'The core supervised algorithms, built from scratch and with scikit-learn: regression, gradient descent, classification, trees, SVMs and honest model tuning.',
  [('Regression', ['Simple and Multiple Linear Regression', 'MSE, MAE, RMSE and R²', 'Assumptions of Linear Regression', 'Polynomial Regression', 'The Bias-Variance Tradeoff'], ['Lab: Linear regression from scratch']),
   ('Gradient Descent and Regularisation', ['Gradient Descent', 'Batch, Stochastic and Mini-Batch Gradient Descent', 'Ridge and Lasso Regularisation', 'Elastic Net'], ['Lab: Gradient descent variants side by side']),
   ('Classification', ['The Perceptron Trick', 'Logistic Regression', 'Sigmoid and Log Loss', 'Softmax for Multiclass Problems', 'Confusion Matrix, Precision, Recall and F1', 'ROC Curves and AUC'], ['Lab: Spam classifier']),
   ('More Supervised Algorithms', ['Support Vector Machines and Kernels', 'Naive Bayes', 'K-Nearest Neighbours', 'Decision Trees', 'Entropy, Gini and Information Gain', 'Regression Trees'], ['Lab: Compare five classifiers on one dataset']),
   ('Model Selection and Tuning', ['Data Leakage', 'Cross-Validation', 'Grid Search and Randomized Search', 'Bayesian Optimisation with Optuna'], ['Lab: Tune a model without overfitting the test set'])]),
 ('Ensembles and Unsupervised Learning', 'Intermediate', [13],
  'Boost accuracy with voting, bagging, random forests, boosting and stacking, then find structure without labels: clustering and PCA.',
  [('Ensemble Learning', ['What is Ensemble Learning?', 'Voting Ensembles', 'Bagging vs Boosting', 'Random Forests and Out-of-Bag Evaluation', 'Feature Importance'], []),
   ('Boosting', ['AdaBoost', 'Gradient Boosting', 'XGBoost', 'Stacking and Blending'], ['Lab: Win a mini Kaggle-style challenge with XGBoost']),
   ('Unsupervised Learning', ['What is Clustering?', 'K-Means', 'K-Means from Scratch', 'Hierarchical Clustering', 'DBSCAN'], ['Lab: Customer segmentation']),
   ('Dimensionality Reduction', ['The Curse of Dimensionality', 'PCA: The Intuition', 'PCA: The Maths Step by Step', 'PCA in Practice'], ['Lab: Compress MNIST with PCA'])]),
]),
('Apps, APIs and MLOps', [
 ('APIs and Apps: FastAPI, Streamlit and Docker', 'Intermediate', [14, 7],
  'Turn Python into products: FastAPI endpoints with Pydantic validation, Streamlit front ends, serving ML models, Docker and AWS deployment.',
  [('APIs and FastAPI Fundamentals', ['What is an API?', 'Why Machine Learning Needs APIs', 'What is FastAPI and Why Use It?', 'Sync vs Async in FastAPI', 'Project Structure and Hello World', 'HTTP Methods: GET, POST, PUT, DELETE'], ['Lab: Your first API']),
   ('Endpoints in Depth', ['Path and Query Parameters', 'Request Bodies and POST Endpoints', 'Update and Delete Endpoints'], ['Lab: A complete CRUD API']),
   ('Validation and Schemas', ['Pydantic Models', 'Pydantic Field Validators and Computed Fields', 'Response Models', 'Handling Validation Errors'], []),
   ('Production Considerations', ['Errors and Status Codes', 'Configuration and Environment Variables', 'Dependency Injection and Routers', 'OpenAPI and Swagger Docs', 'Health Checks and API Versioning'], []),
   ('Streamlit Basics', ['What is Streamlit?', 'Widgets and Layout'], ['Lab: Your first dashboard']),
   ('State and Responsiveness', ['Session State', 'async and await in Streamlit'], ['Lab: Build a chat UI shell for an LLM app']),
   ('Serving Machine Learning Models', ['Serving a Trained Model with FastAPI', 'A Streamlit Front End for Your API'], ['Lab: Wrap an ML model in an API']),
   ('Docker and Cloud Deployment', ['Docker Fundamentals', 'Dockerising a FastAPI App', 'Deploying to AWS EC2'], ['Lab: Ship your ML API to AWS'])]),
 ('MLOps with MLflow', 'Advanced', [15],
  'Manage the ML lifecycle: track experiments, register models and serve them in production.',
  [('MLflow Fundamentals', ['What is MLflow?', 'Installing and Setting Up MLflow'], []),
   ('Experiment Tracking', ['Logging Params, Metrics and Artifacts', 'Artifact Management', 'Autologging', 'Analysing and Visualising Runs'], ['Lab: Track 20 experiments']),
   ('Model Management', ['Model Registry', 'Model Packaging', 'Lifecycle Stages and Transitions'], []),
   ('Serving and Deployment', ['Real-Time Serving and Local Deployment', 'Containerisation', 'Cloud and Orchestration'], ['Lab: Serve a registered model'])]),
]),
('Deep Learning and NLP', [
 ('NLP for Machine Learning', 'Intermediate', [16],
  'Turn text into features and predictions: the NLP pipeline, preprocessing, POS tagging, TF-IDF, Word2Vec and text classification.',
  [('Introduction to NLP', ['What is NLP?', 'NLP Terminology and Roadmap', 'The End-to-End NLP Pipeline', 'Data Acquisition for NLP'], []),
   ('Text Preprocessing', ['Tokenisation', 'Stemming, Lemmatisation and Stopwords', 'POS Tagging and Named Entity Recognition', 'Hidden Markov Models and the Viterbi Algorithm'], ['Lab: Preprocess a corpus with NLTK']),
   ('Text Representation', ['Common Terms: Corpus, Vocabulary, Document', 'One-Hot, Bag of Words and N-Grams', 'TF-IDF'], ['Lab: TF-IDF search engine']),
   ('Word Embeddings', ['What are Word Vectors?', 'The Distributional Hypothesis', 'Word2Vec', 'CBOW and Skip-Gram'], ['Lab: Train Word2Vec on your own text']),
   ('Text Classification', ['Text Classification Pipelines', 'Classic ML vs Embeddings for Text Classification', 'Deploying NLP Systems'], ['Project: Quora Duplicate Question Detection'])]),
 ('Deep Learning with PyTorch', 'Intermediate', [18, 'PyTorch'],
  'How neural networks really work, then build them in PyTorch: backpropagation, activations, optimisers, training loops, GPUs, CNNs and transfer learning.',
  [('Introduction to Deep Learning', ['What is Deep Learning?', 'Why Deep Learning Took Off'], []),
   ('Neural Networks', ['The Perceptron', 'Artificial Neural Networks', 'Forward and Backward Propagation', 'The Chain Rule in Backprop'], ['Lab: A neural network from scratch in NumPy']),
   ('Training Challenges', ['Vanishing and Exploding Gradients', 'Activation Functions', 'Loss Functions', 'Optimisers'], []),
   ('Regularisation and Stability', ['Weight Initialisation', 'Dropout', 'Batch Normalisation'], []),
   ('PyTorch Basics', ['Why PyTorch? History, Features and Ecosystem', 'Tensors in PyTorch', 'Tensor Operations', 'Autograd: Automatic Differentiation'], ['Lab: Gradients by hand vs autograd']),
   ('The Training Pipeline', ['A Training Loop from Scratch', 'The torch.nn Module', 'torch.optim and Loss Functions', 'Dataset and DataLoader'], ['Lab: Rebuild the training loop with nn and DataLoader']),
   ('Building and Improving Networks', ['Building an ANN for Fashion-MNIST', 'Training on a GPU', 'Reducing Overfitting: Dropout, Batch Norm and Weight Decay', 'Hyperparameter Tuning with Optuna'], ['Lab: Push Fashion-MNIST accuracy from 83% to 89%']),
   ('CNNs and Transfer Learning', ['Convolutional Neural Networks in PyTorch', 'Transfer Learning'], ['Lab: CNN for Fashion-MNIST', 'Lab: Fine-tune a pretrained model']),
   ('Keras and Other Frameworks', ['Keras Fundamentals', 'PyTorch vs TensorFlow and Other Frameworks', 'Visualising Network Architecture and Training'], ['Lab: Same model in Keras and PyTorch'])]),
 ('Sequence Models, Attention and Transformers', 'Advanced', [19],
  'From RNNs to Transformers: LSTMs, GRUs, attention, self-attention, BERT and GPT.',
  [('Sequence Models', ['Recurrent Neural Networks', 'Sequence Modelling and Context'], []),
   ('Memory-Based Architectures', ['LSTMs', 'GRUs'], ['Lab: Sentiment with an LSTM']),
   ('Sequence Models in PyTorch', ['RNNs in PyTorch', 'LSTMs in PyTorch'], ['Lab: Question answering with an RNN', 'Lab: Next-word prediction with an LSTM']),
   ('Attention', ['What is Attention?', 'Encoder-Decoder Models', 'Self-Attention'], []),
   ('Transformers', ['The Transformer Architecture', 'BERT', 'GPT'], ['Lab: Fine-tune BERT for classification'])]),
]),
('Generative AI', [
 ('Generative AI and LLM Foundations', 'Beginner', [20],
  'What generative AI is, how LLMs work, and how to use them well: foundation models, tokens, prompting and structured output.',
  [('Fundamentals of Generative AI', ['What is Generative AI?', 'How Generative Models Work', 'Generative vs Discriminative Models', 'The GenAI Roadmap: Builder vs User', 'Foundation Models'], []),
   (ADD + 'How LLMs Work', [ADD + 'What is a Large Language Model?', ADD + 'Tokens and Context Windows', ADD + 'Temperature and Model Settings', ADD + 'Where LLMs Fail'], [ADD + 'Lab: Your first LLM API call']),
   (ADD + 'Prompting and Structured Output', [ADD + 'Prompting Fundamentals', ADD + 'System Prompts and Roles', ADD + 'Structured JSON Output'], [ADD + 'Lab: Reliable JSON extraction']),
   ('Advances and Applications', ['Recent Breakthroughs in GenAI', 'GenAI Applications Across Industries', 'The GenAI Project Lifecycle'], [])]),
 ('LangChain Complete Guide', 'Intermediate', [22],
  'Build LLM apps with LangChain: models, prompts, structured output, parsers, chains, runnables, tools, tool calling and agents.',
  [('LangChain Foundations', ['What is LangChain?', 'LangChain Components', 'Data Connectors and API Integrations', 'Setting Up a LangChain Project and API Keys'], []),
   ('Models', ['LLMs vs Chat Models', 'Chat Models', 'Embedding Models', 'Open-Source Models with Hugging Face'], []),
   ('Prompts', ['Static vs Dynamic Prompts', 'Prompt Templates', 'ChatPromptTemplate and Messages', 'MessagesPlaceholder and Chat History'], ['Lab: A prompt-templated assistant']),
   ('Structured Output and Output Parsers', ['Why Structured Output Matters', 'Structured Output with TypedDict', 'Structured Output with Pydantic and JSON Schema', 'StrOutputParser', 'JsonOutputParser and StructuredOutputParser', 'PydanticOutputParser'], ['Lab: Extract structured data from reviews']),
   ('Chains and Runnables', ['Chains, LCEL and Runnables', 'Sequential, Parallel and Conditional Chains', 'Why Runnables Exist', 'RunnableSequence, Parallel, Passthrough, Lambda and Branch', 'Synthetic Data Generation', 'Memory Management'], ['Lab: Multi-step LCEL pipeline']),
   ('Tools and Tool Calling', ['Tools and Toolkits', 'Built-in Tools', 'Custom Tools: @tool, StructuredTool and BaseTool', 'Tool Calling with bind_tools', 'Injected Tool Arguments'], ['Lab: Currency converter with tool calling']),
   ('Monitoring and Deployment', ['LangSmith Monitoring', 'LangServe Deployment'], ['Lab: Deploy a chain with LangServe'])]),
 ('Retrieval-Augmented Generation (RAG)', 'Intermediate', [23, 21, 24],
  'Ground LLMs in your own data: embeddings and vector databases, loaders, splitters, retrievers, hybrid search, reranking, vectorless and multimodal RAG, and evaluating it all.',
  [('Introduction to RAG', ['What is RAG?', 'RAG vs Fine-Tuning vs Prompting', 'The RAG Pipeline End to End'], [ADD + 'Lab: RAG from scratch, no framework']),
   ('Embeddings and Vector Databases', ['Embeddings and Similarity Search', 'Semantic Search Explained', 'Vector vs SQL vs NoSQL Databases', 'Storage and Indexing (HNSW, IVF)', 'In-Memory, On-Disk and Cloud Vector DBs'], []),
   ('Vector Database Tools', ['Chroma', 'FAISS', 'Qdrant', 'Pinecone', 'LanceDB', 'Vector Search in MongoDB and Cassandra', 'Embedding-Based Retrieval Pipelines'], ['Lab: Same search in three vector DBs', 'Lab: Semantic search over your notes']),
   ('RAG Building Blocks in LangChain', ['Document Loaders', 'PDF, Web, CSV and Directory Loaders', 'load() vs lazy_load()', 'Text Splitters', 'Vector Stores in LangChain', 'Retrievers', 'MMR, Multi-Query and Contextual Compression Retrievers'], []),
   ('Implementing RAG', ['RAG with LangChain and a Vector DB', ADD + 'Chunking Strategies', 'Retrieval Methods', 'Hybrid Search', 'Reranking'], ['Lab: Chat with a PDF', 'Project: Chat with Any YouTube Video']),
   ('Advanced RAG', ['Memory in RAG Systems', 'Multimodal RAG'], ['Lab: RAG over images and text']),
   ('Vectorless RAG', ['Limits of Vector RAG', 'PageIndex and Chunk-Free Segmentation', 'The Document Tree Model', 'The Iterative Search Loop', 'Deterministic Page Referencing'], []),
   ('RAG Evaluation', ['The RAG Triad Metrics', 'LLM-as-a-Judge', 'Turn-Based Evaluation with Ragas'], ['Lab: Evaluate your RAG app with Ragas'])]),
]),
('Agentic AI', [
 ('Agentic AI Fundamentals', 'Beginner', [25],
  'What AI agents are, how the agent loop works, and how to build one from scratch before touching a framework.',
  [('Understanding Agents', ['What is an AI Agent?', 'Agentic AI vs Traditional AI Agents', 'Agentic AI vs Generative AI', 'Agentic AI Use Cases'], []),
   (ADD + 'The Agent Loop', [ADD + 'The Agent Loop: Decide, Act, Observe', ADD + 'How an Agent Decides What to Do Next', ADD + 'Workflows vs Agents', ADD + 'Anatomy of an Agent'], [ADD + 'Lab: Agent loop with a pretend model']),
   (ADD + 'Tools and Function Calling', [ADD + 'What is a Tool?', ADD + 'Function Calling Step by Step', ADD + 'Designing Good Tools'], [ADD + 'Lab: Tool-using agent from scratch']),
   (ADD + 'Reasoning Patterns', [ADD + 'ReAct', ADD + 'Planning and Reflection'], []),
   ('Multi-Agent Systems and the Ecosystem', ['What are Multi-Agent Systems?', 'Overview of Agentic Frameworks', 'Trends in Multi-Agent AI'], [])]),
 ('LangGraph Complete Guide', 'Intermediate', [26, 27, 28],
  'Build agents as graphs, from your first node to production: workflow patterns, state and reducers, tools, persistence, memory, human-in-the-loop, time travel and subgraphs.',
  [('Getting Started', ['LangChain vs LangGraph: Why LangGraph Exists', 'What is LangGraph?', 'Graphs, Nodes, Edges and State', 'The LangGraph Execution Model', 'Simple Graphs and Node Connections', 'LangGraph Studio'], ['Lab: Your first graph']),
   ('Workflow Patterns in LangGraph', ['Sequential Workflows and Prompt Chaining', 'Parallel Workflows', 'Conditional Workflows', 'Iterative (Looping) Workflows'], ['Lab: Essay evaluator with parallel graders', 'Lab: Post generator with an evaluator loop']),
   ('State in Depth', ['The LangGraph State System', 'State Schemas and Data Flow', 'State Reducers', 'Multiple Schemas'], ['Lab: A multi-schema agent']),
   ('Workflows and Agents', ['Chains in LangGraph', 'Routers', 'LangChain Agents', 'ReAct Agents with AgentExecutor', 'Building Agents', 'Agents with Memory', 'Tools in LangGraph: ToolNode and tools_condition', 'Using MCP Tools in LangGraph', 'RAG Inside a LangGraph Agent'], ['Lab: Rebuild your scratch agent in LangGraph']),
   ('Chatbots and Persistence', ['Building a Chatbot with LangGraph', 'Persistence and Checkpointers', 'Threads, Fault Tolerance and Resuming', 'Persistent Storage with SQLite'], ['Lab: Chatbot UI with Streamlit, streaming and saved chats']),
   ('Memory', ['Trimming and Filtering Messages', ADD + 'Summarising Long Conversations', 'Long-Term Memory with Stores'], ['Lab: Keep a long chat under budget']),
   ('Human-in-the-Loop and Debugging', ['Streaming Real-Time Updates', 'Breakpoints', 'Pausing with interrupt and Resuming with Command', 'Editing State with Human Input', 'Dynamic Breakpoints', 'Time Travel: Rewind and Replay'], ['Lab: Approval step before a risky tool', 'Lab: Debug an agent with time travel']),
   ('Subgraphs', ['What are Subgraphs?', 'Shared vs Different State in Subgraphs'], ['Lab: Translation workflow with a subgraph']),
   ('Deployment and Observability', ['Deploying and Running LangGraph Apps', 'LangSmith Observability for LangGraph'], [])]),
 ('Agentic RAG Systems', 'Advanced', [29],
  'Let agents decide how to retrieve: Adaptive RAG, Corrective RAG and Self-RAG, locally and with vector DBs.',
  [('Adaptive RAG', ['What is Adaptive RAG?', 'Adaptive RAG with Cohere', 'Running Adaptive RAG Locally'], ['Lab: Adaptive RAG end to end']),
   ('Agentic RAG Architectures', ['Agents in RAG Pipelines', 'Corrective RAG (CRAG)'], []),
   ('Self-RAG', ['How Self-RAG Works', 'Self-RAG with a Vector DB', 'Deploying Self-RAG Locally'], ['Lab: Build Self-RAG'])]),
 (ADD + 'Knowledge Graphs, Ontologies and Unstructured Data', 'Advanced', [],
  'Model the world as entities and relationships: ontologies with worked examples, Neo4j and Cypher, turning documents into structured data, and knowledge graphs that power agents and GraphRAG.',
  [(ADD + 'Entities and Relationships', [ADD + 'Entities, Relationships and Properties', ADD + 'What is a Knowledge Graph?', ADD + 'Knowledge Graphs vs Relational Databases vs Vector Stores', ADD + 'Where Knowledge Graphs Are Used'], []),
   (ADD + 'Ontologies and Semantics', [ADD + 'What is an Ontology? A Worked Example', ADD + 'Taxonomies, Schemas and Ontologies Compared', ADD + 'RDF, RDFS and OWL in Plain English', ADD + 'Designing an Ontology for Your Domain', ADD + 'Semantic Search, Semantic Layers and Shared Meaning'], [ADD + 'Lab: Design an ontology for an online shop']),
   (ADD + 'Neo4j and Cypher', [ADD + 'Property Graphs and Neo4j', ADD + 'Cypher Basics: MATCH, CREATE and MERGE', ADD + 'Graph Data Modelling', ADD + 'Graph Algorithms: Paths, Centrality and Communities', ADD + 'SPARQL and RDF Triple Stores'], [ADD + 'Lab: Build a company knowledge graph in Neo4j']),
   (ADD + 'Digitising Unstructured Data', [ADD + 'From Documents to Data: OCR and Document Parsing', ADD + 'Extracting Tables, Forms and Layout', ADD + 'Entity and Relation Extraction with LLMs', ADD + 'Schema-Guided Extraction with Pydantic', ADD + 'Entity Resolution and Deduplication'], [ADD + 'Lab: Turn a pile of invoices into structured records']),
   (ADD + 'Knowledge Graphs for AI Agents', [ADD + 'Building a Knowledge Graph from Text with an LLM', ADD + 'GraphRAG', ADD + 'Hybrid Retrieval: Graphs plus Vectors', ADD + 'Text-to-Cypher Agents', ADD + 'Ontology-Grounded Agents'], [ADD + 'Lab: A GraphRAG agent over company documents'])]),
 (ADD + 'Context Engineering and Agent Memory', 'Intermediate', [],
  'Treat the context window as a budget: what to put in it, when to fetch more, how to compact long runs, and how agents remember across sessions.',
  [(ADD + 'The Context Window as a Budget', [ADD + 'From Prompt Engineering to Context Engineering', ADD + 'Context Rot and Lost in the Middle', ADD + 'System Prompts at the Right Altitude', ADD + 'Examples vs Rules', ADD + 'Prompt Caching'], []),
   (ADD + 'Just-in-Time Context', [ADD + 'Retrieval vs Agentic Search', ADD + "Tool Results that Don't Flood the Window", ADD + 'Compaction and Summarisation', ADD + 'Offloading Context to Files and Scratchpads'], [ADD + 'Lab: Keep a 200-step agent inside its budget']),
   (ADD + 'Memory Systems', [ADD + 'Short-Term vs Long-Term Memory', ADD + 'Semantic, Episodic and Procedural Memory', ADD + 'Memory Files: CLAUDE.md and AGENTS.md', ADD + 'Writing, Updating and Forgetting Memories', ADD + 'Knowledge Graphs as Agent Memory'], [ADD + 'Lab: An assistant that remembers your preferences'])]),
 (ADD + 'Tools, Agent Skills and Code Execution', 'Intermediate', [],
  'Give agents capabilities the right way: tools models use well, tool search for large toolsets, code execution, and Agent Skills (SKILL.md).',
  [(ADD + 'Writing Tools for Agents', [ADD + 'Naming, Descriptions and Parameters', ADD + 'Returning Just Enough', ADD + 'Error Messages that Help the Agent Recover', ADD + 'Evaluating Tools with an Agent in the Loop'], []),
   (ADD + 'Scaling to Many Tools', [ADD + 'Why Hundreds of Tool Schemas Break Agents', ADD + 'Tool Search and Deferred Loading', ADD + 'Code Execution: Agents that Write Code against Tools', ADD + 'Sandboxes for Running Agent Code'], [ADD + 'Lab: Agent with a code-execution sandbox']),
   (ADD + 'Agent Skills', [ADD + 'What is an Agent Skill?', ADD + 'Anatomy of a Skill Folder and SKILL.md', ADD + 'Progressive Disclosure: Discovery, Activation, Execution', ADD + 'Writing Descriptions that Trigger Correctly', ADD + 'Bundling Scripts and Reference Files', ADD + 'Skills vs MCP vs Subagents vs Prompts', ADD + 'Testing, Versioning and Sharing Skills'], [ADD + 'Lab: Write a skill and use it in two different agents'])]),
 ('Model Context Protocol (MCP)', 'Intermediate', [30],
  'The standard way to plug tools and data into AI apps: why MCP exists, its architecture and lifecycle, and building local and remote servers and clients.',
  [('Understanding MCP', ['Why MCP Exists: The Fragmentation Problem', 'What is MCP?', 'Hosts, Clients and Servers', 'MCP Primitives: Tools, Resources and Prompts'], []),
   ('How MCP Components Talk', ['Data Flow in MCP', 'The Data Layer: JSON-RPC Messages', 'The Transport Layer: stdio and Streamable HTTP', 'Using MCP in Claude Desktop and Cursor'], []),
   ('The MCP Lifecycle', ['Initialisation: Version and Capability Negotiation', 'Operation and Shutdown'], []),
   ('Building with MCP', ['Open MCP Registries (Smithery)', 'Building a Local MCP Server with FastMCP', 'Building and Deploying a Remote MCP Server', 'Building an MCP Client', 'Building MCP Servers with LangChain', 'Docker MCP Catalog and Toolkit'], ['Lab: Build and connect your own MCP server', 'Lab: Expense tracker MCP server']),
   (ADD + 'MCP in Production', [ADD + 'What Changed in the 2026 MCP Specification', ADD + 'Authorization with OAuth 2.1', ADD + 'MCP Apps: Interactive UI from a Tool', ADD + 'Gateways, Registries and Server Discovery'], [])]),
 (ADD + 'Agent Frameworks and SDKs', 'Intermediate', [],
  'A hands-on tour of the major agent frameworks, type-safe agents and decision models, and how to choose without lock-in.',
  [(ADD + 'Vendor Agent SDKs', [ADD + 'Claude Agent SDK', ADD + 'OpenAI Agents SDK', ADD + 'Google Agent Development Kit (ADK)', ADD + 'Microsoft Agent Framework', ADD + 'AWS Strands Agents and Bedrock AgentCore'], []),
   (ADD + 'Orchestration Frameworks', [ADD + 'LangChain Deep Agents', ADD + 'CrewAI Crews and Flows', ADD + 'LlamaIndex Agents and Workflows', ADD + 'smolagents and Code Agents', ADD + 'TypeScript Agents: Mastra and the Vercel AI SDK'], []),
   (ADD + 'Type-Safe AI and Decision Models', [ADD + 'Why Type Safety Matters for LLM Apps', ADD + 'Pydantic AI', ADD + 'Instructor and Validated Structured Output', ADD + 'Decision Models: Typed Answers instead of Text (Jev)', ADD + 'DSPy: Programming, Not Prompting'], [ADD + 'Lab: A typed routing layer for an agent']),
   (ADD + 'Choosing a Framework', [ADD + 'Comparing Frameworks on One Task', ADD + 'Portability, Lock-In and Going Framework-Free'], [ADD + 'Lab: The same agent in three frameworks'])]),
 (ADD + 'Multi-Agent Systems and Agent Protocols', 'Advanced', [],
  'When multiple agents help, how they coordinate, and the open protocols that connect agents to tools, to each other, to user interfaces and to editors.',
  [(ADD + 'Multi-Agent Design', [ADD + 'When Multiple Agents Help and When They Hurt', ADD + 'Orchestrator and Subagents', ADD + 'Handoffs, Group Chat and Magentic Orchestration', ADD + 'Failure Modes of Multi-Agent Systems'], []),
   (ADD + 'The A2A Protocol', [ADD + 'Agent-to-Agent (A2A) Protocol', ADD + 'A2A Deep Dive: Agent Cards and Discovery', ADD + 'Tasks, Messages, Artifacts and Streaming', ADD + 'A2A vs MCP', ADD + 'Securing Agent-to-Agent Communication'], [ADD + 'Lab: Two agents in different frameworks talking over A2A']),
   (ADD + 'Protocols for Users and Editors', [ADD + 'AG-UI: Streaming Agent Events to a Frontend', ADD + 'Agent Client Protocol: Agents inside Editors', ADD + 'Generative UI', ADD + 'The Open Standards Map: AAIF, MCP, AGENTS.md and A2A'], [])]),
 (ADD + 'Coding Agents and Harness Engineering', 'Advanced', [],
  'Use coding agents well and build the harness around a model: loops, tools, permissions, hooks, sandboxes, long-running agents and keeping agent-written code healthy.',
  [(ADD + 'Working with Coding Agents', [ADD + 'The Coding Agent Landscape: Claude Code, Codex, Gemini CLI, Copilot and Cursor', ADD + 'Explore, Plan, Code, Commit', ADD + 'Spec-Driven Development', ADD + 'Reviewing AI-Written Code'], []),
   (ADD + 'Coding Agents on GitHub', [ADD + 'Copilot in the Editor and on GitHub', ADD + 'Coding Agents that Open Pull Requests', ADD + 'Repository Instructions: AGENTS.md and Custom Instructions', ADD + 'The GitHub MCP Server', ADD + 'Running Coding Agents in GitHub Actions'], []),
   (ADD + 'What a Harness Is', [ADD + 'Model plus Harness: the Parts of an Agent Runtime', ADD + 'Permissions, Hooks and Approval Modes', ADD + 'Subagents, Slash Commands and Plugins', ADD + 'Sandboxes: Containers, MicroVMs and Hosted Sandboxes'], [ADD + 'Lab: Build a minimal coding-agent harness']),
   (ADD + 'Long-Running Agents', [ADD + 'Initializer Agents, Feature Lists and Progress Files', ADD + 'Handing Off across Context Windows', ADD + 'Git as a Safety Net and Checkpoints', ADD + 'Parallel Agents with Worktrees'], []),
   (ADD + 'Harness Engineering for Codebases', [ADD + 'Linters and Tests that Teach the Agent', ADD + 'Background Cleanup Agents'], [ADD + 'Lab: Make a repository agent-ready'])]),
 (ADD + 'Computer-Use, Browser and Voice Agents', 'Advanced', [],
  'Agents that see and act on screens and web pages, and agents that talk in real time.',
  [(ADD + 'Browser Agents', [ADD + 'DOM, Accessibility Tree or Screenshots?', ADD + 'Driving a Browser with Playwright and MCP', ADD + 'Browser Agent Libraries', ADD + 'Logins, Flaky Pages and Safety'], [ADD + 'Lab: A browser agent that fills a form']),
   (ADD + 'Computer Use', [ADD + 'The Screenshot-Action Loop', ADD + 'Running Desktop Agents Safely in VMs', ADD + 'Benchmarks: OSWorld and WebArena'], []),
   (ADD + 'Voice Agents', [ADD + 'Speech-to-Speech vs Cascaded Pipelines', ADD + 'Latency Budgets and Turn-Taking', ADD + 'Tool Calls in a Live Conversation'], [])]),
 (ADD + 'Agent Evals, Observability and Reliability', 'Advanced', [24],
  'Know whether your agent works: outcome and trajectory evals, LLM judges, benchmarks, tracing with OpenTelemetry, and reliability engineering.',
  [(ADD + 'Evaluating Agents', [ADD + 'Why Agent Evals Are Hard', ADD + 'Outcome, Trajectory and Tool-Use Grading', ADD + 'Code, Model and Human Graders', ADD + 'pass@k, pass^k and Noise', ADD + 'Building an Eval Suite from Real Failures', ADD + 'LLM-as-Judge: Rubrics and Calibration'], [ADD + 'Lab: An eval suite for a support agent']),
   (ADD + 'Benchmarks', [ADD + 'Agent Benchmarks: SWE-bench, Terminal-Bench, tau-bench, GAIA and More', ADD + 'Contamination and Eval Awareness'], []),
   ('Observability', ['Traces, Spans and OpenTelemetry GenAI Conventions', 'LangSmith Setup and Zero-Code Tracing', 'Intermediate Outputs and Analytics', 'Low-Code Agent Tracing', ADD + 'Langfuse, Opik, Phoenix and Braintrust', ADD + 'Cost, Latency and Token Dashboards', 'Feedback and Annotation Loops', 'Prompt Optimisation Pipelines'], ['Lab: Trace an app in LangSmith and Opik']),
   (ADD + 'Reliability Engineering', [ADD + 'Retries, Timeouts and Idempotent Tools', ADD + 'Durable Execution', ADD + 'Regression Testing Prompts and Model Upgrades'], [])]),
 (ADD + 'Agent Security and Safety', 'Advanced', [],
  'Threat-model an agent and defend it: prompt injection, the OWASP Top 10 for agentic applications, least privilege, sandboxing, approvals and red-teaming.',
  [(ADD + 'Threat Modelling Agents', [ADD + 'Why Agents Change the Security Picture', ADD + 'Direct and Indirect Prompt Injection', ADD + 'The Lethal Trifecta', ADD + 'OWASP LLM Top 10 and Agentic Top 10'], []),
   (ADD + 'The Agentic Top 10 in Practice', [ADD + 'Goal Hijack and Tool Misuse', ADD + 'Identity, Privilege and Credentials for Agents', ADD + 'Supply Chain: Malicious MCP Servers and Skills', ADD + 'Unexpected Code Execution', ADD + 'Memory Poisoning and Inter-Agent Spoofing', ADD + 'Cascading Failures, Trust Exploitation and Rogue Agents'], []),
   (ADD + 'Defences', [ADD + 'Least Privilege and Scoped Credentials', ADD + 'Sandboxing Files and Network', ADD + 'Human Approval Gates and Auto-Approval Classifiers', ADD + 'Guardrails and Policy Engines', ADD + 'Red-Teaming Your Own Agent'], [ADD + 'Lab: Attack and defend a tool-using agent'])]),
 (ADD + 'Shipping Agents to Production', 'Advanced', [24],
  'Architect, run and operate agents for real users: separating the loop from the sandbox, background agents, UX for approvals, and cost control.',
  [(ADD + 'Architecture', [ADD + 'Separating the Brain from the Hands', ADD + 'Managed Agent Platforms vs Self-Hosting', ADD + 'Background Agents, Queues and Webhooks', ADD + 'Deploying Agents with Docker and Serverless'], []),
   (ADD + 'Product and Operations', [ADD + 'Streaming Progress and Human-in-the-Loop UX', ADD + 'Approvals, Undo and Audit Logs', ADD + 'Rate Limits, Budgets and Cost Controls'], [ADD + 'Lab: Ship a background agent with approvals']),
   ('LLM Gateways and Model Routing', ['What is an LLM Gateway?', 'OpenAI-Compatible Routing with Bifrost', 'Drop-In SDK Replacement', 'Automated Structured Fallbacks'], ['Lab: Add a gateway with automatic fallback']),
   (ADD + 'Personal and Business Automation Agents', [ADD + 'Identity Files: Giving an Agent a Persona and Rules', ADD + 'The Setup Interview: Capturing What the Agent Needs to Know', ADD + 'Tool Registries and Skill Kits', ADD + 'Scheduled Agents with cron', ADD + 'Running an Agent on Your Laptop with Local Models', ADD + 'Agents for Business Automation: Case Studies'], [ADD + 'Lab: Build a personal assistant agent end to end'])]),
 ('Multi-Agent Research System (Capstone)', 'Advanced', [31],
  'Build and ship a multi-agent system that researches, analyses and writes reports, with CI/CD on AWS.',
  [('Architecting Multi-Agent Systems', ['Introduction to Agentic AI and Multi-Agent Architectures', 'Designing Specialised Agents: Search, Reader, Analyst, Generator, Coordinator'], []),
   ('Collaboration and Control', ['Shared Memory and Communication State', 'Prompting for Multi-Turn Collaboration', 'Human Feedback Checkpoints'], []),
   ('Tools and Workflow', ['Connecting arXiv, Search and Paper Parsers', 'LangGraph Agent Workflows', 'Adding RAG for External Knowledge'], ['Lab: Build the research team']),
   ('Deployment and Automation', ['FastAPI Backend for Agents', 'UI for Logs, Graphs and Reports', 'CI/CD with GitHub Actions', 'Docker and AWS EC2 Deployment'], ['Lab: Ship it to AWS'])]),
]),
('Data Engineering', [
 (ADD + 'Data Engineering Foundations', 'Intermediate', [],
  'What data engineers build and why: the data lifecycle, OLTP vs OLAP, batch vs streaming, file formats and advanced SQL.',
  [(ADD + 'The Data Engineering Landscape', [ADD + 'What Does a Data Engineer Do?', ADD + 'The Data Lifecycle: Ingest, Store, Transform, Serve', ADD + 'OLTP vs OLAP', ADD + 'Batch vs Streaming', ADD + 'The Modern Data Stack'], []),
   (ADD + 'Files and Formats', [ADD + 'CSV, JSON, Parquet and Avro', ADD + 'Compression and Partitioned Files', ADD + 'Fast DataFrames with Polars and DuckDB'], [ADD + 'Lab: Convert a CSV lake to partitioned Parquet']),
   (ADD + 'Advanced SQL', [ADD + 'Window Functions', ADD + 'CTEs and Recursive Queries', ADD + 'Query Plans and Indexes', ADD + 'Transactions and Isolation Levels', ADD + 'SQL Patterns: Deduplication, Gaps and Islands, Sessionisation'], [ADD + 'Lab: 25 SQL interview problems'])]),
 ('Big Data with PySpark', 'Advanced', [17],
  "Process data that won't fit in memory with Spark: architecture, DataFrames, Spark SQL and optimisation.",
  [('The Big Data Problem', ['Why Single Machines Fail', 'Distributed Computing and Spark', 'Driver, Executors and Cluster Manager'], []),
   ('PySpark DataFrames and SQL', ['From pandas to PySpark', 'Filters, Aggregations and Joins', 'Spark SQL', 'Complex Data Types'], ['Lab: Analyse a 10 GB dataset']),
   ('Optimisation', ['Lazy Evaluation: Transformations vs Actions', 'Reading the Spark UI', 'Spot Instances and Cost'], [])]),
 (ADD + 'Warehouses and Lakehouses', 'Advanced', [],
  'Design data that is easy to query and cheap to store: dimensional models, slowly changing dimensions, cloud warehouses, and lakehouses on Delta Lake and Iceberg.',
  [(ADD + 'Modelling Fundamentals', [ADD + 'Normalisation and When to Break It', ADD + 'Facts and Dimensions', ADD + 'Star and Snowflake Schemas', ADD + 'Slowly Changing Dimensions', ADD + 'Data Vault and One Big Table'], [ADD + 'Lab: Model an online shop as a star schema']),
   (ADD + 'Cloud Warehouses', [ADD + 'Columnar Storage and MPP', ADD + 'Snowflake, BigQuery and Redshift Compared', ADD + 'Partitioning, Clustering and Cost Control', ADD + 'Semantic Layers and Metrics'], []),
   (ADD + 'The Lakehouse', [ADD + 'From Data Lakes to Lakehouses', ADD + 'Delta Lake', ADD + 'Apache Iceberg and Iceberg v3', ADD + 'Apache Hudi and Choosing a Format', ADD + 'Catalogs: Unity, Polaris, Glue and REST', ADD + 'Time Travel, Schema Evolution and Compaction', ADD + 'Query Engines: Trino, DuckDB and ClickHouse', ADD + 'Spark Performance Tuning: Shuffles, Skew and AQE'], [ADD + 'Lab: Build a small Iceberg lakehouse'])]),
 (ADD + 'Data Pipelines: Ingestion, dbt and Airflow', 'Intermediate', [],
  'Move data in, transform it with tested dbt models, and run it all on a schedule with Airflow and its alternatives.',
  [(ADD + 'Ingestion', [ADD + 'ETL vs ELT', ADD + 'Ingestion Tools: Fivetran, Airbyte and dlt', ADD + 'Change Data Capture'], [ADD + 'Lab: Load an API into DuckDB with dlt']),
   (ADD + 'dbt', [ADD + 'dbt Projects, Models and the DAG', ADD + 'Sources, refs and the Medallion Layers', ADD + 'Tests, Contracts and Documentation', ADD + 'Incremental Models and Snapshots', ADD + 'Jinja, Macros and Packages', ADD + 'CI for dbt and the Fusion Engine'], [ADD + 'Lab: Build a dbt project on DuckDB']),
   (ADD + 'Airflow Core', [ADD + 'Why Pipelines Need an Orchestrator', ADD + 'DAGs, Tasks, Operators and Sensors', ADD + 'The TaskFlow API', ADD + 'Scheduling, Backfills and Idempotency', ADD + 'Dynamic Task Mapping', ADD + 'Assets and Event-Driven Scheduling in Airflow 3'], [ADD + 'Lab: A daily ELT DAG with retries and alerts']),
   (ADD + 'Running Orchestration in Production', [ADD + 'Running Airflow on Docker, Kubernetes and Managed Services', ADD + 'Dagster, Prefect and Other Orchestrators'], [])]),
 (ADD + 'Streaming Data with Kafka', 'Advanced', [],
  'Move and process events in real time: Kafka, delivery guarantees, schemas, CDC with Debezium and stream processing with Flink and Spark.',
  [(ADD + 'Kafka Fundamentals', [ADD + 'Events, Logs and the Streaming Mindset', ADD + 'Topics, Partitions and Offsets', ADD + 'Producers, Consumers and Consumer Groups', ADD + 'Delivery Guarantees and Exactly-Once', ADD + 'Schemas and Schema Evolution', ADD + 'Kafka Without ZooKeeper: KRaft'], [ADD + 'Lab: Produce and consume click events']),
   (ADD + 'Stream Processing', [ADD + 'Windows, Watermarks and Late Data', ADD + 'Spark Structured Streaming', ADD + 'Apache Flink', ADD + 'CDC with Debezium'], [ADD + 'Lab: Real-time order dashboard'])]),
 (ADD + 'Data Quality, Governance and DataOps', 'Advanced', [],
  'Make data trustworthy: tests, contracts, lineage, observability, CI/CD and infrastructure as code for data platforms.',
  [(ADD + 'Trustworthy Data', [ADD + 'Data Quality Dimensions and Tests', ADD + 'Great Expectations and Soda', ADD + 'Data Contracts', ADD + 'Lineage with OpenLineage and Data Catalogs', ADD + 'Data Observability'], []),
   (ADD + 'DataOps and Governance', [ADD + 'CI/CD and Environments for Data', ADD + 'Terraform for Data Platforms', ADD + 'Privacy, PII and Access Control'], [ADD + 'Lab: Add tests, contracts and CI to a pipeline'])]),
 (ADD + 'Cloud Data Platforms', 'Advanced', [],
  'The data services on AWS, Google Cloud and Azure, how they fit together, what they cost, and which certifications map to them.',
  [(ADD + 'The Big Three Clouds', [ADD + 'AWS Data Services: S3, Glue, Athena, EMR, Redshift and Kinesis', ADD + 'Google Cloud Data Services: BigQuery, Dataflow, Pub/Sub and Composer', ADD + 'Azure Data Services: ADLS, Data Factory, Fabric and Databricks', ADD + 'Databricks and Snowflake as Platforms', ADD + 'FinOps: Controlling Data Costs', ADD + 'Data Engineering Certifications Map'], [ADD + 'Lab: Serverless pipeline on AWS']),
   (ADD + 'Data Engineering for AI', [ADD + 'Pipelines for RAG: Chunking, Embedding and Refreshing', ADD + 'Feature Stores and ML Pipelines', ADD + 'Data Agents and MCP Servers for Warehouses'], [])]),
 (ADD + 'Data Engineering Capstone and System Design', 'Advanced', [],
  'Build an end-to-end platform and practise the system design and SQL questions asked in data engineering interviews.',
  [(ADD + 'Capstone', [], [ADD + 'Lab: CDC from Postgres to Kafka to Iceberg to dbt to a dashboard']),
   (ADD + 'Interview Preparation', [ADD + 'Data Pipeline System Design Framework', ADD + 'Design Drills: Clickstream, Ride Events and Fraud Detection', ADD + 'Batch vs Streaming, Lambda vs Kappa Trade-offs', ADD + 'Data Engineering Interview Questions Explained'], [])]),
]),
('Projects', [
 ('End-to-End AI Projects', 'Advanced', ['Projects'],
  'Portfolio projects across data engineering, ML, deep learning, GenAI and agentic AI, each deployed with CI/CD.',
  [('Python and Data Engineering', [], ['Project: Review Scraper End to End', 'Project: Supabase and Streamlit Database App']),
   ('Machine Learning', [], ['Project: Network Intrusion Detection System', 'Project: Insurance Premium Predictor API']),
   ('Deep Learning', [], ['Project: Text Summarisation', 'Project: Machine Translation', 'Project: Question Answering']),
   ('Generative AI and RAG', [], ['Project: RAG Q&A System with CI/CD']),
   ('Agentic AI', [], ['Project: AI Newsletter Generator with MCP'])]),
]),
]


def clean(s):
    return s.replace(ADD, "")

catalog = []
n = 0
for ti, (track, courses) in enumerate(TRACKS, 1):
    track = f"Track {ti} · {track}"
    for title, level, mods, card, modules in courses:
        course_added = title.startswith(ADD)
        title = clean(title)
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
                        "syllabus_modules": mods, "added": course_added, "description": card, "modules": out_modules,
                        "module_count": len(out_modules), "lesson_count": nl, "hours": max(hrs, 1)})

# ---------------------------------------------------------------------------
# Prerequisites. Course-level: what to finish first. Module-level: the exact
# earlier modules a module builds on. Both must point backwards in the catalog.
# ---------------------------------------------------------------------------
CLI, PY, GIT = "The Command Line and Linux Basics", "Python Programming", "Git and GitHub: Zero to Pro"
NUM, DB, STATS = "Data Analysis and Visualisation with Python", "Databases: SQL and NoSQL", "Statistics for Data Science"
FE, ML, ENS = "Machine Learning Foundations: Data, EDA and Features", "Supervised Learning", "Ensembles and Unsupervised Learning"
API, MLF = "APIs and Apps: FastAPI, Streamlit and Docker", "MLOps with MLflow"
NLP, DL, SEQ = "NLP for Machine Learning", "Deep Learning with PyTorch", "Sequence Models, Attention and Transformers"
GEN, LC, RAG = "Generative AI and LLM Foundations", "LangChain Complete Guide", "Retrieval-Augmented Generation (RAG)"
AG, LG, ARAG, KG = ("Agentic AI Fundamentals", "LangGraph Complete Guide", "Agentic RAG Systems",
    "Knowledge Graphs, Ontologies and Unstructured Data")
CTX, SKL, MCP, FW, MAS = ("Context Engineering and Agent Memory", "Tools, Agent Skills and Code Execution",
    "Model Context Protocol (MCP)", "Agent Frameworks and SDKs", "Multi-Agent Systems and Agent Protocols")
CODE, CUA, EVAL, SEC, SHIP, CAP = ("Coding Agents and Harness Engineering", "Computer-Use, Browser and Voice Agents",
    "Agent Evals, Observability and Reliability", "Agent Security and Safety", "Shipping Agents to Production",
    "Multi-Agent Research System (Capstone)")
DEF, SPARK, WH, PIPE, KAF, DQ, CLOUD, DECAP = ("Data Engineering Foundations", "Big Data with PySpark",
    "Warehouses and Lakehouses", "Data Pipelines: Ingestion, dbt and Airflow", "Streaming Data with Kafka",
    "Data Quality, Governance and DataOps", "Cloud Data Platforms", "Data Engineering Capstone and System Design")
PROJ = "End-to-End AI Projects"

PREREQ_COURSES = {
    PY: [CLI], GIT: [CLI, PY],
    NUM: [PY], DB: [PY], STATS: [NUM],
    FE: [NUM, STATS], ML: [FE], ENS: [ML],
    API: [PY, DB], MLF: [ML, API],
    NLP: [ML], DL: [ML], SEQ: [DL, NLP],
    GEN: [SEQ, API], LC: [GEN], RAG: [LC, DB],
    AG: [GEN], LG: [AG, LC], ARAG: [RAG, LG], KG: [ARAG], CTX: [LG, KG], SKL: [CTX], MCP: [SKL, API],
    FW: [LG, MCP], MAS: [FW], CODE: [SKL, GIT], CUA: [FW], EVAL: [FW, RAG], SEC: [SKL, MCP], SHIP: [EVAL, SEC, API],
    CAP: [LG, ARAG, MCP, MAS, SHIP],
    DEF: [DB, NUM, CLI], SPARK: [DEF], WH: [DEF, SPARK], PIPE: [WH, GIT], KAF: [DEF, SPARK], DQ: [PIPE],
    CLOUD: [WH, API, RAG, MCP], DECAP: [KAF, WH, DQ, CLOUD],
}

PREREQ_MODULES = {
    (PY, "Concurrency for AI Apps"): [(PY, "Functions and Iterators")],
    (PY, "Object-Oriented Programming"): [(PY, "Functions and Iterators")],
    (NUM, "NumPy Essentials"): [(PY, "Strings and Data Structures")],
    (DB, "PostgreSQL on Supabase"): [(PY, "Functions and Iterators")],
    (STATS, "Data Behaviour and Relationships"): [(NUM, "NumPy Essentials")],
    (STATS, "Estimation"): [(STATS, "Distributions")],
    (STATS, "Hypothesis Testing"): [(STATS, "Distributions"), (STATS, "Estimation")],
    (STATS, "Bayesian Thinking"): [(STATS, "Probability")],
    (FE, "Exploratory Data Analysis"): [(NUM, "Seaborn and Storytelling"), (NUM, "Statistics and Plots in pandas")],
    (FE, "Feature Transformation and Selection"): [(STATS, "Data Behaviour and Relationships")],
    (ML, "Regression"): [(STATS, "Central Tendency and Dispersion"), (FE, "Feature Scaling and Encoding")],
    (ML, "Gradient Descent and Regularisation"): [(ML, "Regression")],
    (ML, "Classification"): [(STATS, "Probability")],
    (ML, "More Supervised Algorithms"): [(STATS, "Bayesian Thinking")],
    (ENS, "Ensemble Learning"): [(ML, "More Supervised Algorithms")],
    (ENS, "Unsupervised Learning"): [(FE, "Feature Transformation and Selection")],
    (ENS, "Dimensionality Reduction"): [(NUM, "NumPy Essentials"), (ENS, "Unsupervised Learning")],
    (API, "Validation and Schemas"): [(PY, "Object-Oriented Programming")],
    (API, "Production Considerations"): [(PY, "Modules and Exceptions")],
    (API, "State and Responsiveness"): [(PY, "Concurrency for AI Apps")],
    (API, "Serving Machine Learning Models"): [(ML, "Regression")],
    (MLF, "Experiment Tracking"): [(ML, "Regression")],
    (MLF, "Serving and Deployment"): [(API, "Docker and Cloud Deployment")],
    (NLP, "Text Representation"): [(FE, "Feature Transformation and Selection")],
    (NLP, "Word Embeddings"): [(NUM, "NumPy Essentials"), (STATS, "Data Behaviour and Relationships")],
    (DL, "Neural Networks"): [(ML, "Regression"), (ML, "Classification")],
    (SEQ, "Sequence Models"): [(DL, "Neural Networks"), (NLP, "Word Embeddings")],
    (SEQ, "Sequence Models in PyTorch"): [(DL, "The Training Pipeline")],
    (GEN, "How LLMs Work"): [(SEQ, "Transformers")],
    (GEN, "Prompting and Structured Output"): [(API, "Validation and Schemas")],
    (LC, "Structured Output and Output Parsers"): [(GEN, "Prompting and Structured Output"), (API, "Validation and Schemas")],
    (LC, "Monitoring and Deployment"): [(API, "APIs and FastAPI Fundamentals")],
    (RAG, "Introduction to RAG"): [(GEN, "How LLMs Work")],
    (RAG, "Embeddings and Vector Databases"): [(NLP, "Word Embeddings"), (DB, "Relational Databases and SQL")],
    (RAG, "Vector Database Tools"): [(DB, "NoSQL with MongoDB Atlas")],
    (RAG, "RAG Building Blocks in LangChain"): [(LC, "Chains and Runnables")],
    (RAG, "Implementing RAG"): [(LC, "Chains and Runnables"), (RAG, "Vector Database Tools")],
    (RAG, "RAG Evaluation"): [(RAG, "Implementing RAG")],
    (AG, "Understanding Agents"): [(GEN, "How LLMs Work")],
    (AG, "Tools and Function Calling"): [(GEN, "Prompting and Structured Output"), (LC, "Tools and Tool Calling")],
    (LG, "Getting Started"): [(AG, "The Agent Loop"), (LC, "Chains and Runnables")],
    (LG, "Workflows and Agents"): [(AG, "Tools and Function Calling"), (AG, "Reasoning Patterns")],
    (LG, "Chatbots and Persistence"): [(API, "Streamlit Basics")],
    (LG, "Memory"): [(GEN, "How LLMs Work")],
    (ARAG, "Adaptive RAG"): [(RAG, "Implementing RAG"), (LG, "Workflows and Agents")],
    (ARAG, "Agentic RAG Architectures"): [(AG, "Reasoning Patterns")],
    (ARAG, "Self-RAG"): [(RAG, "Vector Database Tools"), (RAG, "RAG Evaluation")],
    (KG, "Knowledge Graphs for AI Agents"): [(ARAG, "Agentic RAG Architectures"), (RAG, "Embeddings and Vector Databases")],
    (MCP, "Understanding MCP"): [(AG, "Tools and Function Calling")],
    (MCP, "Building with MCP"): [(LC, "Tools and Tool Calling"), (API, "Docker and Cloud Deployment")],
    (CODE, "Coding Agents on GitHub"): [(GIT, "GitHub Actions"), (MCP, "Building with MCP")],
    (EVAL, "Observability"): [(LC, "Monitoring and Deployment")],
    (SHIP, "LLM Gateways and Model Routing"): [(API, "Production Considerations")],
    (CAP, "Architecting Multi-Agent Systems"): [(AG, "Multi-Agent Systems and the Ecosystem")],
    (CAP, "Collaboration and Control"): [(LG, "State in Depth"), (LG, "Human-in-the-Loop and Debugging")],
    (CAP, "Tools and Workflow"): [(MCP, "Building with MCP"), (ARAG, "Agentic RAG Architectures")],
    (CAP, "Deployment and Automation"): [(API, "Production Considerations"), (API, "Streamlit Basics"), (MLF, "Serving and Deployment")],
    (SPARK, "PySpark DataFrames and SQL"): [(NUM, "pandas Core"), (DB, "Relational Databases and SQL")],
    (PROJ, "Python and Data Engineering"): [(DB, "PostgreSQL on Supabase"), (API, "State and Responsiveness")],
    (PROJ, "Machine Learning"): [(ENS, "Boosting"), (MLF, "Serving and Deployment")],
    (PROJ, "Deep Learning"): [(SEQ, "Transformers")],
    (PROJ, "Generative AI and RAG"): [(RAG, "Advanced RAG"), (RAG, "RAG Evaluation")],
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
         f"{c['track']} · " + (f"Bootcamp syllabus module(s): {', '.join(map(str, c['syllabus_modules']))}" if c["syllabus_modules"] else "➕ Added beyond the bootcamp syllabus"), "", c["description"], "",
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
