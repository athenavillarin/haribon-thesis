"""
Simple Transformer classifier for HAB detection.
"""

from __future__ import annotations


def import_torch():
    """Lazy import so CLI help still works even if torch is not installed."""
    try:
        import torch  # type: ignore[reportMissingImports]
        import torch.nn as nn  # type: ignore[reportMissingImports]
        return torch, nn
    except Exception as exc:  # noqa: BLE001
        raise ImportError(
            "PyTorch is required for transformer_model. "
            "Install with: pip install torch"
        ) from exc


def build_model(
    input_dim: int,
    seq_len: int,
    d_model: int,
    num_heads: int,
    num_layers: int,
    ff_dim: int,
    dropout: float,
):
    torch, nn = import_torch()

    class HABTransformerClassifier(nn.Module):
        def __init__(self):
            super().__init__()
            self.input_proj = nn.Linear(input_dim, d_model)
            self.pos_embed = nn.Parameter(torch.zeros(1, seq_len, d_model))

            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=num_heads,
                dim_feedforward=ff_dim,
                dropout=dropout,
                batch_first=True,
                activation="gelu",
                norm_first=True,
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
            self.norm = nn.LayerNorm(d_model)
            self.head = nn.Sequential(
                nn.Linear(d_model, d_model // 2),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(d_model // 2, 1),
            )

        def forward(self, x):
            # x: [batch, seq_len, input_dim]
            x = self.input_proj(x)
            x = x + self.pos_embed[:, : x.shape[1], :]
            x = self.encoder(x)
            x = self.norm(x[:, -1, :])  # classify from most recent timestep
            logits = self.head(x).squeeze(-1)
            return logits

    return HABTransformerClassifier()
