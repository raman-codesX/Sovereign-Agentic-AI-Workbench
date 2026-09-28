def search(index, query_embedding, chunks, k=3):
    distance, indices = index.search(query_embedding, k)

    results = [chunks[i] for i in indices[0]]

    return results