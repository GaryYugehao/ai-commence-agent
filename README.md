# AI E-Commerce Agent

This project implements an AI-driven e-commerce agent capable of natural language interaction with users, providing text-based product recommendations, and image-based product search functionalities. The backend is built with Python FastAPI, integrating Google Gemini AI models, while the frontend is a user-friendly chat interface built with React (Vite + TypeScript).

The AI E-Commerce Agent offers three core functionalities to assist users:

1.  **General Conversation & Inquiry:**
    * Users can engage in natural, open-ended conversations with "Rufus," the AI agent.
    * Powered by Google Gemini's chat capabilities (`gemini.chat`), the agent can answer general questions, provide information about its functions, and maintain context throughout the conversation for a coherent interaction. This conversational memory allows for follow-up questions and a more natural user experience.

2.  **Text-Based Product Recommendation:**
    * Users can request product recommendations by describing what they are looking for in text (e.g., "Recommend a t-shirt for sports").
    * If the user's query includes keywords like "recommend," the backend logic triggers a specific workflow.
    * The agent then consults the `products_db` (a JSON file containing product information) and leverages a Gemini language model to match the user's query against the product descriptions and tags, returning relevant product suggestions.

3.  **Image-Based Product Search:**
    * Users can upload an image of a product they are interested in.
    * The backend receives the image, and a Gemini vision model processes it to understand its content and generate a textual description (e.g., "red cotton t-shirt").
    * This generated description is then used as a query to search the `products_db`, similar to the text-based recommendation, to find and suggest visually similar or related products.
### Example Interactions:

To see example responses for each feature, you can try the following inputs:

* **General Conversation:**
    * `hi, what can you do?`
    * `can you see me?`
* **Text-Based Product Recommendation:**
    * `any random recommendations?`
    * `Recommend some toothpaste for me.`
    * `Recommend some t-shirt for me.`
* **Image-Based Product Search:**
    * Upload `./example_pics/pic1.jpg` .
    * Upload `./example_pics/pic2.jpg` .
      *(Note: For image recommendations, ensure the backend is configured to serve images from your `productinfo/images/` directory, and that the sample images exist and are representative of products in your `products.json` for meaningful results.)*

