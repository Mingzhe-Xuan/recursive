# Paired archives

Archive(root, expected) provides get(jid, atoms), batch(ids, graphs, device, with_nodes)
and verify_all(). Shards contain float32 post-convolution node features, original-unit
cumulative predictions, IDs and offsets. Manifest binds parent/checkpoint/config/source
identity, SHA256, byte counts and full ID/atom coverage. No labels are used in production.
publish() validates before publishing a complete manifest and resumes checked partial shards.
