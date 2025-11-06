import argparse
import os

try:
	import chromadb  # type: ignore
	from chromadb.utils import embedding_functions  # type: ignore
except Exception:  # pragma: no cover
	chromadb = None
	embedding_functions = None


def main():
	parser = argparse.ArgumentParser(description="RAG ingestion")
	parser.add_argument("--input", type=str, required=True, help="Directory of text files to ingest")
	parser.add_argument("--collection", type=str, required=True, help="Collection name")
	args = parser.parse_args()

	if chromadb is None:
		print("Chroma not installed; skipping ingestion. Install chromadb to enable.")
		return

	client = chromadb.Client()
	collection = client.get_or_create_collection(args.collection)

	docs = []
	ids = []
	metas = []
	for root, _, files in os.walk(args.input):
		for f in files:
			if f.lower().endswith((".md", ".txt", ".py")):
				path = os.path.join(root, f)
				with open(path, "r", errors="ignore") as fh:
					docs.append(fh.read())
					ids.append(path)
					metas.append({"path": path})

	if not docs:
		print("No documents to ingest.")
		return

	collection.add(documents=docs, ids=ids, metadatas=metas)
	print(f"Ingested {len(docs)} documents into collection '{args.collection}'.")


if __name__ == "__main__":
	main()



