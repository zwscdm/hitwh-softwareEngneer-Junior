import pyupload
'''填写上传用户&密码，询问带教老师'''
user ="class"
pwd ="class@123"
bt_upload = pyupload.pyuploadClient(user=user, pwd=pwd, type='formal')  # type='test'：测试&优化因子， type='formal'：最后一次正式上传因子

'''alpha单次上传示例'''

# cython: language_level=3

alpha_file = 'pyalpha_BABB001.py'  # alpha文件
config_file = 'pyconfig_BABB001.py'  # config文件
save_path = 'bt_result'  # 请确保存在该文件夹，目前需要预先创建文件夹
bt_upload.upload_files(alpha_file=alpha_file, config_file=config_file, save_path=save_path)

'''alpha整体上传示例'''


# import os
#
# alpha_list = sorted(os.listdir('factor_wait'))
# alpha_list = [(alpha_list[i], alpha_list[int(len(alpha_list) / 2) + i]) for i in range(int(len(alpha_list) / 2))]
# save_path = 'bt_result'
# print(alpha_list)
# for i in alpha_list:
#     alpha = i[0]
#     config = i[1]
#     alpha_file = f'factor_wait/{alpha}'  # alpha文件
#     config_file = f'factor_wait/{config}'  # config文件
#


'''查看已成功上传因子, user为因子开头名'''
print(bt_upload.get_success_alpha(user='BABB'))