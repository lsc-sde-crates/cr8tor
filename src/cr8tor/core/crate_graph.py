from rdflib import Graph
from rdflib.query import Result
import sys
from pathlib import Path


class ROCrateGraph:
    def __init__(
        self, rocrate_metadata_path: Path, base_uri="https://lscsde.org/crate/"
    ):
        """Load ROCrate graph"""
        self.graph = Graph()

        rocrate_metadata_path = Path(rocrate_metadata_path)

        with open(
            rocrate_metadata_path.joinpath("data", "ro-crate-metadata.json"),
            "r",
            encoding="utf-8",
        ) as f:
            ro_crate_jsonld = f.read()

        self.graph.parse(data=ro_crate_jsonld, format="json-ld", publicID=base_uri)
        print("\n=== DEBUG: RDF Triples ===")
        for stmt in self.graph:
            print(stmt)

    def run_query(self, sparql_query) -> Result:
        """Execute SPARQL query on the graph."""
        triples = self.graph.query(sparql_query)
        return triples

    def is_created(self) -> bool:
        """Check if 'create' action has been successfully run on project"""
        query = """
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          SELECT (IF(COUNT(?action) > 0, "True", "False") AS ?result) WHERE {
            ?action rdf:type schema:CreateAction ;
                    schema:name 'Create LSC Project Action';
                    schema:actionStatus 'CompletedActionStatus' .
          }
        """
        result = self.run_query(query)
        for row in result:
            return row.result
        return False

    def is_validated(self) -> bool:
        """Check if project has been validated successfully"""
        query = """
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          SELECT (IF(COUNT(?action) > 0, "True", "False") AS ?result) WHERE {
            ?action rdf:type schema:AssessAction ;
                    schema:name 'Validate LSC Project Action';
                    schema:actionStatus 'CompletedActionStatus' .
          }
        """
        result = self.run_query(query)
        for row in result:
            return row.result
        return False

    def is_signed(self) -> bool:
        """Check if project has been signed successfully"""
        query = """
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          SELECT (IF(COUNT(?action) > 0, "True", "False") AS ?result) WHERE {
            ?action rdf:type schema:AssessAction ;
                    schema:name 'IG Sign-Off Project Action';
                    schema:actionStatus 'CompletedActionStatus' .
          }
        """
        result = self.run_query(query)
        for row in result:
            return row.result
        return False

    def is_staged(self) -> bool:
        """Check if project has been staged successfully"""
        query = """
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          SELECT (IF(COUNT(?action) > 0, "True", "False") AS ?result) WHERE {
            ?action rdf:type schema:AssessAction ;
                    schema:name 'Stage Data Transfer Action';
                    schema:actionStatus 'CompletedActionStatus' .
          }
        """
        result = self.run_query(query)
        for row in result:
            return row.result
        return False

    def get_validate_status(self) -> bool:
        """Get validation status of project"""
        query = """
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          SELECT ?status WHERE {
            ?action rdf:type schema:AssessAction ;
                    schema:name 'Validate LSC Project Action';
                    schema:actionStatus ?status .
          }
        """
        result = self.run_query(query)
        for row in result:
            return row.status
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crate_graph.py <path_to_rocrate_metadata.json>")
        sys.exit(1)

    rocrate_metadata_path = sys.argv[1]
    graph = ROCrateGraph(rocrate_metadata_path)

    print("\n=== Running get_validate_status() test ===")
    created = graph.get_validate_status()
    print(f"\nResult: get_validate_status() -> {created}")
