import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

class Neo4jClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def init_constraints(self):
        """Creates unique constraints for nodes to prevent duplicates and speed up queries."""
        with self._driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:Finding) REQUIRE f.fingerprint IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repo) REQUIRE r.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Commit) REQUIRE c.hash IS UNIQUE")

    def ingest_finding(self, finding_data: Dict):
        """Ingests a finding and connects it to its repo, commit, and file."""
        with self._driver.session(database=os.getenv("NEO4J_DB")) as session:
            session.write_transaction(self._ingest_finding_tx, finding_data)

    @staticmethod
    def _ingest_finding_tx(tx, finding_data: Dict):
        """
        A single transaction that creates the full graph relationship for a finding.
        MERGE is used to avoid creating duplicate nodes.
        """
        query = """
        // Step 1: Find or create the Repo, Commit, and File nodes
        MERGE (repo:Repo {name: $repo_name})
        MERGE (commit:Commit {hash: $commit_hash})
        MERGE (file:File {path: $file_path})

        // Step 2: Find or create the Finding node
        MERGE (finding:Finding {fingerprint: $fingerprint})
        ON CREATE SET
            finding.check_id = $check_id,
            finding.line = $line,
            finding.message = $message,
            finding.severity = $severity,
            finding.code_snippet = $code_snippet,
            finding.status = 'open',
            finding.created_at = timestamp()
        SET finding.updated_at = timestamp()

        // Step 3: Create the relationships between all the nodes
        MERGE (repo)-[:HAS_COMMIT]->(commit)
        MERGE (commit)-[:MODIFIED_FILE]->(file)
        MERGE (file)-[:CONTAINS_FINDING]->(finding)
        """
        tx.run(query, **finding_data)

    def list_findings(self) -> List[Dict]:
        """Lists all findings with their associated repository and commit."""
        with self._driver.session(database=os.getenv("NEO4J_DB")) as session:
            query = """
            MATCH (repo:Repo)-[]->(commit:Commit)-[]->(file:File)-[]->(finding:Finding)
            RETURN finding, repo.name as repo_name, commit.hash as commit
            ORDER BY finding.severity DESC, finding.updated_at DESC
            """
            results = session.run(query)
            # Combine the finding properties with the repo_name and commit from the query
            return [
                {**record["finding"], "repo_name": record["repo_name"], "commit": record["commit"]}
                for record in results
            ]

    def get_finding(self, fingerprint: str) -> Optional[Dict]:
        """Gets a single finding with its associated repository and commit."""
        with self._driver.session(database=os.getenv("NEO_DB")) as session:
            query = """
            MATCH (repo:Repo)-[]->(commit:Commit)-[]->(file:File)-[]->(finding:Finding {fingerprint: $fp})
            RETURN finding, repo.name as repo_name, commit.hash as commit
            """
            result = session.run(query, fp=fingerprint).single()
            if result:
                return {**result["finding"], "repo_name": result["repo_name"], "commit": result["commit"]}
            return None

    def update_finding_status(self, fingerprint: str, status: str) -> Optional[Dict]:
        """Updates the status of a specific finding."""
        with self._driver.session(database=os.getenv("NEO_DB")) as session:
            query = """
            MATCH (f:Finding {fingerprint: $fp})
            SET f.status = $status, f.updated_at = timestamp()
            RETURN f
            """
            result = session.run(query, fp=fingerprint, status=status).single()
            return dict(result['f']) if result else None
