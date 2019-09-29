# -*- coding: utf-8 -*-
# Author: ZaneYork
import csv
import sys
import os
import binascii

# 大小端切换（True或False）
ENDIAN_SWAP = True
# 规则文件名(CSV)
RULE = './rule.csv'
# 原文件名
SRC = './1.exe'
# 目标文件名
DEST = './2.exe'
# 是否保留首尾空格(True或False,默认不开启,每个文本后自动补00 00)
SPACE_RESERVE = False
# 是否在只有一个候选时直接确认
QUICK_COMFIRM = True
# CSV编码
CSV_ENCODING = 'gbk'

def swap_endian(bytes, endian = True):
    if endian:
        for i in range(0, len(bytes) - 1, 2):
            tmp = bytes[i]
            bytes[i] = bytes[i + 1]
            bytes[i + 1] = tmp
        return bytes

def to_unicode(bytes):
    return swap_endian(bytearray(binascii.unhexlify("".join([hex(ord(x)).replace('0x', '').zfill(4) for x in bytes]))), ENDIAN_SWAP)

def forcedecode(context,method = 'utf-8'):   
    pos = 0
    maxpos = len(context)
    if maxpos == 0:
        print('数据长度为0')
        return None
    result = ''
    while pos < maxpos:
        try:
            ##单个数据解码
            str1 = context[pos:pos+1]
            result += str1.decode(method)
            pos += 1
        except:
            try:
                ##两个数据解码
                str2 = context[pos:pos+2]
                result += str2.decode(method)
                pos += 2
            except:
                try:
                    ##三个数据解码
                    str3 = context[pos:pos+3]
                    result += str3.decode(method)
                    pos += 3
                except:
                    try:
                        ##解码失败，将数据转换为字符串
                        result += context[pos:pos+1].hex()
                        pos += 1
                    except:
                        (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
                        print("forcedecode: ", ErrorValue)
                        break
    return result

# 对子串加以预处理，找到匹配失败时子串回退的位置
def preprocess(patter):
    length = len(patter)
    p = handlerList(length)
    j = -1
    p[0] = j
    for i in range(1, length):
        j = p[i - 1]
        while j >= 0 and patter[i] != patter[j+1]:
            j = p[j]

        if patter[i] == patter[j+1]:  # 含有重复字符时，回退的位置+1
            p[i] = j + 1
        else:
            p[i] = -1

    return p

# 初始化一个元组
def handlerList(len, default=0):
    if len <= 0:
        return
    p = []
    for i in range(len):
        p.append(default)
    return p

def kmp(value, pattern, expect, offsetEnd):
    srcSize = len(value) if offsetEnd > len(value) else offsetEnd
    subSize = len(pattern)
    p = preprocess(pattern)
    tIndex, pIndex, total = expect, 0, 0
    locations = []
    while tIndex < srcSize and pIndex < subSize:  # 找到合适的回退位置
        if (value[tIndex] == pattern[pIndex]):
            tIndex += 1
            pIndex += 1
        elif pIndex == 0:
            tIndex += 1
        else:
            pIndex = p[pIndex - 1] + 1

        if pIndex == subSize:  # 输出匹配结果，并且让比较继续下去
            pIndex = 0
            total += 1
            if expect == tIndex - subSize:
                return [tIndex - subSize]
            locations.append(tIndex - subSize)
    return locations


def select_context(bytes, positions, baseStr, length, lastSelect = 1):
    if QUICK_COMFIRM and len(positions) == 1:
        return positions[0], 1
    os.system('cls')
    searchStr = forcedecode(baseStr)
    print("find :", searchStr)
    for i, position in enumerate(positions):
        try:
            print(i+1, ":", hex(position))
            textA = forcedecode(bytes[position - length: position])
            textB = forcedecode(bytes[position: position + len(baseStr)])
            textC = forcedecode(bytes[position + len(baseStr): position + len(baseStr) + length])
            text = "%s\033[0;31;40m%s\033[0m%s" % (textA, textB, textC)
            print(text)
        except:
            pass
    while True:
        message = input("please select (default:%d)" % (lastSelect))
        try:
            if message == '':
                return positions[lastSelect - 1], lastSelect
            return positions[int(message) - 1], int(message)
        except:
            pass
    

rules = []
with open(RULE, "r", encoding=CSV_ENCODING) as csvfile:
    reader = csv.reader(csvfile)
    for line in reader:
        rules.append(line)

with open(SRC, 'rb')as fp:
    origin = bytearray(fp.read())

def to_offset_config(offset, offsetBegin, offsetEnd):
    if offsetEnd == 0xffffffff:
        return hex(offset)
    else:
        return hex(offset) + '-' + hex(offsetEnd) + '-' + hex(offsetBegin)

for rule in rules:
    if len(rule) < 2:
        continue
    rule_src = to_unicode(rule[0])
    if not SPACE_RESERVE:
        rule_dest = to_unicode(rule[1].strip())
    else:
        rule_dest = to_unicode(rule[1])

    offset = 0
    offsetBegin = 0
    offsetEnd = 0xffffffff
    lastSelect = 1
    if len(rule) >= 3:
        try:
            offsetRange = rule[2].split('-')
            offsetBegin = offset = int(offsetRange[0], 16)
            if len(offsetRange) >= 2:
                offsetEnd = int(offsetRange[1], 16)
            if len(offsetRange) >= 3:
                offsetBegin = int(offsetRange[2], 16)
        except:
            print(offset,offsetBegin,offsetEnd)
            os.system("pause")
            pass
    if len(rule) >= 4:
        try:
            lastSelect = int(rule[3])
        except:
            pass
    locations = kmp(origin, rule_src, offset, offsetEnd)
    if len(locations) == 1 and locations[0] == offset:
        pass
    elif len(locations) != 0:
        if offsetEnd == 0xffffffff:
            locations = kmp(origin, rule_src, 0, len(origin))
        else:
            locations = kmp(origin, rule_src, offsetBegin, offsetEnd)
        offset, lastSelect = select_context(origin, locations, rule_src, 32, lastSelect)
    else:
        print("WRARNING: Dest String is not exist!", rule[0],"->",rule[1])
        os.system('pause')
        continue
    if len(rule) < 3:
        rule.append(to_offset_config(offset, offsetBegin, offsetEnd))
    else:
        rule[2] = to_offset_config(offset, offsetBegin, offsetEnd)
    if len(rule) < 4:
        rule.append(lastSelect)
    else:
        rule[3] = lastSelect
    while len(rule_src) > len(rule_dest):
        rule_dest.append(0)
    if len(rule_dest) > len(rule_src):
        print("WRARNING: Dest String is too large!", rule[0],"->",rule[1])
        os.system('pause')
    for i in range(0, len(rule_dest)):
        origin[offset + i] = rule_dest[i]

with open(DEST, 'wb')as fp:
    fp.write(origin)

with open(RULE, 'w', newline='',encoding=CSV_ENCODING) as f:
    writer=csv.writer(f)
    writer.writerows(rules)
    f.close()
