from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex


class PrpCrypt(object):

    def __init__(self, key, iv):
        #将字符串转换成bytes，‘’变为b‘’
        if(type(key) == bytes):
            self.key = key
        elif(type(key) == str):
            self.key = key.encode('utf-8')

        if(type(iv) == bytes):
            self.iv = iv
        elif(type(iv) == str):
            self.iv = iv.encode('utf-8')

        self.mode = AES.MODE_CBC

    # 加密函数，如果text不足16位就用空格补足为16位，
    # 如果大于16当时不是16的倍数，那就补足为16的倍数。
    def encrypt(self, text):
        text = text.encode('utf-8')
        cryptor = AES.new(self.key, self.mode, self.iv)
        # 这里密钥key 长度必须为16（AES-128）,
        # 24（AES-192）,或者32 （AES-256）Bytes 长度
        # 目前AES-128 足够目前使用
        length = 16
        count = len(text)
        if count < length:
            add = (length - count)
            # \0 backspace
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        elif count > length:
            add = (length - (count % length))
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        print("text is", text)
        self.ciphertext = cryptor.encrypt(text)
        #b'\x84K2\x16\x14\x83\xcf\xe3,\xb9\xc4\xb9\xdf(^\xe7'
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        # 返回值为将字节串结果转换成字符串（\x后两位保持原样，其余的按照ascii表专程数字）
        # b'844b32161483cfe32cb9c4b9df285ee7'
        return b2a_hex(self.ciphertext)

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        #print("text is", text)
        cryptor = AES.new(self.key, self.mode, self.iv)
        #如果是字符串要先转换成字节串，若是字节串则直接解码
        # plain_text = cryptor.decrypt(a2b_hex(text))
        result = cryptor.decrypt(text) # reslut is bytes
        # 结果为32位，我们要用的只是前16位
        # for b in result[0:16]:
        #     print(str(b))

        #return bytes.decode(plain_text).rstrip('\0')
        return result


if __name__ == '__main__':
    #keys中每个数字类型为int
    keys = [52, 53, 99, 52, 56, 99, 99, 101, 50, 101, 50, 100, 55, 102, 98, 100]
    #[4,5,c,4,8,c,c,e,2,e,2,d,7,f,b,d]
    str_key = ""
    for key in keys:
        #根据ACSCII码将int转换成对应的字符，并将所有字符拼接起来，得到16位字符
        key = chr(key)
        str_key = str_key + key
    print("key is: " + str_key)

    ivs = [1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 7, 5, 3, 2, 1]
    #[标题开始，正文开始，正文结束，请求，响铃，垂直制表符，回车键，设备控制1，设备控制3，结束传输块，分组符，响铃，请求，正文结束，正文开始，标题开始]
    str_iv = ""
    for iv in ivs:
        # 根据ACSCII码将int转换成对应的字符，并将所有字符拼接起来，得到16位字符
        iv = chr(iv)
        str_iv = str_iv + iv
    print("iv is: " + str_iv)

    # 将int型的list转换成bytes型字节串先将十进制转换成十六进制，然后可以按照ascii表转换的转换显示
    #                        P          X    *             8    3             r          k   \t   ~          >             ^       t
    #十六进制为[11,ca,cc,11,"50",c0,8d,"58","2a",a3,f1,cd,"38","33",18,f4,e1,"72",a5,91,"4b","9","7e",cf,a9,"3e",c7,89,b9,"5e",99,"74"]
    longKey = [17, 202, 204, 17, 80, 192, 141, 88, 42, 163, 241, 205, 56, 51, 24, 244, 225, 114, 165, 145, 75, 9, 126, 207, 169, 62, 199, 137, 185, 94, 153, 116]
    longKey = bytes(longKey)

    answer = [90, 6, 215, 70, 79, 143, 87, 238, 40, 105, 7, 229, 121, 92, 70, 127]
    answer = bytes(answer)

    pc = PrpCrypt(str_key,str_iv)  # 初始化密钥
    #e = pc.encrypt("testtesttest")  # 加密
    d = pc.decrypt(longKey)  # 解密
    #print("加密:", e)
    print("解密:", d)