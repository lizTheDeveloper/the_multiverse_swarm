import argparse
from neo4j import GraphDatabase

class LangGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def execute_query(self, query):
        with self.driver.session() as session:
            result = session.run(query)
            return [record for record in result]

def main():
    parser = argparse.ArgumentParser(description="LangGraph tool for Neo4j and Cypher")
    parser.add_argument("query", type=str, help="Cypher query to execute")
    parser.add_argument("--uri", type=str, default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", type=str, default="neo4j", help="Neo4j user")
    parser.add_argument("--password", type=str, default="test", help="Neo4j password")

    args = parser.parse_args()

    langgraph = LangGraph(args.uri, args.user, args.password)
    try:
        results = langgraph.execute_query(args.query)
        for record in results:
            print(record)
    finally:
        langgraph.close()

if __name__ == "__main__":
    main()
