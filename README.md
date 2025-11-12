# SME Security Package Recommender (Agentic AI)

This system helps small and medium enterprises (SMEs) select the most suitable security package based on their industry, size, basic tech stack, budget, and compliance requirements. It uses agentic AI to recommend the most suitable Green Circle managed security package — Green Apple, Green Grape, or Green Kiwi — along with a suggested tooling stack of 3–5 vendor components (e.g., EDR, NDR, SIEM, TI).

# ===================================
# How to Run
# ===================================

1. Clone this repository:

	git clone https://github.com/YOUR_USERNAME/SME-Security-Recommender.git
	cd SME-Security-Recommender


2. Install dependencies:

	pip install -r requirements.txt


3. Add your OpenAI API key inside .env (optional):

	HF_API_TOKEN=your-openai-api-key-here


4. Data repository (optional):

	All input data (package definitions, vendor components, and SME profiles) are stored under the data/ directory.

	You can modify or replace these files with your own data to test different SME profiles or vendor setups.

5. Run the security package recommender script:

	python recommender.py


6. Output:

	All results (PDFs and JSON summaries) will be automatically saved under the runs/ directory.


# ===================================
# Assumptions
# ===================================

1- The system assumes that each SME profile contains complete and valid information, including: SME name, industry, size, budget, tech stack, and compliance needs.

2- All package definitions (e.g., Green Apple, Green Grape, Green Kiwi) and vendor components (e.g., EDR, NDR, SIEM, TI tools) are provided and stored under the data/ directory.

3- The OpenAI API key is available and correctly set in the .env file before running the system.

4- The system utilizes an open-source OpenAI Large Language Model (LLM) — specifically the openai/gpt-oss-20b model — hosted on the Hugging Face platform. This LLM serves as the core reasoning engine, interpreting and analyzing the provided SME profiles to generate relevant and context-aware security package recommendations.

# ===================================
# Limitations
# ===================================

1- Model dependency: The quality and accuracy of recommendations rely heavily on the underlying LLM (openai/gpt-oss-20b). Any model bias or limitation may affect results.

2- Maintenance dependency: Future model or API changes (e.g., version updates, endpoint deprecations) may require code adjustments.


# ===================================
# Architecture note
# ===================================

SME-Security-Recommender/
├── configs/
│   └── config.yaml
│
├── data/
│   ├── vendor_components.txt
│   └── Green_Circle_packages_definitions.txt
│   └── SME_profiles.yaml
│
├── runs/
│   ├── Concise_SME_Summary.json
│   └── SME_Summary_Table.json
│   └── SME_Recommendations.pdf
│
├── recommender.py
├── .env
├── requirements.txt
└── README.md

Main Components

1- Data repository 
	- Holds input data: package definitions, vendor components, SME profiles.  

2- Config repository 
	- Stores configurations such as environment variables

3- .env file
	- Stores sensitive settings such as OpenAI API keys   

4- Recommendation script recommender.py
	- Loads and validates SME profiles from YAML file. Each profile includes details such as SME_Name, industry, size: headcount and number of endpoints, cloud/on-prem mix, regulatory drivers (e.g., ISO 27001, PDPL), and rough monthly budget band (e.g., <$2k / $2–5k)
	- loads security package definitions and vendor components from txt files.
	- Uses `openai/gpt-oss-20b` (Hugging Face) to analyze SME data and produce recommendations.
	- Recommends the most suitable Green Circle security package (Green Apple, Green Grape, or Green Kiwi) and selects 3–5 vendor components for the suggested tooling stack (e.g., EDR, NDR, SIEM, TI).
	- Provides a short justification for each recommendation — explaining why the chosen package and tools best fit the SME’s needs.
	- Creates structured outputs capturing all recommendations and justifications in JSON and PDF formats.

5- Runs repository

	- save output files to ensure reproducibility and traceability of each execution
