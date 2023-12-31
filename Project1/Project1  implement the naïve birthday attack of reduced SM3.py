from gmssl import sm3, func
import time


def birthday_attack(collision):
    global col_list, msg_sm3, i, msg
    # 进行碰撞储存的数组
    col_list = [-1] * pow(2, collision)
    msg = int(pow(2, collision))#消息

    for i in range(msg):
        #SM3计算
        message = sm3.sm3_hash(func.bytes_to_list(bytes(str(i), encoding='utf-8')))
        msg_sm3 = int(message[0:int(collision / 4)], 16)

        if col_list[msg_sm3] == -1:
            col_list[msg_sm3] = i
            if i + 1 == msg:
                print("遍历完成，未找找到碰撞。")
                break
        else:
            break


if __name__ == '__main__':
    # 以20bit的碰撞为例
    collision = int(input("输入要碰撞的比特数(测试用20bit):"))

    start_time = time.time()
    birthday_attack(collision)
    collision_m1 = i
    collision_m2 = col_list[msg_sm3]
    collision_sm3 = hex(msg_sm3)
    end_time = time.time()

    if i + 1 != msg:
        print("找到碰撞。\n消息", collision_m1, "与消息", collision_m2, "的前", collision,
              "bit的SM3哈希值碰撞了\n碰撞部分的16进制表示为", collision_sm3)
        print("碰撞的时间为", end_time - start_time, "s")
