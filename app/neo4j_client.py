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

    def verify_connection(self):
        with self._driver.session() as session:
            result = session.run("RETURN 1")
            return result.single()[0] == 1

    def init_constraints(self):
        with self._driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:Finding) REQUIRE f.fingerprint IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repo) REQUIRE r.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Commit) REQUIRE c.hash IS UNIQUE")

    def ingest_finding(self, finding_data: Dict):
        with self._driver.session(database=os.getenv("NEO4J_DB")) as session:
            session.write_transaction(self._ingest_finding_tx, finding_data)

    @staticmethod
    def _ingest_finding_tx(tx, finding_data: Dict):
        query = """
        MERGE (repo:Repo {name: $repo_name})
        MERGE (commit:Commit {hash: $commit_hash})
        MERGE (file:File {path: $file_path})
        MERGE (finding:Finding {fingerprint: $fingerprint})
        ON CREATE SET
            finding.check_id = $check_id,
            finding.line = $line,
            finding.message = $message,
            finding.severity = $severity,
            finding.code_snippet = $code_snippet,
            finding.status = 'open',
            finding.created_at = timestamp(),
            finding.updated_at = timestamp()
        ON MATCH SET
            finding.updated_at = timestamp()

        MERGE (repo)-[:HAS_COMMIT]->(commit)
        MERGE (commit)-[:MODIFIED_FILE]->(file)
        MERGE (file)-[:CONTAINS_FINDING]->(finding)
        """
        tx.run(query, **finding_data)

    def list_findings(self) -> List[Dict]:
        with self._driver.session(database=os.getenv("NEO4J_DB")) as session:
            query = """
            MATCH (repo:Repo)-[]->(commit:Commit)-[]->(file:File)-[]->(finding:Finding)
            RETURN finding, repo.name as repo_name, commit.hash as commit
            ORDER BY finding.severity DESC, finding.updated_at DESC
            """
            results = session.run(query)
            return [
                {**record["finding"], "repo_name": record["repo_name"], "commit": record["commit"]}
                for record in results
            ]

    def get_finding(self, fingerprint: str) -> Optional[Dict]:
        with self._driver.session(database=os.getenv("NEO4J_DB")) as session:
            query = """
            MATCH (repo:Repo)-[]->(commit:Commit)-[]->(file:File)-[]->(finding:Finding {fingerprint: $fp})
            RETURN finding, repo.name as repo_name, commit.hash as commit
            """
            result = session.run(query, fp=fingerprint).single()
            if result:
                return {**result["finding"], "repo_name": result["repo_name"], "commit": result["commit"]}
            return None

    def update_finding_status(self, fingerprint: str, status: str) -> Optional[Dict]:
        with self._driver.session(database=os.getenv("NEO4J_DB")) as session:
            query = """
            MATCH (f:Finding {fingerprint: $fp})
            SET f.status = $status, f.updated_at = timestamp()
            RETURN f
            """
            result = session.run(query, fp=fingerprint, status=status).single()
            return result["f"] if result else None
