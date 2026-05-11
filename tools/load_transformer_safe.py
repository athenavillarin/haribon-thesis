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
    try:
        # allowlist numpy reconstructors used by some pickles
        torch.serialization.add_safe_globals(["numpy._core.multiarray._reconstruct"])
    except Exception as e:
        pass
    try:
        obj = torch.load(p, map_location='cpu', weights_only=False)
        print('  LOADED type:', type(obj))
        if isinstance(obj, dict):
            print('  KEYS:', list(obj.keys())[:20])
            for k in list(obj.keys())[:10]:
                v = obj[k]
                print('   key', k, 'type', type(v), 'shape', getattr(v, 'shape', None))
        else:
            try:
                arr = np.array(obj)
                print('  asarray shape', arr.shape)
            except Exception as e:
                print('  cannot asarray', e)
    except Exception as e:
        print('  LOAD ERROR:', repr(e))
print('DONE')
