import datetime
import json
import time
import re
import requests
import base64
from getpass import getpass
from Cryptodome.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
from Cryptodome.PublicKey import RSA
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

SEP_PUBKEY = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxG1zt7VW/VNk1KJC7AuoInrMZKTf0h6S6xBaROgCz8F3xdEIwdTBGrjUKIhIFCeDr6esfiVxUpdCdiRtqaCS9IdXO+9Fs2l6fx6oGkAA9pnxIWL7bw5vAxyK+liu7BToMFhUdiyRdB6erC1g/fwDVBywCWhY4wCU2/TSsTBDQhuGZzy+hmZGEB0sqgZbbJpeosW87dNZFomn/uGhfCDJzswjS/x0OXD9yyk5TEq3QEvx5pWCcBJqAoBfDDQy5eT3RR5YBGDJODHqW1c2OwwdrybEEXKI9RCZmsNyIs2eZn1z1Cw1AdR+owdXqbJf9AnM3e1CN8GcpWLDyOnaRymLgQIDAQAB'


class SEP():
    def __init__(self) -> None:
        self._session = requests.Session()
        self._urls = {
            'sep_home': 'http://sep.ucas.ac.cn/',
            'slogin': 'http://sep.ucas.ac.cn/slogin',
            'code': 'http://sep.ucas.ac.cn/changePic',
            'ehall': 'http://sep.ucas.ac.cn/portal/site/416/2095',
            'sik': 'https://ehall.ucas.ac.cn/site/apps/launch'
        }

    def login_sep(self, username, password):
        # get JSESSIONID in cookies
        self._session.get(url=self._urls['sep_home'])
        assert 'JSESSIONID' in self._session.cookies

        # get code
        resp_code = self._session.get(url=self._urls['code'])
        with open('./code.jpg', 'wb') as f:
            f.write(resp_code.content)
        code = input('请输入验证码（查看 code.jpg 文件）: ')

        # login
        data = {
            'userName': username,
            'pwd': self.encrpt(password),
            'certCode': code,
            'sb': 'sb'
        }
        self._session.post(url=self._urls['slogin'], data=data)
        if 'sepuser' not in self._session.cookies:
            raise ValueError('登录失败，请检查账号密码或验证码')
        return self._session.cookies

    def login_ehall(self):
        # 访问 2095 页面中包含的 cas-login 页面地址即可获取 ehall cookies
        resp_2095 = self._session.get(url=self._urls['ehall'])
        cas_login_url = re.search("\'http.*2095\'", resp_2095.text)
        # remove \' and \'
        cas_login_url = cas_login_url.group()[1:-1]
        # 获取 ehall cookies
        self._session.get(url=cas_login_url)
        if 'vjuid' not in self._session.cookies:
            raise ValueError('管理大厅登陆失败')
        return self._session.cookies

    @staticmethod
    def encrpt(password, public_key=SEP_PUBKEY):
        public_key = f'-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----'
        rsakey = RSA.importKey(public_key)
        cipher = Cipher_pksc1_v1_5.new(rsakey)
        cipher_text = base64.b64encode(cipher.encrypt(password.encode()))
        return cipher_text.decode()

    def get_idendities(self):
        cookies = self._session.cookies
        url_post = 'https://ehall.ucas.ac.cn/site/data-source/detail'
        # url_get1 = 'https://ehall.ucas.ac.cn/site/user/get-identitys?agent_uid=&starter_depart_id=68859&test_uid=0'
        url_get2 = 'https://ehall.ucas.ac.cn/site/form/start-data?app_id=740&node_id=&userview=1'
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
                   'X-Requested-With': 'XMLHttpRequest'}
        # r10a_data = {'id': 10, 'inst_id': 0, 'app_id': 740,
        #              'params[change]': '{"170":{"type":"one"}}',
        #              'starter_depart_id': 68859, 'test_uid': 0}
        r10b_data = {'id': 10, 'inst_id': 0, 'app_id': 740,
                     'params[change]': '{"171":{"type":"one","date":{"rxsj":"Y"}}}',
                     'starter_depart_id': 68859, 'test_uid': 0}
        r59a_data = {'id': 59, 'inst_id': 0, 'app_id': 740,
                     'params[change]': '{"171":{"type":"one","date":{"rxsj":"Y"}}}',
                     'starter_depart_id': 68859, 'test_uid': 0}

        # r10a 身份信息：证件号、手机号、邮箱等
        # r10a = requests.post(url=url_post, data=r10a_data,
        #                      headers=headers, cookies=cookies, verify=False)
        # r10b 培养信息：单位、专业、导师等
        r10b = requests.post(url=url_post, data=r10b_data,
                             headers=headers, cookies=cookies, verify=False)
        # r59a 培养单位：代码、名称
        r59a = requests.post(url=url_post, data=r59a_data,
                             headers=headers, cookies=cookies, verify=False)
        # rget1 账号信息：不同身份对应的学号、uid (与 cookies 中的 vjuid 相同)
        # rget1 = requests.get(url=url_get1, headers=headers,
        #                      cookies=cookies, verify=False)
        # rget2 主要用于获取 sik 表单
        rget2 = requests.get(url=url_get2, headers=headers,
                             cookies=cookies, verify=False)

        form1533 = rget2.json()['d']['data']['1533']
        # User_xx: 18 姓名, 19 学号, 20 性别, 27 手机, 56 姓名, 82 空
        # Calender_xx: 28 空, 30 当时, 57 当时, 100 空, 117 空, 180 空, 182 空

        # Input_xx: 21 培养单位代码, 22 培养单位, 23 攻读专业, 61 培养层次
        form1533.update({'Input_21': r59a.json()['d']['list']['dept_sn'],
                         'Input_22': r10b.json()['d']['list']['171pydw'],
                         'Input_23': r10b.json()['d']['list']['171gdzy'],
                         'Input_61': r10b.json()['d']['list']['171pycc']
                         })

        # 班级
        if 'class' in r59a.json()['d']['list']:
            form1533.update(
                {'User_82': r59a.json()['d']['list']['class']})

        # 自动判断集中教学，填写集中教学院系
        if r59a.json()['d']['list']['jizhong']:
            form1533.update({'Input_24': r59a.json()['d']['list']['jizhong']})
        return form1533

    def submit_sik(self, form_id=None, form_temp=None, start_day=None, days=5):
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
                   'X-Requested-With': 'XMLHttpRequest'}
        if form_id is None:
            form_id = self.get_idendities()
        form_temp.update(form_id)

        if start_day is None:
            start_day = datetime.date.today()
        end_day = start_day + datetime.timedelta(days=days)
        timestr = time.strftime('%Y-%m-%dT%H:%M:%S+08:00')
        form_temp.update({
            # "2022-09-26T16:00:00.000Z", 离校时间
            "Calendar_28": f"{start_day.isoformat()}T00:00:00.000Z",
            # "2022-09-27T16:19:56+08:00", 当时
            "Calendar_30": timestr,
            # "2022-09-27T16:19:56+08:00", 当时
            "Calendar_57": timestr,
            # 返校时间
            "Calendar_100": f"{end_day.isoformat()}T00:00:00.000Z"
        })
        data_string = json.dumps(
            {"app_id": "740", "node_id": "", "form_data": {"1533": form_temp}, "userview": 1})
        data = {'data': data_string, 'starter_depart_id': 68859,
                'step': 0, 'agent_uid': ''}
        resp = self._session.post(
            url=self._urls['sik'], data=data, headers=headers, verify=False)

        if resp.json().get('e') != 0:
            print(f'{start_day} 至 {end_day} 行程填报失败')
        else:
            print(f'{start_day} 至 {end_day} 行程填报成功')