![ai-commerce-agent-ezgif com-speed](https://github.com/user-attachments/assets/07696eb4-ba23-4004-9dd5-27c53222616b)


## Tech Stack

* **Backend:**
    * Python 3.12
    * FastAPI: High-performance web framework
    * Uvicorn: ASGI server
    * Google Gemini API: AI model support
    * Pydantic & Pydantic-Settings: Data validation and configuration management
    * Conda: Environment management
* **Frontend:**
    * React (Vite + TypeScript)
    * Tailwind CSS: UI styling
    * Axios: HTTP requests
* **Version Control:** Git & GitHub

### Technology Choices and Trade-offs:

* **FastAPI (Backend Framework):**
    * **Why I chose it:** "I went with FastAPI because, compared to something like Flask, I find it offers a more guided approach. Flask is great for its 'do whatever you want' flexibility, but FastAPI has this well-established paradigm of 'Endpoint -> Pydantic -> Database' (even though I'm using a JSON file here instead of a full DB with SQLAlchemy for simplicity). This structure is incredibly useful for quick validation, automatic API documentation, and handling things like pre and post-processing with validators. It just feels more efficient for building out APIs."
    * **In short:** Offers structure, speed, built-in validation, and auto-docs, which I prefer over Flask's more minimal approach for this kind of project.

* **Pydantic (Data Validation & Settings):**
    * **Why I chose it:** "Pydantic works hand-in-glove with FastAPI, which is a major plus. It handles data validation and settings management really smoothly. In the past, for Google YouTube production environments, I've used tools like protobuf, but for a personal project like this, protobuf would be overly complex and frankly, a bit bloated. Pydantic is lightweight and does exactly what I need for schema definition and loading configs from `.env` files."
    * **In short:** Excellent synergy with FastAPI; lightweight and effective for validation and settings without the overkill of enterprise database tools for this project's scale.

* **Google Gemini API (AI Model):**
    * **Why I chose it:** "This was a pretty straightforward decision. I have a 16-month Gemini membership that I got when I was studying at the University of Waterloo. This gives me a very generous amount of free development credits, making it the most cost-effective option for me to experiment with its chat and vision capabilities without worrying about API costs during development."
    * **In short:** Significant free usage tier available to me, making it ideal for development and experimentation for a personal project.

* **React (Frontend Library):**
    * **Why I chose it:** "For the frontend, I picked React. The reason is simple: it's the most popular library out there. This means a huge community, tons of resources, and a vast ecosystem of tools and components that make development easier."
    * **In short:** Its popularity translates to extensive resources and a large ecosystem, which is beneficial for development.

* **Tailwind CSS (CSS Framework):**
    * **Why I chose it:** "I opted for Tailwind CSS because it's just faster for me. Compared to writing custom CSS or using other frameworks, Tailwind's utility-first approach lets me build and style UIs much more quickly directly in the markup."
    * **In short:** Enables rapid UI development due to its utility-first approach.

## Prerequisites

Before you begin, please ensure your system has the following software installed:

* Git: For cloning the code repository.
* Conda (Miniconda or Anaconda): For managing Python environments. ([Miniconda Installation Guide](https://docs.conda.io/en/latest/miniconda.html))
* Node.js and npm (or yarn): Recommended Node.js 22.x LTS version. ([Node.js Downloads](https://nodejs.org/))
* A valid Google Gemini API Key. ([Get a Gemini API Key](https://aistudio.google.com/))

## Project Setup and Installation

Please follow these steps to set up and run this project:

**1. Clone the Repository**

```bash
git clone https://github.com/GaryYugehao/ai-commence-agent.git
cd cd ai-commerce-agent
```

**2. Backend Environment Setup (using Conda)**

We recommend using the `environment.yml` file with Conda to create a Python environment consistent with the development setup. An `requirements.txt` file is also provided as an alternative.

* **Option A: Using `environment.yml` (Recommended for exact environment replication)**
    ```bash
    # Run from the project root directory:
    conda env create -f environment.yml
    conda activate ai-commerce-agent
    ```
  The environment name `ai-commerce-agent` is specified in the `environment.yml` file.

* **Option B: Using `requirements.txt` in `./backend/` (If you prefer not to use the Conda environment file or want to install in an existing environment)**
  First, create a new Conda environment (or another Python virtual environment of your choice) and activate it:
    ```bash
    conda create --name ai-commerce-agent python=3.12
    conda activate ai-commerce-agent
    ```
  Then, install the dependencies:
    ```bash
    cd backend
    pip install -r requirements.txt
    cd ..
    ```

**3. Frontend Environment Setup**

```bash
cd frontend
npm install   # Or if you use yarn: yarn install
cd ..
```

**4. Configure Environment Variables (Crucial!)**

* **Backend API Key:**
    1.  Navigate to the `.idea/` directory.
    2.  Copy the `.idea/.env.example` file and rename it to `.env`.
        ```bash
        cp .idea/.env.example .idea/.env
        ```
    3.  Edit the `.idea/.env` file and replace the `GEMINI_API_KEY` placeholder with your own valid Google Gemini API Key.
        ```env
        # .idea/.env
        GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
        ```

* **Frontend API Address (if adjustment is needed):**
  The frontend application will, by default, attempt to connect to `http://localhost:8086` (or the backend port you have configured in your code). If you have provided a `.env.example` file in the `frontend/` directory for `VITE_API_BASE_URL`, please include instructions here on how to create `.env.local` or `.env` and modify it. Typically, for local development, the default pointing to `http://localhost:BACKEND_PORT_NUMBER` is sufficient.

## Running the Application

**1. Start the Backend Server**

* Ensure your Conda environment `ai-commerce-agent` is activated:
    ```bash
    conda activate ai-commerce-agent
    ```
* From the **project root directory**, run the following command to start the FastAPI backend service:
    ```bash
    uvicorn backend.main:app --host 0.0.0.0 --port 8086 --reload
    ```
* The backend API service should now be running at `http://localhost:8086`. You will see logs in your terminal similar to "INFO: Uvicorn running on http://0.0.0.0:8086".

**2. Start the Frontend Development Server**

* Open a new terminal window or tab.
* Your Conda environment does **not** need to be activated for the frontend, unless your Node/npm installation is managed via Conda. Typically, Node.js/npm is independent of the Python environment.
* Navigate to the `frontend/` directory:
    ```bash
    cd frontend
    ```
* Run the following command to start the Vite frontend development server:
    ```bash
    npm run dev
    ```
  (Or, if you use `yarn`: `yarn dev`)
* The frontend application will usually open automatically in your browser, or you can find the access URL in the terminal output (typically `http://localhost:5173`).

You should now be able to interact with the AI E-Commerce Agent via the frontend URL in your browser!

## Project Structure (Overview)

```
project-root/
├── example_pics/
│   ├── pic1.jpg           # Example pic for you to test image recommendation
│   ├── pic1.jpg           # Example pic for you to test image recommendation
├── .idea/
│   ├── .env.example        # environment variable example
├── backend/
│   ├── config.py           # Application configuration (includes API key loading)
│   ├── main.py             # FastAPI application entry point
│   ├── schema.py           # Pydantic data models
│   ├── utils.py            # Utility functions
│   └── requirements.txt    # Python dependencies (pip)
├── frontend/
│   ├── public/             # Static assets
│   ├── src/                # React application source (App.tsx, components, etc.)
│   ├── .env.example        # (Optional) Frontend environment variable example
│   ├── index.html          # Vite entry HTML
│   ├── package.json        # Node.js dependencies and scripts
│   ├── vite.config.ts      # Vite configuration
│   └── tailwind.config.js  # Tailwind CSS configuration
├── productinfo/
│   ├── products.json       # Example product data
│   └── images/             # Example product image folder
│       ├── image1.jpg
│       └── ...
├── .gitignore              # Git ignore rules
├── environment.yml         # Conda environment definition file
└── README.md               # This file
```

---

Please feel free to raise any issues or provide suggestions!
# ai-commence-agent
