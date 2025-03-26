from rdflib import Graph
from rdflib.query import Result
import sys
from pathlib import Path
import cr8tor.core.schema as schemas


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

    def is_project_action_complete(
        self,
        command_type: schemas.Cr8torCommandType,
        action_type: schemas.RoCrateActionType,
        project_id: str,
    ) -> bool:
        """Check if a project 'action' has completed successfully"""

        query = f"""
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          PREFIX cr8tor: <https://lscsde.org/crate/>
          SELECT (IF(COUNT(*) > 0, 'True', 'False') AS ?result) WHERE {{
            cr8tor:{command_type}-{project_id} rdf:type schema:{action_type} ;
                    schema:actionStatus 'CompletedActionStatus' .
          }}
        """
        result = self.run_query(query)
        for row in result:
            return str(row.result.value).strip().lower() == "true"
        return False

    def get_validate_status(self) -> bool:
        """Get validation status of project"""
        query = """
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          SELECT ?status WHERE {
            ?action rdf:type schema:AssessAction ;
                    schema:name 'Validate Data Project Action';
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

    print("\n=== Running is_created() test ===")
    created = graph.is_created("030838cb-24cb-44b8-9385-51bc6ea7160a")
    print(f"\nResult: is_created() -> {created}")
