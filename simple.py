import numpy as np
import faiss

# 1. Define dimensions and data size
d = 64                           # Dimension of the vectors
nb = 10000                       # Number of vectors in the database
nq = 5                           # Number of query vectors

# 2. Create some random data (float32 is required by FAISS)
np.random.seed(42)
xb = np.random.random((nb, d)).astype('float32')
xq = np.random.random((nq, d)).astype('float32')

# 3. Build the index
index = faiss.IndexFlatL2(d)   # L2 distance index
print(f"Index is trained: {index.is_trained}")

# 4. Add vectors to the index
index.add(xb)                  
print(f"Total vectors in index: {index.ntotal}")

# 5. Search for the top 4 nearest neighbors (k=4)
k = 4
distances, indices = index.search(xq, k) 

# 6. Show results
print("\nSearch Results (Indices of nearest neighbors):")
print(indices)
print("\nDistances:")
print(distances)
