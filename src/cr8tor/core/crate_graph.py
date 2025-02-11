from rdflib import Graph
from rdflib.query import Result


class ROCrateGraph:
    def __init__(self, rocrate_metadata_path, base_uri="https://lscsde.org/crate/"):
        """Load ROCrate graph"""
        self.graph = Graph()

        with open(rocrate_metadata_path, "r", encoding="utf-8") as f:
            ro_crate_jsonld = f.read()

        self.graph.parse(data=ro_crate_jsonld, format="json-ld", publicID=base_uri)
        # print("\n=== DEBUG: RDF Triples ===")
        # for stmt in self.graph:
        #   print(stmt)

    def run_query(self, sparql_query) -> Result:
        """Execute SPARQL query on the graph."""
        triples = self.graph.query(sparql_query)
        return triples

    def is_validated(self) -> bool:
        """Verify if crate has been validated"""
        query = """
          PREFIX schema: <http://schema.org/>
          PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
          SELECT ?action ?name WHERE {
            ?action rdf:type schema:AssessAction ;
                    schema:name ?name .
          }
        """
        result = self.run_query(query)
        [print(str(row.name)) for row in result]

        #
        # Add condition logic
        #
        return True
