# Feature cache

`publish_cache(root, identity, ids, produce, shard_size)` takes a label-free inference callback.
It atomically writes float32 node shards with per-structure offsets and SHA-256 receipts.
Restart verifies receipts before reusing completed shards; incompatible inputs are rejected.
Only a verified complete library gets a `manifest.json` with status `complete`.

`FeatureStore(root, expected)` checks exact identity and parent/checkpoint dependencies,
IDs, hashes, widths, offsets, finite values and dtype. Node counts are checked against geometry.
Shards are memoized for efficient random access; `verify_all` rechecks on-disk hashes.
The caller must supply identities containing task, seed, round, checkpoint, graph, split,
config and parent-cache hashes. Read-only consumers must not modify returned tensor views.
