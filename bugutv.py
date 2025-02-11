#!/opt/conda/bin/python3.9
import base64
import httpx
import re
import sys
import time
from urllib.parse import urlencode
from urllib.parse import quote

import requests

# global variables
uname = ''            # username，需要修改成自己的登录用户名！！！！！！！！！！！！！！！！！！！！
upassword = ''         # password，需要修改成自己的密码！！！！！！！！！！！！！！！！！！！！！！！

# 通知服务
# fmt: off
push_config = {

    'NTFY_URL': 'https://ntfy.sh',                     # ntfy地址,如https://ntfy.sh
    'NTFY_TOPIC': '',                   # ntfy的消息应用topic，需要修改成自己的topic ！！！！！！！！！！！！！！！！！！！！
    'NTFY_PRIORITY':'3',                # 推送消息优先级,默认为3

}
# fmt: on

data_nonce = ''
wpnonce = ''
spaceurl = 'https://www.bugutv.org/user'
r = httpx.Client(http2=True)

#以下是使用ntfy通知的函数
def ntfy(title: str, content: str) -> None:
    """
    通过 Ntfy 推送消息
    """

    def encode_rfc2047(text: str) -> str:
        """将文本编码为符合 RFC 2047 标准的格式"""
        encoded_bytes = base64.b64encode(text.encode("utf-8"))
        encoded_str = encoded_bytes.decode("utf-8")
        return f"=?utf-8?B?{encoded_str}?="

    if not push_config.get("NTFY_TOPIC"):
        return
    print("ntfy 服务启动")
    priority = "3"
    if not push_config.get("NTFY_PRIORITY"):
        print("ntfy 服务的NTFY_PRIORITY 未设置!!默认设置为3")
    else:
        priority = push_config.get("NTFY_PRIORITY")

    # 使用 RFC 2047 编码 title
    encoded_title = encode_rfc2047(title)

    data = content.encode(encoding="utf-8")
    headers = {"Title": encoded_title, "Priority": priority}  # 使用编码后的 title

    url = push_config.get("NTFY_URL") + "/" + push_config.get("NTFY_TOPIC")
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:  # 使用 response.status_code 进行检查
        print("Ntfy 推送成功！")
    else:
        print("Ntfy 推送失败！错误信息：", response.text)

#从个人空间页面获取当前K值
def get_point(spaceurl):
    ret = r.get(spaceurl).text
    time.sleep(1)
    point_now = re.findall(r'<span class="badge badge-warning-lighten"><i class="fas fa-coins"></i> (.*?)</span>', ret)[0]
    return point_now

#登录网站，并获取个人空间入口
def login(uname, upassword):
    ret = r.get(r'https://www.bugutv.org').text
    time.sleep(1)
    print("准备登录")
    #进行登录
    data = {'action': "user_login", 'username': uname, 'password': upassword, 'rememberme': 1}
    ret = r.post('https://www.bugutv.org/wp-admin/admin-ajax.php', data=data).text
    time.sleep(1)
    if '\\u767b\\u5f55\\u6210\\u529f' in ret:
        print('登录成功')
    else:
        print('登录失败')
        return False, False

#进行签到
def qiandao():
    ret = r.get('https://www.bugutv.org/user').text
    time.sleep(1)
    data_nonce = re.findall(r'data-nonce="(.*?)" ', ret)[0]
    print('准备签到：获取到签到页 data-nonce: ' + data_nonce )

    data = {'action': 'user_qiandao',"nonce":data_nonce}
    ret = r.post('https://www.bugutv.org/wp-admin/admin-ajax.php', data=data).text
    time.sleep(1)
    if '\\u4eca\\u65e5\\u5df2\\u7b7e\\u5230' in ret:
        print('今日已签到，请明日再来')
    if '\\u7b7e\\u5230\\u6210\\u529f' in ret:
        print('签到成功，奖励已到账：1.0积分')

#退出登录
def logout():
    ret = r.get('https://www.bugutv.org/wp-login.php?action=logout&redirect_to=https%3A%2F%2Fwww.bugutv.org&_wpnonce=' + wpnonce).text
    print('退出登录')


if __name__ == '__main__':
    print("开始运行bugutv自动签到脚本：")
    for i in range(3): # 尝试3次
        if i > 0:
            print('尝试第' + str(i) + '次')
        try:
            login(uname, upassword)

            #获取签到前的积分数量
            k_num1 = get_point(spaceurl)

            #开始签到
            qiandao()
            
            #获取签到后的积分数量
            k_num2 = get_point(spaceurl)

            ret = r.get("https://www.bugutv.org/user").text

            wpnonce = re.findall(r'action=logout&amp;redirect_to=https%3A%2F%2Fwww.bugutv.org&amp;_wpnonce=(.*?)',ret)[0]

            #发送推送 通知
            title = '布谷TV签到：获得'+str(int(k_num2)-int(k_num1))+'个积分'
            content = uname+'本次获得积分: ' + str(int(k_num2)-int(k_num1)) + '个\n'+'累计积分: ' + str(int(k_num2)) + '个'
            #ntfy通知
            ntfy(title,content)
            
            
            print('***************布谷TV签到：结果统计***************')
            print(content)
            print('**************************************************')
            
            #退出登录
            logout()
            sys.exit(0)
        except Exception as e:
            print('line: ' + str(e.__traceback__.tb_lineno) + ' ' + repr(e))
            time.sleep(10)
