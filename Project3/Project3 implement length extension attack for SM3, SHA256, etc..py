from gmssl import sm3, func
import time
import random
import struct

#稍微修改修改python库中的sm3实现部分以完成长度扩展攻击
IV = [
    1937774191, 1226093241, 388252375, 3666478592,
    2842636476, 372324522, 3817729613, 2969243214,
]

T_j = [
    2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169,
    2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169,
    2043430169, 2043430169, 2043430169, 2043430169, 2055708042, 2055708042,
    2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042,
    2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042,
    2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042,
    2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042,
    2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042,
    2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042,
    2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042,
    2055708042, 2055708042, 2055708042, 2055708042
]


rotl = lambda x, n: ((x << n) & 0xffffffff) | ((x >> (32 - n)) & 0xffffffff)
bytes_to_list = lambda data: [i for i in data]



def sm3_ff_j(x, y, z, j):
    if 0 <= j < 16:
        ret = x ^ y ^ z
    elif 16 <= j < 64:
        ret = (x & y) | (x & z) | (y & z)
    return ret


def sm3_gg_j(x, y, z, j):
    if 0 <= j < 16:
        ret = x ^ y ^ z
    elif 16 <= j < 64:
        ret = (x & y) | ((~ x) & z)
    return ret


def sm3_p_0(x):
    return x ^ (rotl(x, 9 % 32)) ^ (rotl(x, 17 % 32))


def sm3_p_1(x):
    return x ^ (rotl(x, 15 % 32)) ^ (rotl(x, 23 % 32))


def sm3_cf(v_i, b_i):
    w = []
    for i in range(16):
        weight = 0x1000000
        data = 0
        for k in range(i * 4, (i + 1) * 4):
            data = data + b_i[k] * weight
            weight = int(weight / 0x100)
        w.append(data)

    for j in range(16, 68):
        w.append(0)
        w[j] = sm3_p_1(w[j - 16] ^ w[j - 9] ^ (rotl(w[j - 3], 15 % 32))) ^ (rotl(w[j - 13], 7 % 32)) ^ w[j - 6]
        str1 = "%08x" % w[j]
    w_1 = []
    for j in range(0, 64):
        w_1.append(0)
        w_1[j] = w[j] ^ w[j + 4]
        str1 = "%08x" % w_1[j]

    a, b, c, d, e, f, g, h = v_i

    for j in range(0, 64):
        ss_1 = rotl(
            ((rotl(a, 12 % 32)) +
             e +
             (rotl(T_j[j], j % 32))) & 0xffffffff, 7 % 32
        )
        ss_2 = ss_1 ^ (rotl(a, 12 % 32))
        tt_1 = (sm3_ff_j(a, b, c, j) + d + ss_2 + w_1[j]) & 0xffffffff
        tt_2 = (sm3_gg_j(e, f, g, j) + h + ss_1 + w[j]) & 0xffffffff
        d = c
        c = rotl(b, 9 % 32)
        b = a
        a = tt_1
        h = g
        g = rotl(f, 19 % 32)
        f = e
        e = sm3_p_0(tt_2)

        a, b, c, d, e, f, g, h = map(
            lambda x: x & 0xFFFFFFFF, [a, b, c, d, e, f, g, h])

    v_j = [a, b, c, d, e, f, g, h]
    return [v_j[i] ^ v_i[i] for i in range(8)]


#此处进行修改，把IV换为第一步hash时各寄存器的值
def sm3_hash(msg, new_IV):
    len1 = len(msg)
    reserve1 = len1 % 64
    msg.append(0x0080)
    reserve1 = reserve1 + 1
    range_end = 56
    if reserve1 > range_end:
        range_end = range_end + 64

    for i in range(reserve1, range_end):
        #填充0，直到到消息长度为56或再加整数倍的64字节
        msg.append(0x0000)

    bit_length = len1 * 8
    bit_length_str = [bit_length % 0x0100]
    for i in range(7):
        bit_length = int(bit_length / 0x0100)
        bit_length_str.append(bit_length % 0x0100)
    for i in range(8):
        msg.append(bit_length_str[7 - i])

    #此处进行修改，把加密次数减少一次
    group_count = round(len(msg) / 64) - 1

    B = []
    for i in range(0, group_count):
        #加密从第64字节开始
        B.append(msg[(i + 1) * 64:(i + 2) * 64])

    #初始值为更新后的向量值
    V = [new_IV]
    for i in range(0, group_count):
        V.append(sm3_cf(V[i], B[i]))

    y = V[i + 1]
    result = ""
    for i in y:
        result = '%s%08x' % (result, i)
    return result


#填充函数
def padding(msg):
    mlen = len(msg)
    msg.append(0x0080)
    mlen += 1
    tail = mlen % 64
    range_end = 56
    if tail > range_end:
        range_end = range_end + 64
    for i in range(tail, range_end):
        msg.append(0x0000)
    bit_len = (mlen - 1) * 8
    msg.extend([int(x) for x in struct.pack('>q', bit_len)])
    for j in range(int((mlen - 1) / 64) * 64 + (mlen - 1) % 64, len(msg)):
        global pad
        pad.append(msg[j])
        global pad_str
        pad_str += str(hex(msg[j]))
    return msg


#SM3长度扩展攻击：old_hash--secret的hash值；secret_len--secret的长度；append_m--附加的消息
def generate_guess_hash(old_hash, secret_len, append_m):
    vectors = []
    message = ""
    #分组，转换为整数
    for r in range(0, len(old_hash), 8):
        vectors.append(int(old_hash[r:r + 8], 16))

    #伪造消息
    for i in range(0, secret_len):
        message += 'a'
    message = func.bytes_to_list(bytes(message, encoding='utf-8'))
    message = padding(message) #填充
    message.extend(func.bytes_to_list(bytes(append_m, encoding='utf-8')))
    return sm3_hash(message, vectors)


if __name__ == '__main__':
    secret = str(random.random())#随机生成消息
    #附加消息
    append_m = "lalaland"
    pad_str = ""
    pad = []
    secret_hash = sm3.sm3_hash(func.bytes_to_list(bytes(secret, encoding='utf-8')))
    secret_len = len(secret)

    start_time = time.time()
    #hash2
    guess_hash = generate_guess_hash(secret_hash, secret_len, append_m)
    #new_msg为secret+padding+append_m
    new_msg = func.bytes_to_list(bytes(secret, encoding='utf-8'))
    new_msg.extend(pad)
    new_msg.extend(func.bytes_to_list(bytes(append_m, encoding='utf-8')))
    new_msg_str = secret + pad_str + append_m
    new_hash = sm3.sm3_hash(new_msg)  # hash3
    end_time = time.time()

    print("原消息：", secret)
    print("原消息的长度：", len(secret))
    print("原消息的hash值（hash1）：" + secret_hash)
    print("附加消息：", append_m, "\n")
    print("伪造消息的hash值（hash2）：", guess_hash)
    print("正确消息（secret+padding+append_m）：", new_msg_str)
    print("正确消息的hash值（hash3）：", new_hash)

    if new_hash == guess_hash:
        print("\n成功")
    else:
        print("\n失败")

    print("所用时间为：", end_time - start_time, "s")

