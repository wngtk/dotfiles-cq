#!/usr/bin/python3
"""
# **********************************************************************************
# Copyright (c) [Year] [name of copyright holder]
# [Software Name] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# Author:
# Create: 2020-08-03
# Description: abichecker tool
# **********************************************************************************
"""
import os
import shutil
import re
import sys
import subprocess
import distutils.version

class Package(object):
    """
    rpm package
    """
    def __init__(self, file_name):
        """
        init function
        """
        package_arch = file_name.split('.')[-2]
        package_name_version = re.sub(package_arch + '.rpm', '', file_name)
        package_version = re.findall(r'-\d+.*$', package_name_version)[0]
        package_name = re.sub(package_version, '', package_name_version)
        package_version = re.sub(r'^-', '', package_version)
        package_version = re.sub(r'\.+$', '', package_version)
        self.file_name = file_name
        self.name = package_name
        self.version = package_version
        self.arch = package_arch
        # if self.name.endswith('libs'):
        #     self.type = 'libs'
        # elif self.name.endswith('devel'):
        #     self.type = 'devel'
        # elif self.name.endswith('debuginfo'):
        #     self.type='debuginfo'
        # else:
        #     self.type='main'
            
    def __str__(self):
        """
        string of Package
        """
        return 'Name: ' + self.name + ', Version: ' + self.version +\
               ', Arch: ' + self.arch


def move_file(src_path, dst_path, infile):
    """
    move infile from src_path to dst_path
    """
    f_src = os.path.join(src_path, infile)
    if not os.path.exists(dst_path):
        os.mkdir(dst_path)
    f_dst = os.path.join(dst_path, infile)
    shutil.move(f_src, f_dst)

def get_version_num(packages):
    """
    get the version of given packages
    """
    version_num = []
    for package in packages:
        if package.version not in version_num:
            version_num.append(package.version)
    if distutils.version.LooseVersion(version_num[0]) > distutils.version.LooseVersion(version_num[1]):
        version_num[0], version_num[1] = version_num[1], version_num[0]
    return version_num


def get_sofile_name(sofilename):
    """
    get the .so file name
    ie: foo.so.0.0 -> foo.so
    """
    return  re.findall(r'.*.so', sofilename)[0]


def get_rpms(filepath):
    """
    get .rpm files starts with pkg in the given filepath
    """
    files = os.listdir(filepath)
    rpms = []
    for eachfile in files:
        #if eachfile.endswith('.rpm') and eachfile.startswith(pkg):
        if eachfile.endswith('.rpm'):
            rpms.append(eachfile)
    return rpms


def check_valid_rpmnum(packages):
    """
    check if the number of .rpm files is valid
    """
    type_num = {}
    for package in packages:
        if package.type in type_num.keys():
            type_num[package.type] += 1
        else:
            type_num[package.type] = 1
    if type_num['main'] == 2 or \
        'libs' in type_num.keys() and type_num['libs'] == 2 or \
        'devel' in type_num.keys() and type_num['devel'] == 2:
        return True
    else:
        print('The valid number of main rpmfiles and lib rpmfiles should be 2+2 or 0+2 or 2+0')
        return False


# def check_valid_version(packages):
#     """
#     check if the package version is valid
#     """
#     version_num = get_version_num(packages)
#     if len(version_num) != 2:
#         print('The version to be checked is not 2.')
#         return False
#     else:
#         return True


def rpm_uncompress(packages, common_dir, version_num):
    """
    uncompress the rpm packages in common_dir
    """
    os.chdir(common_dir)
    for version in version_num:
        if not os.path.exists(version):
            os.mkdir(version)
    for package in packages:
        os.chdir(common_dir)
        # move_file(common_dir, common_dir + '/' + package.version, package.file_name)
        os.chdir(package.version)
        os.system('rpm2cpio ' + common_dir+'/'+package.file_name + ' | cpio -div')


def dumper_by_debuginfo(verdir,version):
    """
    generate .dump file by debuginfo .rpm file
    """
    os.chdir(verdir)
    sofiles = []
    for root, dirs, files in os.walk(verdir):
        for eachfile in files:
            full_file = os.path.join(root, eachfile)
            if re.match(r'.*\.so.*', full_file) and not os.path.islink(full_file):
                sofiles.append(full_file)
    res = []
    if len(sofiles) > 0:
        for sofile in sofiles:
            (sofile_path, sofile_name) = os.path.split(sofile)
            sofile_name = get_sofile_name(sofile_name)
            if os.system('abi-dumper ' + sofile + ' --search-debuginfo='
                         + verdir + '/usr/lib/debug/'
                         + ' -o ' + 'ABI-' + sofile_name + '.dump' + ' -lver ' + version) == 0:
                res.append(sofile_name)
    return res


