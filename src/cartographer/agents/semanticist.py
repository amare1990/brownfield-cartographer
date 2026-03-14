# src/cartographer/agents/semanticist.py

import os
from dotenv import load_dotenv

from pathlib import Path
from typing import Dict
import json
import re

from sklearn.cluster import KMeans
import numpy as np

from openai import OpenAI

from src.cartographer.graph.knowledge_graph import KnowledgeGraph


load_dotenv(".env")
# ----------------------------------------------------
# Context Window Budget
# ----------------------------------------------------

class ContextWindowBudget:
    """
    Tracks token usage and selects model tier
    depending on task importance.
    """

    def __init__(self, max_tokens: int = 200000):
        self.max_tokens = max_tokens
        self.used_tokens = 0

    def estimate_tokens(self, text: str) -> int:
        return int(len(text) / 4)

    def can_afford(self, text: str) -> bool:
        return (self.used_tokens + self.estimate_tokens(text)) < self.max_tokens

    def consume(self, text: str):
        self.used_tokens += self.estimate_tokens(text)

    def choose_tier(self, synthesis=False):
        return "expensive" if synthesis else "cheap"


# ----------------------------------------------------
# Semanticist Agent
# ----------------------------------------------------

class Semanticist:
    """
    LLM-powered semantic understanding agent.

    Responsibilities:
    - Generate purpose statements
    - Detect documentation drift
    - Cluster modules into business domains
    - Generate Day-One FDE answers
    """

    def __init__(self, kg: KnowledgeGraph):

        self.kg = kg
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        self.cheap_model = os.getenv("MODEL_CHEAP")
        self.expensive_model = os.getenv("MODEL_EXPENSIVE")
        self.embed_model = os.getenv("MODEL_EMBED")

        self.budget = ContextWindowBudget()

        self.purpose_statements: Dict[str, str] = {}
        self.doc_drift: Dict[str, bool] = {}
        self.domain_map: Dict[str, str] = {}

    # ----------------------------------------------------
    # LLM call wrapper
    # ----------------------------------------------------

    def _call_llm(self, prompt: str, synthesis: bool = False) -> str:

      if not self.budget.can_afford(prompt):
          return "Budget exceeded"

      tier = self.budget.choose_tier(synthesis)
      model = self.expensive_model if tier == "expensive" else self.cheap_model

      # fallback to a default model if env var not set
      model = model or ("gpt-4o" if tier == "expensive" else "gemini-1.5-pro")

      response = self.client.chat.completions.create(
          model=model,
          messages=[{"role": "user", "content": prompt}],
          temperature=0.2,
      )

      self.budget.consume(prompt)

      if response and response.choices:
          content = response.choices[0].message.content
          return content.strip() if content else "No content returned"

      return "Error: API response empty"

    # ----------------------------------------------------
    # Purpose Statement Generation
    # ----------------------------------------------------

    def generate_purpose_statement(self, file_path: str):

      try:
          code = Path(file_path).read_text(encoding="utf-8")[:6000]
      except Exception:
          return

      docstring = self._extract_docstring(code)

      prompt = f"""
                You are a software architecture analyst.

                Analyze the following module code and write a 2–3 sentence PURPOSE
                statement describing the BUSINESS FUNCTION of the module.

                Focus on the role it plays in the system, not implementation details.

                Code:
                {code}

                Return only the purpose statement.
                """

      purpose = self._call_llm(prompt)

      self.purpose_statements[file_path] = purpose

      if docstring:
          self.doc_drift[file_path] = self._detect_doc_drift(docstring, purpose)

      if file_path in self.kg.module_graph.nodes:
          self.kg.module_graph.nodes[file_path]["purpose"] = purpose
          self.kg.module_graph.nodes[file_path]["doc_drift"] = self.doc_drift.get(file_path, False)

    # ----------------------------------------------------
    # Docstring extraction
    # ----------------------------------------------------

    def _extract_docstring(self, code: str):

        match = re.search(r'"""(.*?)"""', code, re.DOTALL)

        if match:
            return match.group(1)

        return None

    # ----------------------------------------------------
    # Documentation Drift Detection
    # ----------------------------------------------------

    def _detect_doc_drift(self, docstring: str, purpose: str):

        prompt = f"""
                  Compare the module documentation and the inferred purpose.

                  Docstring:
                  {docstring}

                  Inferred Purpose:
                  {purpose}

                  Does the documentation contradict the implementation?

                  Answer only YES or NO.
                  """

        result = self._call_llm(prompt)

        return "YES" in result.upper()

    # ----------------------------------------------------
    # Domain Clustering
    # ----------------------------------------------------

    def cluster_into_domains(self, k: int = 6):

      texts = list(self.purpose_statements.values())

      if not texts:
          return

      if len(texts) < 2:
        print("Skipping domain clustering — not enough modules.")
        return {}

      k = min(k, len(texts))

      embeddings = [self._embed_text(t) for t in texts]

      X = np.array(embeddings)

      kmeans = KMeans(n_clusters=k, random_state=42).fit(X)

      modules = list(self.purpose_statements.keys())

      clusters = {}

      for module, label in zip(modules, kmeans.labels_):

          domain_name = f"domain_{label}"

          self.domain_map[module] = domain_name
          clusters.setdefault(domain_name, []).append(module)

          if module in self.kg.module_graph.nodes:
            self.kg.module_graph.nodes[module]["domain"] = domain_name

      return clusters

    # ----------------------------------------------------
    # Embedding helper
    # ----------------------------------------------------

    def _embed_text(self, text: str):

      embed_model = self.embed_model or "text-embedding-3-small"  # fallback default
      response = self.client.embeddings.create(
          model=embed_model,
          input=text,
      )

      return response.data[0].embedding

    # ----------------------------------------------------
    # Day-One FDE Questions
    # ----------------------------------------------------

    def answer_day_one_questions(self):

      module_nodes = dict(self.kg.module_graph.nodes(data=True))
      lineage_edges = list(self.kg.lineage_graph.edges(data=True))

      # Collect velocity map
      velocity_map = {
          module: data.get("git_velocity", 0)
          for module, data in module_nodes.items()
      }

      context = json.dumps(
          {
              "modules": module_nodes,
              "lineage": lineage_edges,
              "velocity_map": velocity_map
          },
          indent=2
      )[:12000]

      prompt = f"""
  You are a Forward Deployed Engineer onboarding to a production codebase.

  Using the architecture data below, answer the following FIVE questions
  with evidence (file paths or dataset names).

  Architecture Data:
  {context}

  Questions:

  1. What is the primary data ingestion path?

  2. What are the 3-5 most critical output datasets or endpoints?

  3. What is the blast radius if the most critical module fails?

  4. Where is the business logic concentrated vs distributed?

  5. What has changed most frequently in the last 90 days?

  Provide concise bullet-point answers with evidence references.
  """

      return self._call_llm(prompt, synthesis=True)

    # ----------------------------------------------------
    # Run full semantic analysis
    # ----------------------------------------------------

    def analyze_repo(self):

      for module in self.kg.module_graph.nodes:

          if isinstance(module, str) and module.endswith(".py"):
              self.generate_purpose_statement(module)

      self.cluster_into_domains()

    # ----------------------------------------------------
    # Export results
    # ----------------------------------------------------

    def export_semantic_artifacts(self, output_dir="artifacts"):

        Path(output_dir).mkdir(exist_ok=True)

        with open(f"{output_dir}/purpose_statements.json", "w") as f:
            json.dump(self.purpose_statements, f, indent=2)

        with open(f"{output_dir}/domain_map.json", "w") as f:
            json.dump(self.domain_map, f, indent=2)

        with open(f"{output_dir}/doc_drift.json", "w") as f:
            json.dump(self.doc_drift, f, indent=2)
