from django.http import JsonResponse
import os
import signal
import subprocess
import requests
import json
import platform
import datetime
import re
from catalog.models import LibUser


def render_json(code=0, msg='success', data={}):
    result = {
        'code': code,
        'message': msg,
        'data': data,
    }
    return JsonResponse(result)


def is_ip(address):
    """
    校验是否是IP地址
    :param address:
    :return:
    """
    compile_ip = re.compile(
        '^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')
    if compile_ip.match(address):
        return True
    else:
        return False


def get_ip(request):
    """
    获取IP
    :param request:
    :return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_ips_list(ips):
    """
    根据正则表达式获取字符串中的IP地址
    """
    pattern = re.compile(
        r"((?:(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d))))")
    a = pattern.findall(ips)
    ips_list = [g[0] for g in a]

    return ips_list


def get_request(url, params={}, headers={}, timeout=120):
    """
    HTTP请求-Get请求
    :param url:
    :param params:  string URL中的参数
    :param headers:
    :param timeout:
    :return:
    """
    if not headers:
        headers = {
            "Content-Type": "application/json",
        }

    response = requests.request(
        'GET', url, headers=headers, params=params, timeout=timeout)
    return response.text


def post_request(url, params={}, data={}, headers={}, timeout=120):
    """
    HTTP请求-Post请求
    :param url:
    :param params:  string URL中的参数
    :param data:    dict body中的参数
    :param headers: dict
    :param timeout:
    :return:
    """
    if not headers:
        headers = {
            "Content-Type": "application/json",
        }

    response = requests.request(
        'POST', url, headers=headers, params=params, data=json.dumps(data), timeout=timeout)
    return response.text


def run_cmd(cmd_string, timeout=600):
    """
    执行命令
    :param cmd_string:  string 字符串
    :param timeout:  int 超时设置
    :return:
    """
    p = subprocess.Popen(cmd_string, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True, close_fds=True,
                         start_new_session=True)

    format = 'utf-8'
    if platform.system() == "Windows":
        format = 'gbk'

    try:
        (msg, errs) = p.communicate(timeout=timeout)
        ret_code = p.poll()
        if ret_code:
            code = 1
            msg = "[Error]Called Error ： " + str(msg.decode(format))
        else:
            code = 0
            msg = str(msg.decode(format))
    except subprocess.TimeoutExpired:
        # 注意：不能使用p.kill和p.terminate，无法杀干净所有的子进程，需要使用os.killpg
        p.kill()
        p.terminate()
        os.killpg(p.pid, signal.SIGUSR1)

        # 注意：如果开启下面这两行的话，会等到执行完成才报超时错误，但是可以输出执行结果
        # (outs, errs) = p.communicate()
        # print(outs.decode('utf-8'))

        code = 1
        msg = "[ERROR]Timeout Error : Command '" + cmd_string + \
            "' timed out after " + str(timeout) + " seconds"
    except Exception as e:
        code = 1
        msg = "[ERROR]Unknown Error : " + str(e)

    return code, msg


def get_uuid():
    """
    生成唯一的uuid
    :return:
    """
    import uuid
    uid = str(uuid.uuid4())
    return ''.join(uid.split('-'))


def UTC2Local(utc_str):
    """
    处理UTC时间
        类似：2019-10-23T06:00:34.882747 或者是  2020-01-13T19:53:56Z时间
    :param utc_str
    :return:
    """
    # 先去掉小数点
    utc_str = utc_str.split('.')[0]

    # 第一次替换为空格,第二次替换为空字符串
    utc_time = utc_str.replace("T", " ").replace("Z", "")

    # UTC转本地时间+8h
    utc_str = datetime.datetime.strptime(
        utc_time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)

    # 控制输出格式
    return utc_str.strftime("%Y-%m-%d %H:%M:%S")


def validate_password(password, min_len=8, max_len=26):
    """
    校验密码
        长度：8-26位
        密码至少包含：大写字母、小写字母、数字、特殊字符（!@$%^-_=+[{}]:,./?）中的三种
    :param max_len:
    :param min_len:
    :param password:
    :return:
    """
    length = len(password)
    if length < min_len:
        return 200, '密码长度不符'

    if length > max_len:
        return 200, '密码长度不符'

    reg = "[A-Za-z0-9!@$%^-_=+\[{}\]:,./?]"
    if len(re.findall(reg, password)) < length:
        return 201, '密码有非法字符'

    first = re.search('[A-Z]', password)
    num1 = 1 if first else 0

    second = re.search('[a-z]', password)
    num2 = 1 if second else 0

    third = re.search('[0-9]', password)
    num3 = 1 if third else 0

    fourth = re.search("[!@$%^-_=+\[{}\]:,./?]", password)
    num4 = 1 if fourth else 0

    if num1 + num2 + num3 + num4 < 3:
        return 202, '密码必须包含大写字母、小写字母、数字和特殊字符中的三种'

    return 0, 'success'


def is_dir(path):
    """
    判断目录是否存在
    :param path:
    :return:
    """
    if path and os.path.isdir(path):
        return True

    return False


def is_file(path):
    """
    判断文件是否存在
    :param path:
    :return:
    """
    if path and os.path.isfile(path):
        return True

    return False


def traverse_path(path):
    """
    遍历目录，获取文件和目录
    :param path:
    :return:
    """
    g = os.walk(path)

    dirs = []
    files = []

    # 三个参数：分别返回 1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
    for path, dir_list, file_list in g:
        for dir_name in dir_list:
            dirs.append(os.path.join(path, dir_name))

        for file_name in file_list:
            files.append(os.path.join(path, file_name))

    return dirs, files


def unzip_file(zip_src, dst_dir=None):
    """
    解压缩（Zip格式）- 注意：如果不传目的路径，则默认解压到源路径+_files
    :param zip_src:  源路径
    :param dst_dir:  目的解压路径，如为空则默认为源路径+_files
    :return:
    """
    import zipfile
    r = zipfile.is_zipfile(zip_src)

    if not zip_src:
        return 1, '源路径为空', ''

    # 判断是否是zip压缩包
    if not r:
        return 1, '非zip压缩包', ''

    # 如果目的解压路径参数不传，则默认为源路径+_files
    if not dst_dir:
        dst_dir = zip_src + "_files"
        if not os.path.isdir(dst_dir):
            os.mkdir(dst_dir)

    # 判断目的解压的目录是否存在
    if not os.path.isdir(dst_dir):
        return 1, '目的解压目录不存在', ''

    fz = zipfile.ZipFile(zip_src, 'r')
    for file in fz.namelist():
        # Mac电脑压缩Zip会增加__MACOSX目录，自动跳过
        if '__MACOSX' not in file:
            fz.extract(file, dst_dir)
    fz.close()

    return 0, 'success', dst_dir


def unrar_file(rar_src, dst_dir=None):
    """
    解压缩（rar格式）- 注意：如果不传目的路径，则默认解压到源路径+_files
    注意：需要安装rarfile, pip install rarfile
    注意：如果是Linux需要安装unrar
    :param rar_src:  源路径
    :param dst_dir:  目的解压路径，如为空则默认为源路径+_files
    :return:
    """
    import rarfile

    if not rar_src:
        return 1, '源路径为空', ''

    # 如果目的解压路径参数不传，则默认为源路径+_files
    if not dst_dir:
        dst_dir = rar_src + "_files"
        if not os.path.isdir(dst_dir):
            os.mkdir(dst_dir)

    # 判断目的解压的目录是否存在
    if not os.path.isdir(dst_dir):
        return 1, '目的解压目录不存在', ''

    rar = rarfile.RarFile(rar_src, mode='r')
    rar.extractall(dst_dir)
    rar.close()

    return 0, 'success', dst_dir


def get_file_type(file):
    """
    获取文件的后缀名
    :param file:
    :return:
    """
    if not file:
        return ''

    file_list = os.path.splitext(file)

    if len(file_list) >= 2:
        return file_list[1]

    return ''


def get_ips(cidr):
    """
    获取某个网段的所有IP
    注意：需要安装IPy，pip install IPy
    :param cidr:
    :return:
    """
    from IPy import IP
    ips = IP(cidr)
    return ips


def get_next_value(value, list):
    """
    获取list中value的下一个值（如果value为最后一个，则下一个为第一个）
    :param value:
    :param list:
    :return:
    """
    if value not in list:
        return ''

    list_count = len(list)
    index = list.index(value)

    next_index = index + 1 if (index + 1) < list_count else 0
    return list[next_index]


def md5_string(content):
    """
    MD5加密
    :param content:
    :return:
    """
    if not content:
        return ''

    import hashlib
    return hashlib.md5(content.encode(encoding="UTF-8")).hexdigest()


def get_python_version():
    """
    获取Python版本
    :return:
    """
    import sys
    return sys.version_info


class EmailBackend:
    def authenticate(self, request, **credentials):
        # 要注意登录表单中用户输入的用户名或者邮箱的 field 名均为 username
        email = credentials.get('email', credentials.get('username'))
        try:
            user = LibUser.objects.get(email=email)
        except LibUser.DoesNotExist:
            pass
        else:
            if user.check_password(credentials["password"]):
                return user

    def get_user(self, user_id):
        """
        该方法是必须的
        """
        try:
            return LibUser.objects.get(pk=user_id)
        except LibUser.DoesNotExist:
            return None

class CardNoBackend:
    def authenticate(self, request, **credentials):
        card_no = credentials.get('card_No', credentials.get('username'))
        try:
            user = LibUser.objects.get(card_No=card_no)
        except LibUser.DoesNotExist:
            pass
        else:
            if user.check_password(credentials["password"]):
                return user

    def get_user(self, user_id):
        """
        该方法是必须的
        """
        try:
            return LibUser.objects.get(pk=user_id)
        except LibUser.DoesNotExist:
            return None