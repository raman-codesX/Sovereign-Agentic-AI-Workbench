import faiss

def vector_store(embedd):
    dimension = embedd.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embedd)

    return index
