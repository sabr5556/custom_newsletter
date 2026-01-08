# The Daily Distill 🥃
**A Custom AI-Powered Newsletter Aggregator**

The Daily Distill is an intelligent news aggregation platform that turns the chaos of RSS feeds into a hyper-personalized, high-signal daily briefing.

Unlike standard aggregators that just dump links, this project uses a multi-stage AI pipeline to **read, filter, deduplicate, and synthesize** thousands of articles into a cohesive, professional newsletter tailored to individual user interests.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg) ![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg) ![Anthropic](https://img.shields.io/badge/AI-Claude%203.5%20Haiku-purple)

## 🏗 Architecture

The system operates in three distinct phases to ensure efficiency and scalability:

### Phase 1: Ingestion & Refining
* **Scraper (`scraper.py`)**: Fetches thousands of articles from diverse RSS sources (CNBC, ESPN, TechCrunch, etc.) looking back 24 hours.
* **Tagger (`tagger.py`)**: Uses **Claude 3 Haiku** to analyze every single article. It assigns primary/secondary tags, filters out low-value content (clickbait, reviews, "top 10" lists), and assigns an importance score (1-10).
* **Deduper (`deduper.py`)**: Performs semantic analysis to identify and merge duplicate stories across different publishers, ensuring the master feed is clean.

### Phase 2: User Management & Generation
* **Database (`user_manager.py`)**: A SQLite database stores user profiles, preferences (e.g., "Nvidia, AI, Football"), and their generated newsletter history.
* **Generator (`generator.py`)**: The core logic engine. It:
    1.  **Matches**: Selects the top 5-7 stories from the master feed that align with a specific user's preferences.
    2.  **Synthesizes**: Writes a custom "Deep Dive" analysis and an Executive Summary specifically for that user.
    3.  **Formats**: Outputs a production-ready Markdown newsletter.

### Phase 3: Delivery
* **Interface (`app.py`)**: A Streamlit dashboard that serves as the admin panel.
    * **User Management**: Create and edit subscriber profiles.
    * **Preview**: View and regenerate newsletters in real-time.
    * **Review**: See exactly what the AI wrote before it (hypothetically) sends.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* An Anthropic API Key (Claude)

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/sabr5556/custom_newsletter](https://github.com/sabr5556/custom_newsletter)
    cd custom_newsletter
    ```

2.  **Environment Setup**
    Create a `.env` file in the root directory:
    ```bash
    ANTHROPIC_API_KEY=sk-ant-api03...
    ```

### Usage Workflow

1.  **Run the Scraper (Phase 1)**
    This pulls fresh news and builds the `master_feed.json`.
    ```bash
    cd phase1
    python main.py
    ```

2.  **Initialize the Database**
    Navigate to the Phase 2 directory and initialize the database.
    ```bash
    cd ../phase2
    python user_manager.py
    ```

3.  **Launch the Dashboard (Phase 2)**
    Start the admin panel interface.
    ```bash
    streamlit run app.py
    ```

4.  **Generate a Newsletter**
    * Open the Streamlit app in your browser (usually `http://localhost:8501`).
    * Select a user from the sidebar.
    * Click **"🚀 Generate Newsletter"**.

---

## 🛠 Tech Stack
* **Language**: Python
* **GUI**: Streamlit
* **AI Model**: Anthropic Claude 3 Haiku (via API)
* **Database**: SQLite
* **Data Format**: JSON (Intermediate), SQL (Persistent)