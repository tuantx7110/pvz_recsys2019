#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 基础模块
import os
import sys
import gc
import json
import time
import functools
from datetime import datetime

# 数据处理
import numpy as np
import pandas as pd
from math import sqrt
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer

# 自定义工具包
sys.path.append('../tools/')
import loader
import cate_encoding
import custom_cate_encoding

# 设置随机种子
SEED = 2018
np.random.seed (SEED)

FEA_NUM = 24

input_root_path = '../input/'
output_root_path = '../feature/'

tr_base_path = input_root_path + 'train.ftr'
te_base_path = input_root_path + 'test.ftr'

cv_id_path = input_root_path + 'cv_id.csv.0329'

postfix = 's0_{}'.format(FEA_NUM)
file_type = 'ftr'

# 当前特征
tr_fea_out_path = output_root_path + 'tr_fea_{}.{}'.format(postfix, file_type)
te_fea_out_path = output_root_path + 'te_fea_{}.{}'.format(postfix, file_type)

# 当前特征 + 之前特征 merge 之后的完整训练数据
tr_out_path = output_root_path + 'tr_{}.{}'.format(postfix, file_type)
te_out_path = output_root_path + 'te_{}.{}'.format(postfix, file_type)


ID_NAMES = ['session_id', 'impressions']
TARGET_NAME = 'target'

def feat_extract(df):
    tr = loader.load_df('../input/tr.ftr')
    te = loader.load_df('../input/te.ftr')
    df_sample = pd.concat([tr, te])
    df_sample['impr_rank'] = df_sample.groupby(['session_id']).cumcount().values

    actions = ['interaction item image', 'interaction item info', \
            'interaction item deals', 'interaction item rating', \
            'search for item', 'clickout item']
    df = df[df.action_type.isin(actions)]
    df = df[~pd.isnull(df.reference)]
    df = df[['session_id', 'reference', 'step']]
    df.columns = ID_NAMES + ['step']
    df['impressions'] = df['impressions'].astype('int')
    df = df.merge(df_sample[['session_id', 'step']].drop_duplicates(), \
            on='session_id', how='left')
    # 过滤掉最后一次 clk 样本
    df = df[df.step_x < df.step_y] 
    df = df.drop_duplicates(subset=['session_id'], keep='last')

    df_feat = df_sample[ID_NAMES + ['impr_rank']] \
            .merge(df[ID_NAMES + ['step_x']] \
            .drop_duplicates(subset=ID_NAMES), on=ID_NAMES, how='left')

    print (df_feat.head())
    print ('filter', df_feat.shape)
    sub_df = df_feat[~pd.isnull(df_feat['step_x'])]
    sub_df = sub_df[['session_id', 'impr_rank']]
    sub_df.columns = ['session_id', 'lastest_item-impr_rank']
    print ('filter', sub_df.shape)

    df_feat = df_sample[['session_id']].drop_duplicates()
    df_feat = df_feat.merge(sub_df, on='session_id', how='left') 

    print (df_feat.shape)
    print (df_feat.head())
    print (df_feat.columns.tolist())

    return df_feat

def output_fea(tr, te):
    # 特征重排，保证输出顺序一致
    # ...

    # 特征文件只保留主键 & 本次新增特征
    #primary_keys = ['session_id', 'impressions']
    #fea_cols = []
    #required_cols =  primary_keys + fea_cols

    # 特征输出
    #tr = tr[required_cols]
    #te = te[required_cols]

    print (tr.head())
    print (te.head())

    loader.save_df(tr, tr_fea_out_path)
    loader.save_df(te, te_fea_out_path)

def add_meta_fea(df):
    df['impr_rank_sub_lastest_item-impr_rank'] = \
            df['impr_rank'] - df['lastest_item-impr_rank']
    df['abs_impr_rank_sub_lastest_item-impr_rank'] = \
            np.abs(df['impr_rank_sub_lastest_item-impr_rank'])

# 生成特征
def gen_fea(base_tr_path=None, base_te_path=None):

    tr = loader.load_df('../input/train.ftr')
    te = loader.load_df('../input/test.ftr')

    #tr = loader.load_df('../input/tr.ftr')
    #te = loader.load_df('../input/te.ftr')

    #tr = loader.load_df('../feature/tr_s0_9.ftr')
    #te = loader.load_df('../feature/te_s0_9.ftr')

    #tr = loader.load_df('../feature/tr_fea_s0_1.ftr')
    #te = loader.load_df('../feature/te_fea_s0_1.ftr')

    #tr = tr.head(1000)
    #te = te.head(1000)

    df_base = pd.concat([tr, te])
    df_feat = feat_extract(df_base)

    tr_sample = loader.load_df('../feature/tr_s0_0.ftr')
    te_sample = loader.load_df('../feature/te_s0_0.ftr')

    #merge_keys = ['session_id', 'impressions']
    merge_keys = ['session_id']
    tr = tr_sample[ID_NAMES + ['impr_rank']] \
            .merge(df_feat, on=merge_keys, how='left')
    te = te_sample[ID_NAMES + ['impr_rank']] \
            .merge(df_feat, on=merge_keys, how='left')
    add_meta_fea(tr)
    add_meta_fea(te)
    del tr['impr_rank'], te['impr_rank']

    print (tr.shape, te.shape)
    print (tr.head())
    print (te.head())
    print (tr.columns)

    output_fea(tr, te)

# merge 已有特征
def merge_fea(tr_list, te_list):
    tr = loader.merge_fea(tr_list, primary_keys=ID_NAMES)
    te = loader.merge_fea(te_list, primary_keys=ID_NAMES)

    tr['impressions'] = tr['impressions'].astype('int')
    te['impressions'] = te['impressions'].astype('int')

    print (tr.head())
    print (te.head())

    print (tr[ID_NAMES].head())

    loader.save_df(tr, tr_out_path)
    loader.save_df(te, te_out_path)


if __name__ == "__main__":

    print('start time: %s' % datetime.now())
    root_path = '../feature/'
    base_tr_path = root_path + 'tr_s0_15.ftr'
    base_te_path = root_path + 'te_s0_15.ftr'

    gen_fea()

    # merge fea
    prefix = 's0'
    #fea_list = [3,6,8,14,15,FEA_NUM]
    fea_list = [22,FEA_NUM]

    tr_list = [base_tr_path] + \
            [root_path + 'tr_fea_{}_{}.ftr'.format(prefix, i) for i in fea_list]
    te_list = [base_te_path] + \
            [root_path + 'te_fea_{}_{}.ftr'.format(prefix, i) for i in fea_list]

    #merge_fea(tr_list, te_list)

    print('all completed: %s' % datetime.now())
