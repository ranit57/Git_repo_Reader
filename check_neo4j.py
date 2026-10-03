from neo4j import GraphDatabase

uri = 'neo4j://127.0.0.1:7687'
username = 'neo4j'
password = 'MMita@123'

driver = GraphDatabase.driver(uri, auth=(username, password))

with driver.session() as session:
    # Check nodes
    result = session.run('MATCH (n) RETURN labels(n) as labels, count(*) as count')
    print('=== Nodes ===')
    for record in result:
        print(f'  {record["labels"]}: {record["count"]}')
    
    # Check relationships
    result = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(*) as count')
    print('\n=== Relationships ===')
    for record in result:
        print(f'  {record["type"]}: {record["count"]}')
    
    # Sample some data
    result = session.run('MATCH (n) RETURN n LIMIT 10')
    print('\n=== Sample Nodes ===')
    for record in result:
        node = record['n']
        print(f'  Labels: {list(node.labels)}, Props: {dict(node)}')

driver.close()