# E002 addendum — M3 BLOCKED, M3b added (written before M3b runs)

M3 (x86_64 under colima qemu binfmt) came out BLOCKED, not PASS. jaxlib 0.10.2 needs AVX
and the qemu CPU model does not offer it (`RuntimeError: This version of jaxlib was built
using AVX instructions...`). jaxlib 0.10.2 has no macOS x86_64 wheel, so Rosetta on the
host is not an option either.

M3b: same container script, linux/amd64 through a separate colima profile `torax-x86`
(vz + Rosetta, which offers AVX/AVX2 on current macOS). The default profile is not touched.

| ID | Expected under H | Reading |
|---|---|---|
| M3b | restart0-3 all PASS | PASS: consistent with x86_64 passing, as upstream CI does. That supports "follows arm64". FAIL on restart1/2 is ambiguous: Rosetta's CPU feature set (e.g. FMA) may differ from CI runners, so it does not falsify H. It does falsify "x86_64 is immune under every feature set". restart0/3 failing, or jaxlib not loading, makes M3b INVALID/BLOCKED. |
