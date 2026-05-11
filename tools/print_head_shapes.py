import torch
p='transformer_model/saved_model/haribon_transformer_hybrid_adaptive.pt'
try:
    torch.serialization.add_safe_globals(["numpy._core.multiarray._reconstruct"])
except Exception:
    pass
obj=torch.load(p,map_location='cpu',weights_only=False)
state=obj['model_state_dict']
print('config d_model:', obj['config'].get('d_model'))
print('num_layers:', obj['config'].get('num_layers'))
print('num_heads:', obj['config'].get('num_heads'))
for k in state:
    if k.startswith('head'):
        print(k, state[k].shape)
