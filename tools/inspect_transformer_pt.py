import torch
import os
import numpy as np

files = [
    'transformer_model/saved_model/haribon_transformer_native_masking.pt',
    'transformer_model/saved_model/haribon_transformer_hybrid_adaptive.pt'
]
for p in files:
    print('PATH:', p)
    if not os.path.exists(p):
        print('  MISSING')
        continue
    obj = torch.load(p, map_location='cpu')
    print('  TYPE:', type(obj))
    if isinstance(obj, dict):
        print('  KEYS:', list(obj.keys())[:20])
        cnt = 0
        for k, v in obj.items():
            try:
                print('   key', k, 'shape', getattr(v, 'shape', None), 'dtype', getattr(v, 'dtype', None))
            except Exception as e:
                print('   key', k, 'type', type(v))
            cnt += 1
            if cnt >= 5:
                break
    else:
        try:
            arr = np.array(obj)
            print('  asarray shape', arr.shape)
        except Exception as e:
            print('  cannot asarray', e)
print('DONE')
