"""Step 08. Normalization.

The trap this file exists to avoid: normalize BEFORE scoring, and normalize labels and
predictions identically. Do it one-sided and skills F1 measures the quality of this synonym
table rather than the extractor — and it drifts every time an entry is added.

So `evals/` imports `normalize_skills` from here and applies it to both sides. There is one
table, not two.
"""

SKILL_SYNONYMS = {
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",
    "node": "node.js",
    "nodejs": "node.js",
    "nextjs": "next.js",
    "next": "next.js",
    "py": "python",
    "gcp": "google cloud",
    "tf": "terraform",
    "es": "elasticsearch",
    "rails": "ruby on rails",
    "ror": "ruby on rails",
    "postgres sql": "postgresql",
}

# Display casing. Everything is compared lowercase; this is only for what lands in Parquet.
DISPLAY = {
    "postgresql": "PostgreSQL", "kubernetes": "Kubernetes", "javascript": "JavaScript",
    "typescript": "TypeScript", "python": "Python", "go": "Go", "rust": "Rust",
    "java": "Java", "ruby": "Ruby", "react": "React", "next.js": "Next.js",
    "node.js": "Node.js", "django": "Django", "fastapi": "FastAPI", "terraform": "Terraform",
    "docker": "Docker", "aws": "AWS", "azure": "Azure", "google cloud": "Google Cloud",
    "kafka": "Kafka", "redis": "Redis", "mysql": "MySQL", "mongodb": "MongoDB",
    "elasticsearch": "Elasticsearch", "spark": "Spark", "airflow": "Airflow", "dbt": "dbt",
    "snowflake": "Snowflake", "databricks": "Databricks", "graphql": "GraphQL",
    "pytorch": "PyTorch", "tensorflow": "TensorFlow", "ruby on rails": "Ruby on Rails",
    "llm": "LLM", "rag": "RAG", "c++": "C++", "scala": "Scala", "kotlin": "Kotlin",
    "swift": "Swift", "vue": "Vue", "angular": "Angular", "svelte": "Svelte",
    "flask": "Flask", "ansible": "Ansible", "grpc": "gRPC", "rabbitmq": "RabbitMQ",
}

# Everything is stored as an annual figure so the columns are comparable. 2080 = 40h x 52w.
HOURS_PER_YEAR = 2080
MONTHS_PER_YEAR = 12


def normalize_skills(skills):
    """Canonical, deduplicated, sorted. Applied to labels and predictions identically."""
    out = set()
    for s in skills or []:
        key = s.strip().lower()
        out.add(SKILL_SYNONYMS.get(key, key))
    return sorted(out)


def display_skills(skills):
    return [DISPLAY.get(s, s) for s in normalize_skills(skills)]


def to_annual(amount, period):
    """Hourly and monthly figures become annual so the salary column means one thing.

    Without this an hourly rate sits in the same column as a salary and every downstream
    number — trends, filters, the matcher — is quietly wrong.
    """
    if amount is None or period is None:
        return None
    if period == "year":
        return amount
    if period == "month":
        return amount * MONTHS_PER_YEAR
    if period == "hour":
        return amount * HOURS_PER_YEAR
    return None


def normalize(extraction):
    """Returns a copy with skills canonicalised and salary converted to annual."""
    data = extraction.model_dump()
    data["skills"] = normalize_skills(data.get("skills"))
    period = data.get("salary_period")
    if period and period != "year":
        data["salary_min"] = to_annual(data.get("salary_min"), period)
        data["salary_max"] = to_annual(data.get("salary_max"), period)
        # Keep the original period so nothing pretends the post said "per year".
    return type(extraction)(**data)
