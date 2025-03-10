from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.basic import chunk_elements

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def parse_pdf(path_name: str):
    elements = partition_pdf(
        path_name,
        strategy="hi_res",
        include_page_breaks=True,
        infer_table_structure=True,
        languages=["chi_sim", "eng"],
        extract_image_block_types=["table"],
        encoding="utf-8",
    )
    # 删除figures文件夹

    return elements


def parse_pdf_langchain(path_name: str):

    loader = PyPDFLoader(path_name)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    new_docs = text_splitter.split_documents(documents)
    return new_docs


if __name__ == "__main__":
    dd = parse_pdf_langchain("example-docs/二、考试管理操作手册.pdf")
    print(dd)
    # dd = parse_pdf("example-docs/二、考试管理操作手册.pdf")
    # documents = chunk_elements(dd)
    # doc = []
    # for d in documents:
    #     print(d)
    #     print(d.metadata.to_dict())
    #     d = Document(
    #         page_content=d.text,
    #         metadata=d.metadata.to_dict(),
    #     )
    #     doc.append(d)
    # print(doc)
