# Bank Transaction AI Assistant

This AI-powered assistant allows users to ask natural language questions about their **bank transactions**, and it responds with **relevant answers and visualizations**.

---

## Project Structure

```

submission.zip
├── data/                # Includes the sqlite database and embeddings file
├── notebooks/           # Notebooks and their .html exports
├── main/                # Core application classes and app.py
├── requirements.txt     # All Python dependencies
└── README.md            # Setup and usage instructions (this file)

````

---

## How to Run the Application

### 1. Install Python Dependencies

In the root directory (where `requirements.txt` is located), run:

```bash
pip install -r requirements.txt
````

> We recommend using a virtual environment to avoid conflicts:
>
> ```bash
> python -m venv venv
> source venv/bin/activate  # or venv\Scripts\activate on Windows
> ```

---

### 2. Launch the App

From the root directory:

```bash
cd main
streamlit run app.py
```

This will start the Streamlit app at:
👉 [http://localhost:8501](http://localhost:8501)

---

## `notebooks/`

The `notebooks/` folder contains exploratory notebooks and code experiments. It also contains their `.html` versions.

---

## Example Prompts

* *"How much did I spend on Uber last month?"*
* *"Visualise utility bills over the year."*
* *"Summarize my spending by category between August and September."*

---

