# JARVIS-DFT 2021 source

`jarvis_2021.json` fixes Figshare file 29204826, official MD5, byte count and JSON member.
It is the 55,722-structure snapshot used for the original ALIGNN task table.
Official metadata: https://api.figshare.com/v2/articles/6815699

The ZIP and unpacked records are generated inputs and are ignored by Git.
Preprocessing records local SHA-256, graph IDs, failures, label exclusion counts and actual splits.
Tasks come from the 29 rows of the official regression table, not the smaller train_all_jv script.
For piezoelectric dij, the published unit string is retained as dataset-native; no unverified
scale factor is introduced. Any later conversion requires a separately documented data audit.