def do_abi_compliance_check(common_dir, old_dumpi, new_dumpi, old_version, new_version):
    """
    abi compliance check
    """
    # 检查compat_reports目录是否存在
    if not os.path.exists("compat_reports"):
        os.makedirs("compat_reports")
    # 指定输出文件
    output_file_path = 'compat_reports/abi_compliance_report.txt'
    old_dump_path = os.path.join(common_dir, old_version, 'ABI-' + old_dumpi + '.dump')
    new_dump_path = os.path.join(common_dir, new_version, 'ABI-' + new_dumpi + '.dump')
    # 打开文件，准备写入
    with open(output_file_path, 'a') as f:
        # 使用 subprocess.Popen 运行 abi-compliance-checker，将标准输出和标准错误输出同时重定向到文件和终端
        process = subprocess.Popen(['abi-compliance-checker', '-l', old_dumpi, '-old', old_dump_path, '-new', new_dump_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # 读取 abi-compliance-checker 输出并写入文件和终端
        while True:
            output = process.stdout.readline()
            error = process.stderr.readline()

            if not output and not error:
                break

            if output:
                f.write(output)
                print(output, end='')

            if error:
                print(error, end='')
        # 等待 abi-compliance-checker 执行完成
        process.wait()
    # os.system('abi-compliance-checker -l ' + old_dumpi +
    #           ' -old ' + common_dir + '/' + old_version + '/' + 'ABI-' + old_dumpi + '.dump'
    #           ' -new ' + common_dir + '/' + new_version + '/' + 'ABI-' + new_dumpi + '.dump')


def abi_compliance_check(common_dir, dumps, verdirs):
    """
    check the compatibility by given .dump files in common_dir + verdirs
    """
    old_dump = dumps[0]
    new_dump = dumps[1]
    if len(old_dump) == 0:
        print('Error: Did not find .so file in old_version')
        return
    if len(new_dump) == 0:
        print('Error: Did not find .so file in new_version')
        return
    os.chdir(common_dir)
    # 将数组转换为集合
    old_dump_set = set(old_dump)
    new_dump_set = set(new_dump)
    intersection_dump = old_dump_set & new_dump_set 
    unique_new_dump = new_dump_set - old_dump_set
    if unique_new_dump:
        print('Warning: old_version has less .so files, try checking these .so files.')
        for unique_item in unique_new_dump:  
            print(unique_item)
        while True:
            user_input = input("是否要继续？(y/n): ").lower()
            if user_input == 'y':
                break  
            elif user_input == 'n':
                sys.exit()
            else:
                print("无效的输入，请输入 'y' 或 'n'.")
    unique_old_dump = old_dump_set - new_dump_set  
    if unique_old_dump:
        print('Warning: new_version has less .so files, try checking these .so files.')
        for unique_item in unique_old_dump:  
            print(unique_item)
        while True:
            user_input = input("是否要继续？(y/n): ").lower()
            if user_input == 'y':
                break  
            elif user_input == 'n':
                sys.exit()
            else:
                print("无效的输入，请输入 'y' 或 'n'.")
    for dump in intersection_dump:
        do_abi_compliance_check(common_dir, dump, dump, verdirs[0], verdirs[1])
    generate_compatibility_html_report("compat_reports/abi_compliance_report.txt", "compat_reports/compatibility_reports.html")
    # if len(old_dump) == len(new_dump):
    #     for i in range(len(old_dump)):
    #         do_abi_compliance_check(common_dir, old_dump[i], new_dump[i], verdirs[0], verdirs[1])
    # elif len(old_dump) < len(new_dump):
    #     print('Warning: old_version has less .so files, try checking these .so files.')
    #     for i in range(len(old_dump)):
    #         if old_dump[i] in new_dump:
    #             do_abi_compliance_check(common_dir, old_dump[i], old_dump[i], verdirs[0], verdirs[1])
    # else:
    #     print('Warning: new_version has less .so files, try checking these .so files.')
    #     for i in range(len(new_dump)):
    #         if new_dump[i] in old_dump:
    #             do_abi_compliance_check(common_dir, new_dump[i], new_dump[i], verdirs[0], verdirs[1])


def main_function(pkg_name, folder):
    """
    main_function
    """
    common_dir = os.path.join(folder, pkg_name)
    rpms = get_rpms(common_dir)
    packages = []
    for rpm in rpms:
        packages.append(Package(rpm))
    verdirs = get_version_num(packages)
    if len(verdirs) != 2:
        print('The version to be checked is not 2.')
        return False
    # if check_valid_rpmnum(packages) and check_valid_version(packages):
    rpm_uncompress(packages, common_dir, verdirs)
    dumps = []
    for verdir in verdirs:
        dumps.append(dumper_by_debuginfo(common_dir + '/' + verdir, verdir))
    abi_compliance_check(common_dir, dumps, verdirs)




def generate_compatibility_html_report(report_file_path, output_html_path):
    """
    Generate an HTML report based on compatibility data.

    Parameters:
    - report_file_path (str): The path to the compatibility report file (e.g., "abi_compliance_report.txt").
    - output_html_path (str): The path to the output HTML file that will be generated.

    Generates an HTML report table with information extracted from the compatibility report file.
    The HTML table includes details about libraries, binary compatibility, source compatibility, 
    total binary compatibility problems, total source compatibility problems, and a link to the detailed report.

    The generated HTML file is saved to the specified output path.

    Usage example:
    generate_compatibility_html_report("abi_compliance_report.txt", "compatibility_reports.html")
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            a {{
                color: blue;
                text-decoration: underline;
                cursor: pointer;
            }}
            .darkorange {{
            color: darkorange;
            }}
            .red {{
                color: red;
            }}
            .green {{
                color: green;
            }}
        </style>
    </head>
    <body>

    <h2>兼容性报告总览</h2>

    <table>
        <tr>
            <th>序号</th>
            <th>动态库</th>
            <th>二进制兼容性</th>
            <th>源码兼容性</th>
            <th>二进制兼容性问题</th>
            <th>源码兼容性问题</th>
            <th>详情</th>
        </tr>
        {rows}
    </table>

    </body>
    </html>
    """
    # Extracting data from the abi_compliance_report.txt content
    reports = []
    with open(report_file_path, "r") as report_file:
        lines = report_file.readlines()
        for index, i in enumerate(range(0, len(lines), 9), start=1):  # Assuming each report has 9 lines
            report_info = lines[i:i+9]
            binary_compatibility = report_info[4].split(": ")[1].strip()
            source_compatibility = report_info[5].split(": ")[1].strip()
            # 根据百分比添加样式类
            binary_compatibility_percentage = float(binary_compatibility.rstrip('%'))
            source_compatibility_percentage = float(source_compatibility.rstrip('%'))
            binary_compatibility_class = "green" if binary_compatibility_percentage == 100 else "red" if binary_compatibility_percentage == 0 else "darkorange"
            source_compatibility_class = "green" if source_compatibility_percentage == 100 else "red" if source_compatibility_percentage == 0 else "darkorange"

            match = re.search(r'problems: \d+, warnings: \d+', report_info[6])
            if match:
                total_binary_problems = match.group(0)
            else:
                total_binary_problems = "未知"
            match = re.search(r'problems: \d+, warnings: \d+', report_info[7])
            if match:
                total_source_problems = match.group(0)
            else:
                total_source_problems = "未知"
            report_link = report_info[8].split(": ")[1].strip()
            match = re.search(r'compat_reports/([^/]+)/', report_link)
            if match:
                library = match.group(1)
            else:
                library = "NaN"
            report_link = report_link.replace("compat_reports/", "")
            row = f"""
            <tr>
                <td>{index}</td>
                <td>{library}</td>
                <td class="{binary_compatibility_class}">{binary_compatibility}</td>
                <td class="{source_compatibility_class}">{source_compatibility}</td>
                <td>{total_binary_problems}</td>
                <td>{total_source_problems}</td>
                <td><a href="{report_link}" target="_blank">报告</a></td>
            </tr>
            """
            reports.append(row)

    # Create HTML file with the formatted data
    html_content = html_template.format(rows="\n".join(reports))
    with open(output_html_path, "w") as html_file:
        html_file.write(html_content)


if __name__ == '__main__':
    """
    main
    1. create a directory named sys.argv[1] (libfoo) in sys.argv[2] (/root/checkdir/);
    2. put the rpm files and debuginfo files of 2 versions in libfoo;
    3. run 'python abichecker.py 'libfoo' '/root/checkdir/'
    4. the results are saved in /root/checkdir/libfoo/compat_reports
    """
    main_function(sys.argv[1], sys.argv[2])
