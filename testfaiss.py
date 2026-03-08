import faiss
import numpy as np

# Create a simple index for 128-dimensional vectors
index = faiss.IndexFlatL2(128) 
print(index.is_trained)  # Should output: True