def submit_sik():
    with open('./sik_info.json', 'r') as f:
        data = json.load(f)
    with open('./sik_templete.json', 'r') as f:
        form_temp = json.load(f)
    campus_code = {
        "雁栖湖校区": "1",
        "玉泉路校区": "2",
        "中关村校区": "3",
        "奥运村校区": "4"
    }
    form_temp.update({
        "Input_69": data['form']['出校事由具体说明'],
        "Input_157": data['form']['所在校区'],
        "RepeatTable_33": [
            {
                "SelectV2_93": [
                    {
                        "name": data['form']['出发地'],
                        "value": campus_code[data['form']['出发地']],
                        "default": 0,
                        "imgdata": ""
                    }
                ],
                "Input_42": data['form']['目的地'],
                "Input_45": data['form']['出行方式']
            }
        ]
    })

    if data['sep_login']['邮箱']:
        userName = data['sep_login']['邮箱']
        passwd = data['sep_login']['密码']
    else:
        userName = input('请输入邮箱：')
        passwd = getpass('请输入密码: ')

    sep = SEP()
    sep.login_sep(userName, passwd)
    sep.login_ehall()
    form_id = sep.get_idendities()
    print(f'''身份信息: 
        姓名: {form_id['User_18']}
        学号: {form_id['User_19']}
        手机号: {form_id['User_27']}
    ''')

    start_day = data['申请']['开始时间'].split('-')
    start_day = datetime.date(int(start_day[0]), int(
        start_day[1]), int(start_day[2]))
    end_day = data['申请']['结束时间'].split('-')
    end_day = datetime.date(int(end_day[0]), int(end_day[1]), int(end_day[2]))
    days_step = int(data['申请']['单次申请天数'])
    delta_days = (end_day - start_day).days

    for delta in range(0, delta_days, days_step):
        time.sleep(1)
        sday = start_day + datetime.timedelta(days=delta)
        sep.submit_sik(form_id=form_id, form_temp=form_temp,
                       start_day=sday, days=days_step)


if __name__ == "__main__":
    submit_sik()
