# DPA-2 wrapper

Target checkpoint: `OpenLAM_2.1.0_27heads_2024Q1.pt`, branch `Domains_SSE-PBE`.

`DPA2RepformerRecursor` targets the DeePMD-kit `2024Q1` Repformer ABI used by this checkpoint.
The recursive state contains invariant atom features `g1`, invariant pair features `g2`, and polar
vector pair features `h2`. Neighbor lists, masks, switching weights, type embeddings, and mapping
remain fixed. One additional `K` repeats the complete ordered Repformer layer sequence after
irrep-level norm alignment to the first-pass input state.

Use `installed()` to replace `repformers.forward` only for a scoped native model call. `K=0` runs
the official preprocessing and layer sequence once; it must reproduce the official branch output
before `K>0` results are accepted. Current releases of DeePMD-kit use a different private rotation
helper and are deliberately rejected by the real validation workflow rather than treated as ABI
compatible.
