import json
import logging
import os
from typing import Dict, Sequence

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import BaseNode, NodeWithScore, TextNode
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from src.utils.llm_utils import achat

from src.rbot_rag.gen_rewrites_from_rules import gen_rewrites_from_rules
from src.rbot_rag.my_query_fusion_retriver import FUSION_MODES, MyQueryFusionRetriever
from src.rbot_rag.my_structure_retriever import MyStructureRetriever
from src.rbot_rag.prompts import STACKOVERFLOW_QA_PROMPT


def init_docstore() -> SimpleDocumentStore:
    docstore = SimpleDocumentStore()

    def read_docs(filename: str) -> Sequence[BaseNode]:
        doc_nodes = []
        with open(filename, "r") as fin:
            for line in fin.readlines():
                obj = json.loads(line)
                myid = f'{obj["id"]}-{obj["answer_id"]}'
                doc = STACKOVERFLOW_QA_PROMPT.format(
                    title=obj["question_title"],
                    question_body=obj["question_body"],
                    answer_body=obj["answer_body"],
                )
                text_node = TextNode(text=doc, id_=myid)
                doc_nodes.append(text_node)
        return doc_nodes

    doc_nodes = read_docs("src/rbot_rewriter/rag/stackoverflow-rewrite-query-optimization.jsonl")
    docstore.add_documents(doc_nodes)
    return docstore


def rag_retrieve(
    query: str,
    schema: str,
    docstore: SimpleDocumentStore,
    embed_dim: int,
    RETRIEVER_TOP_K: int = 10,
) -> Dict:
    # initialize client
    db = chromadb.PersistentClient(path="../rag/chroma_db")

    # get collection
    stackoverflow_chroma_collection = db.get_or_create_collection("stackoverflow")

    # assign chroma as the vector_store to the context
    stackoverflow_vector_store = ChromaVectorStore(chroma_collection=stackoverflow_chroma_collection)
    stackoverflow_storage_context = StorageContext.from_defaults(vector_store=stackoverflow_vector_store)

    # load your index from stored vectors
    stackoverflow_index = VectorStoreIndex.from_vector_store(
        stackoverflow_vector_store, storage_context=stackoverflow_storage_context
    )

    stackoverflow_retriever = stackoverflow_index.as_retriever(similarity_top_k=RETRIEVER_TOP_K)

    retriever = MyQueryFusionRetriever(
        docstore=docstore,
        qa_retriever=stackoverflow_retriever,
        schema=schema,
        embed_dim=embed_dim,
        mode=FUSION_MODES.RECIPROCAL_RANK,
        similarity_top_k=RETRIEVER_TOP_K,
        use_async=False,
        verbose=True,
    )
    retriever_res = retriever.retrieve(query)
    logging.info("Retrieved Rewrite Cases: " + str(retriever_res))
    return {"retriever_res": retriever_res, "rewrites": retriever._queries}


def rag_semantics_retrieve(query: str, schema: str, docstore: SimpleDocumentStore, RETRIEVER_TOP_K: int = 10) -> Dict:
    # initialize client
    db = chromadb.PersistentClient(path="../rag/chroma_db")

    # get collection
    stackoverflow_chroma_collection = db.get_or_create_collection("stackoverflow_summary")

    # assign chroma as the vector_store to the context
    stackoverflow_vector_store = ChromaVectorStore(chroma_collection=stackoverflow_chroma_collection)
    stackoverflow_storage_context = StorageContext.from_defaults(vector_store=stackoverflow_vector_store)

    # load your index from stored vectors
    stackoverflow_index = VectorStoreIndex.from_vector_store(
        stackoverflow_vector_store, storage_context=stackoverflow_storage_context
    )

    retriever = stackoverflow_index.as_retriever(similarity_top_k=RETRIEVER_TOP_K)
    result = retriever.retrieve(query)

    node_with_scores = []
    for cur_node in result:
        cur_node_ids = eval(cur_node.metadata["references"])
        assert len(cur_node_ids) == 1
        cur_node_id = cur_node_ids[0]
        node_with_scores.append(NodeWithScore(node=docstore.get_node(cur_node_id), score=cur_node.get_score()))
    logging.info("Retrieved Rewrite Cases: " + str(node_with_scores))

    rewrites, _ = gen_rewrites_from_rules(sql=query, schema=schema, fun=achat, verbose=True)
    return {"retriever_res": node_with_scores, "rewrites": rewrites}


def rag_structure_retrieve(
    query: str,
    schema: str,
    docstore: SimpleDocumentStore,
    embed_dim: int,
    RETRIEVER_TOP_K: int = 10,
) -> Dict:
    # initialize client
    db = chromadb.PersistentClient(path="../rag/chroma_db")

    # get collection
    stackoverflow_chroma_collection = db.get_or_create_collection("stackoverflow_structure")

    # assign chroma as the vector_store to the context
    stackoverflow_vector_store = ChromaVectorStore(chroma_collection=stackoverflow_chroma_collection)
    stackoverflow_storage_context = StorageContext.from_defaults(vector_store=stackoverflow_vector_store)

    # load your index from stored vectors
    stackoverflow_index = VectorStoreIndex.from_vector_store(
        stackoverflow_vector_store, storage_context=stackoverflow_storage_context
    )

    stackoverflow_retriever = stackoverflow_index.as_retriever(similarity_top_k=RETRIEVER_TOP_K)

    retriever = MyStructureRetriever(
        docstore=docstore,
        qa_retriever=stackoverflow_retriever,
        embed_dim=embed_dim,
        schema=schema,
        mode=FUSION_MODES.RECIPROCAL_RANK,
        similarity_top_k=RETRIEVER_TOP_K,
        use_async=False,
        verbose=True,
    )
    retriever_res = retriever.retrieve(query)
    logging.info("Retrieved Rewrite Cases: " + str(retriever_res))
    return {"retriever_res": retriever_res, "rewrites": retriever._queries}
