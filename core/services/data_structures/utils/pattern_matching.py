def compute_kmp_fail(pattern):
    """计算模式的失败函数"""
    m = len(pattern)
    fail = [0] * m
    j = 1
    k = 0
    while j < m:
        if pattern[j] == pattern[k]:
            fail[j] = k + 1
            j += 1
            k += 1
        elif k > 0:
            k = fail[k - 1]
        else:
            j += 1
    return fail


def find_kmp(pattern, text):
    """
    从 text 中找到第一个完全匹配 pattern 的位置
    :param pattern: 寻找的模式
    :param text: 被查找的对象
    :return: text 的索引位置, 若失败返回 -1
    """
    m, n = len(pattern), len(text)
    if m == 0:
        return 0

    fail = compute_kmp_fail(pattern)
    j = 0
    k = 0
    while j < n:
        if text[j] == pattern[k]:
            if k == m - 1:
                return j - m + 1
            j += 1
            k += 1
        elif k > 0:
            k = fail[k - 1]
        else:
            j += 1
    return -1


def find_all_kmp(pattern, text):
    """
    从 text 中找到所有完全匹配 pattern 的位置
    :param pattern: 寻找的模式
    :param text: 被查找的对象
    :return: text 的索引位置, 若失败返回 -1
    """
    m, n = len(pattern), len(text)
    if m == 0:
        return 0

    fail = compute_kmp_fail(pattern)
    j = 0
    k = 0
    match = []
    while j < n:
        if text[j] == pattern[k]:
            if k == m - 1:
                match.append(j - m + 1)
                # 继续搜索下一个可能的匹配
                k = fail[k]
                j += 1
            else:
                j += 1
                k += 1
        elif k > 0:
            k = fail[k - 1]
        else:
            j += 1
    return match


def find_all_from_list(pattern: str, texts, sep="*"):
    """
    对于字符串列表 text_list 返回所有包含 pattern 的索引
    :param pattern: 匹配模式
    :param texts: 字符串列表 ["text1", "text2", ...] or "text1*text2*...*"
    :param sep: 特殊分割符, 默认为 "*" , 要求一定不在 text_list 所含有的字符里
    :return: text_list 包含 pattern 的索引 [idx1, idx2, ...]
    """
    m = len(pattern)
    if isinstance(texts, list):
        text = sep.join(texts) + sep
        if m == 0:  # 简单情况, 全部匹配
            return [i for i in range(len(texts))]
    else:
        text = texts
        if m == 0:  # 简单情况, 全部匹配
            all_length = len(text.split(sep)) - 1
            return [i for i in range(all_length)]

    n = len(text)

    fail = compute_kmp_fail(pattern)  # 失败函数
    k, j = 0, 0  # k 在 pattern 上遍历, j 在 text 上遍历

    match = []  # 记录索引
    texts_num = 0  # 记录目前位于 text_list 的第几段

    # 开始匹配
    while j < n:  # j 在 text 上遍历
        if text[j] == sep:
            texts_num += 1  # 检索到了 sep 说明没有匹配进入下一段

        # 开始逐个字符匹配
        if text[j] == pattern[k]:  # 当前字符匹配成功
            if k == m - 1:  # 完全匹配, 加入结果集
                match.append(texts_num)
                # 直接去往下一段
                texts_num += 1
                while text[j] != sep:  # 不用比较
                    j += 1
                j += 1  # text 中下一段第一个字符
                k = 0  # 从 pattern 第一个字符开始
            else:  # 继续寻找
                j += 1
                k += 1
        elif k > 0:  # 之前存在匹配项, 失败函数返回下一步索引位置
            k = fail[k - 1]
        else:  # 当前字符未匹配, j 后移
            j += 1
    return match


if __name__ == '__main__':
    text = "This is a sentence, the target is to find the pattern which is matching"
    pattern = "th"

    match_index = find_kmp(pattern, text)
    print(text[match_index:])

    all_match = find_all_kmp(pattern, text.lower())
    for match in all_match:
        print(text[match:])

    print("=" * 100)
    pattern = "abc"
    text_list = ["abc421", "a12abc", "39akbc", "3ma3b1abc", "a31bc", "1ac1abc"]
    all_match_index = find_all_from_list(pattern, text_list)
    print(all_match_index)
    for match_index in all_match_index:
        print(text_list[match_index])

    print("=" * 100)
    pattern = "abc"
    text_list = ["abc421", "a12abc", "39akbc", "3ma3b1abc", "a31bc", "1ac1abc"]
    texts = "*".join(text_list) + "*"
    all_match_index = find_all_from_list(pattern, texts)
    print(all_match_index)
    for match_index in all_match_index:
        print(text_list[match_index])
