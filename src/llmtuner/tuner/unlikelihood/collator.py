# Authors: Tianchi Cai, Xierui Song 2023

import torch
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple
from transformers import DataCollatorForSeq2Seq


@dataclass
class UnlikelihoodDataCollatorWithPadding(DataCollatorForSeq2Seq):
    r"""
    Data collator for pairwise data.
    """

    def _pad_labels(self, batch: torch.Tensor, positions: List[Tuple[int, int]]) -> torch.Tensor:
        padded_labels = []
        for feature, (prompt_len, answer_len) in zip(batch, positions):
            if self.tokenizer.padding_side == "left":
                start, end = feature.size(0) - answer_len, feature.size(0)
            else:
                start, end = prompt_len, prompt_len + answer_len
            padded_tensor = self.label_pad_token_id * torch.ones_like(feature)
            padded_tensor[start:end] = feature[start:end]
            padded_labels.append(padded_tensor)
        return torch.stack(padded_labels, dim=0).contiguous() # in contiguous memory

    def __call__(self, features: Sequence[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        r"""
        Pads batched data to the longest sequence in the batch.

        """
        concatenated_features = []
        label_positions = []
        for feature in features:
            prompt_len, answer_len = len(feature["input_ids"]), len(feature["output_ids"])
            concatenated_features.append({
                "input_ids": feature["input_ids"] + feature["output_ids"],
                "attention_mask": [1] * (prompt_len + answer_len)
            })
            label_positions.append((prompt_len, answer_len))

        batch = self.tokenizer.pad(
            concatenated_features,
            padding=self.padding,
            max_length=self.max_length,
            pad_to_multiple_of=self.pad_to_multiple_of,
            return_tensors=self.return_tensors,
        )
        batch["labels"] = self._pad_labels(batch["input_ids"], label_positions)
        batch["score"] = torch.FloatTensor([feature["score"] for feature in features])
        return batch
