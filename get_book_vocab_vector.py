# from sklearn.metrics.pairwise import cosine_similarity
from concurrent import futures
from pathlib import Path

import numpy as np
import pandas as pd
import spacy

nlp = spacy.load("en_core_web_trf", disable=["parser", "ner"])
word_freq_df = pd.read_csv("bnc_coca_word_freq.csv")


def process_tokens(doc):
    return [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and token.is_alpha
        and len(token.text) > 2
        and token.pos_ != "PROPN"
    ]


def df_to_normalized_vector(df, max_k=30):
    """
    将词汇分布DataFrame转为归一化向量
    :param df: 输入DataFrame (index='1k','2k'...; columns='count')
    :param max_k: 最大频率区间 (默认到30k)
    :return: 归一化向量 (numpy array)
    """
    # 创建全0向量 (长度=max_k)
    vector = np.zeros(max_k)

    # 填充有效数据
    for label, count in df["count"].items():
        k_val = int(label.replace("k", ""))  # 提取数字部分
        if 1 <= k_val <= max_k:
            vector[k_val - 1] = count  # 1k对应索引0, 2k对应索引1...

    # 归一化处理
    return vector / vector.sum()


def get_word_freq_ranking(file_path):
    doc = nlp(Path(file_path).read_text())
    tokens = process_tokens(doc)
    tokens_df = pd.DataFrame({"word": tokens})
    word_counts = tokens_df["word"].value_counts().reset_index()
    word_counts.columns = ["word", "count"]  # 重命名列
    word_counts = word_counts.merge(word_freq_df, on="word")
    return (
        word_counts.groupby("label")
        .agg({"label": "count"})
        .sort_index(key=lambda x: x.str.replace("k", "").astype(int))
        .rename(columns={"label": "count"})
    )


books = list(Path("book_sentence").glob("*.txt"))


def get_book_vocab_vector(book):
    result = df_to_normalized_vector(get_word_freq_ranking(book))
    print(book.stem)
    return result


if __name__ == "__main__":
    with futures.ProcessPoolExecutor(4) as executor:
        results = executor.map(get_book_vocab_vector, books)

    book_vocab_vectors = pd.DataFrame(
        data=dict(book=[i.stem for i in books], vector=list(results)),
        columns=pd.Index(["book", "vector"]),
    )
    book_vocab_vectors.to_csv("book_vocab_vectors.csv", index=False)
