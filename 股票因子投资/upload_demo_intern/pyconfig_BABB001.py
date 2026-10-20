CONSTANTS = {} # 不需要修改
UNIVERSE = {"pool" :"","disable":""} # 不需要修改

ALPHA = [# 每一个字典对应一个因子，不同的参数。
    {
     "id":"Alpha_BABB001",# 因子名，请严格按照:Alpha_名字（拼写，比如张三：ZS or Zsan or zhangsan）+因子编号（对于每个人，每个编号只能对应一个因子）
     "dumpAlphaFile":True,# 不需要修改
    #  "Config":{"alphacode":"pyalpha_xxx001", 'trimp':60}, #alphacode是pyalpha_xxx.py文件的名字，trimp是一些别的参数
     "Config":{"alphacode":"pyalpha_BABB001",'trimp':60},
     "Processes":[], # 不需要修改

     'sense':'尾盘收益率波动越小，收益越高'
    }
     
]
# 回测包需要传入的参数。
BACKTEST = dict(
 )
import sys
import pandas as pd
import numpy as np

# diagnose_pyupload.py
