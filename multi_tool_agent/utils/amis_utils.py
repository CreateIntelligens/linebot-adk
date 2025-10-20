# =============================================================================
# 阿美族語詞典工具函數
# 從阿美族語詞典中隨機選取單字並提供詳細解釋
# 包含定義、同義詞和例句等資訊
# =============================================================================

import os
import json
import random
import logging

logger = logging.getLogger(__name__)


async def get_amis_word_of_the_day() -> dict:
    """
    從阿美族語詞典中隨機選取一個單字並回傳其定義。
    """
    try:
        # 讀取 amis.json 檔案
        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'asset/amis.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            word_list = json.load(f)

        # 隨機選取一個單字
        word_data = random.choice(word_list)

        amis_word = word_data.get("title", "N/A")

        # 從 heteronyms 中獲取所有定義、同義詞和例句
        definitions_list = []
        all_synonyms = []
        all_examples = []

        heteronyms = word_data.get("heteronyms", [])
        for heteronym in heteronyms:
            definitions = heteronym.get("definitions", [])
            for def_item in definitions:
                # 獲取定義（可能包含英文和中文）
                def_text = def_item.get("def", "")

                # 提取中文部分
                chinese_def = _extract_chinese_definition(def_text)
                if chinese_def:
                    definitions_list.append(chinese_def)

                # 收集同義詞
                synonyms = def_item.get("synonyms", [])
                all_synonyms.extend(synonyms)

                # 收集例句
                examples = def_item.get("example", [])
                all_examples.extend(examples)

        # 格式化報告
        if definitions_list:
            if len(definitions_list) == 1:
                report = f"📖 阿美語每日一字：{amis_word}\n\n📜 中文意思：{definitions_list[0]}"
            else:
                # 多個定義，用編號顯示
                defs_text = "\n".join([f"{i+1}. {def_text}" for i, def_text in enumerate(definitions_list)])
                report = f"📖 阿美語每日一字：{amis_word}\n\n📜 中文意思：\n{defs_text}"
        else:
            report = f"📖 阿美語每日一字：{amis_word}\n\n📜 中文意思：無定義資料"

        # 處理同義詞（去重並清理格式）
        if all_synonyms:
            cleaned_synonyms = _clean_synonyms(all_synonyms, word_list)
            if cleaned_synonyms:
                synonym_text = "、".join(cleaned_synonyms)
                report += f"\n\n🔗 同義詞：{synonym_text}"

        # 處理例句
        if all_examples:
            cleaned_examples = _clean_examples(all_examples)
            if cleaned_examples:
                if len(cleaned_examples) == 1:
                    report += f"\n\n💬 例句：{cleaned_examples[0]}"
                else:
                    examples_text = "\n".join([f"{i+1}. {example}" for i, example in enumerate(cleaned_examples)])
                    report += f"\n\n💬 例句：\n{examples_text}"

        return {
            "status": "success",
            "report": report
        }
    except FileNotFoundError:
        logger.error("amis.json 檔案不存在")
        return {
            "status": "error",
            "error_message": "找不到阿美族語詞典檔案。"
        }
    except Exception as e:
        logger.error(f"處理阿美族語每日一字時發生錯誤: {e}")
        return {
            "status": "error",
            "error_message": f"處理每日一字時發生錯誤：{str(e)}"
        }


def _extract_chinese_definition(def_text):
    """提取定義中的中文部分"""
    if not def_text:
        return ""

    # 方法1: 尋找 * 分隔符
    if "*" in def_text:
        parts = def_text.split("*")
        return parts[-1].strip() if len(parts) > 1 else def_text

    # 方法2: 尋找第一個中文字符開始的部分
    words = def_text.split()
    chinese_start = -1
    for i, word in enumerate(words):
        if any('\u4e00' <= char <= '\u9fff' for char in word):
            chinese_start = i
            break

    if chinese_start != -1:
        return " ".join(words[chinese_start:])

    # 方法3: 如果都沒有，返回原文
    return def_text


def _clean_synonyms(synonyms, word_list):
    """清理同義詞並驗證是否存在"""
    cleaned = []
    for synonym in synonyms:
        if synonym:
            # 移除特殊符號（如 `karahay~ -> karahay）
            clean_word = synonym.strip('`~')

            # 檢查是否在詞典中存在
            if _word_exists_in_dict(clean_word, word_list):
                # 顯示原始格式
                cleaned.append(synonym)
            else:
                # 如果清理後的詞存在，顯示清理後的
                if _word_exists_in_dict(synonym, word_list):
                    cleaned.append(synonym)
                else:
                    # 即使不存在也保留，可能是引用格式
                    cleaned.append(synonym)

    # 去重
    return list(dict.fromkeys(cleaned))


def _word_exists_in_dict(word, word_list):
    """檢查單字是否存在於詞典中"""
    for item in word_list:
        if item.get("title", "").lower() == word.lower():
            return True
    return False


def _clean_examples(examples):
    """清理和格式化例句"""
    cleaned = []
    for example in examples:
        if example and example.strip():
            # 移除開頭的空格
            clean_example = example.strip()

            # 分析例句結構：通常是 阿美語 + 英文 + 中文
            # 例如：`pasamo~ `to~ `sowal~ give the gist of the matter in words 說要點，即興略說事情的要旨
            formatted_example = _format_example(clean_example)

            cleaned.append(formatted_example)

    # 去重但保持順序
    return list(dict.fromkeys(cleaned))


def _format_example(example):
    """格式化單個例句，添加適當的換行"""
    # 找尋英文和中文的分界點
    words = example.split()

    # 尋找第一個中文字符的位置
    chinese_start = -1
    for i, word in enumerate(words):
        if any('\u4e00' <= char <= '\u9fff' for char in word):
            chinese_start = i
            break

    if chinese_start > 0:
        # 分離阿美語+英文 和 中文部分
        amis_english = " ".join(words[:chinese_start])
        chinese = " ".join(words[chinese_start:])

        # 格式化：阿美語+英文 換行 中文
        return f"{amis_english}\n→ {chinese}"
    else:
        # 如果沒有中文或格式不標準，直接返回
        return example