import torch
import os

p = 'transformer_model/saved_model/haribon_transformer_native_masking.pt'
obj = torch.load(p, map_location='cpu', weights_only=False)
print('TYPE', type(obj))
for k in ['scenario','history_days','horizon','feature_names','norm_mean','norm_std','config']:
    print(k, '=>', type(obj.get(k)), obj.get(k))
print('\nmodel_state_dict keys sample:')
for i, k in enumerate(obj['model_state_dict'].keys()):
    print(i, k)
    if i>40:
        break
