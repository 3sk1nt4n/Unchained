# Unchained DFIR Report - COMPLETE

## Verification scope

This system has no deterministic validator by design. Code verifies protocol structure, custody receipts, exact evidence spans, and status monotonicity; forensic meaning still requires analyst review.

## Case profile

- OS route: `windows`
- Evidence shape: `both`
- Capability: Windows tested path \- memory ready\, disk raw\-only
- Evidence items: 4
- Ready tool families: volatility3\.windows

## Executive summary (model-authored, nonauthoritative)

Memory evidence strongly supports that the Print Spooler process was hosting injected or reflectively loaded executable content\. The evidence establishes suspicious private executable memory but does not identify the payload\, its source\, or the responsible injector\. A short\-lived\, highly privileged process is a plausible precursor because it possessed capabilities consistent with process injection\; however\, no direct artifact links it to the spooler\. Targeted follow\-up queries did not recover corroborating process artifacts\, leaving attribution unsupported rather than disproved\.

## Investigative narrative (model-authored, nonauthoritative)

The investigation was led by the hypothesis that the Print Spooler process had been compromised in memory\. The process was observed at the expected system path with a recorded parent identifier\, while memory inspection identified private read\-write\-execute allocations containing shellcode\-like 64\-bit instruction bytes and MZ\-bearing content\. Taken together\, these observations strongly support in\-memory injection or reflective loading\. The available lineage evidence does not itself identify the recorded parent as the Services process\, and the conclusion rests on memory evidence without disk corroboration\.\\n\\nA secondary line of inquiry assessed a short\-lived process as a possible injector\. It existed for approximately 15 seconds and reported a parent that was not recovered through the targeted follow\-up\. Its security context included remote\-interactive\, domain\-administrator\, and high\-integrity attributes\, together with enabled debug privilege\. This establishes that the process had privileged capability consistent with accessing or manipulating another process\, but capability alone does not demonstrate that it acted against the spooler\. No direct process relationship\, injection artifact\, recovered executable path\, or command line connected the candidate to the compromised process\.\\n\\nTargeted examination of the exited candidate produced no environment\, loaded\-module\, or handle records\. Separate command\-line and security\-identifier queries for its reported parent also produced no records\. These non\-affirmative results do not establish benign activity and do not show that the artifacts never existed\; process termination\, memory degradation\, or artifact loss may account for their absence\. Accordingly\, the candidate\-injector theory remains uncorroborated by direct evidence\.

## Findings

| ID | Finding | Severity | Investigator | Judge | Tool calls | Evidence spans |
|---|---|---|---|---|---|---|
| F\-001 | Private executable payload regions in Print Spooler | CRITICAL | CONFIRMED | CONFIRMED | [call_aWrX9WEYr0p9ymq3VDBspZLT] [call_seBSqqV33GWbBEjOLgdgGPm5] | `Se77223761f656bccf8cdef39` `Sc272bf780bd4c2000b75e18f` `S009d6882de3732e5af5e8bb1` |
| F\-002 | Privileged short\-lived coreupdater\.exe is a candidate precursor\, not a proven injector | HIGH | NEEDS-REVIEW | NEEDS-REVIEW | [call_YpxMbPCbSUO0RmyIXwpDUAAZ] [call_hg8h31KWsN3X0LEIiiU0Fi4e] [call_vSkdiUTqADdz97KWkCHOwV7N] | `Sd852075ce534b2a089016745` `Sbe6e45e70e8c79623198193d` `S72cbcedc40085c03114c7618` `S0c6eb0e2de77fb210c213373` `Sa155948718fbba7dc3f81200` |
| F\-003 | Candidate\-injector attribution could not be corroborated | MEDIUM | UNSUPPORTED | UNSUPPORTED | [call_sYArmqYcWJPDl7gksUbiLZdn] [call_5Pc6suWYDyQDHJCtmJfhDXM8] [call_m3LAFPx2BXvlnAeBuuvFPCZA] [call_P8LYdSDp7R5NWuF9ztuskWea] [call_pQdoXUv4Owc3L5RyQpS6cGaK] | `Sc92767857e938b236485aec0` `S601531e9f7ffc946727ffda2` `Sa348cbd20d729ccc8d63fb0d` `Sfe4f342a020ff42102fc282d` `Se507d0f0d7f955a710e469d0` |

## IOC list

| Finding | IOC |
|---|---|
| F\-001 | spoolsv\.exe |
| F\-001 | PID 3724 |
| F\-001 | C\:\\\\Windows\\\\System32\\\\spoolsv\.exe |
| F\-002 | coreupdater\.ex |
| F\-002 | PID 3644 |
| F\-002 | PPID 2244 |
| F\-003 | coreupdater\.ex |
| F\-003 | PID 3644 |
| F\-003 | PID 2244 |

The process names\, identifiers\, parent identifier\, and system path supplied with the findings are useful pivots for validation against independent endpoint\, identity\, and network telemetry\. They should be treated as investigative indicators rather than standalone proof of attribution\, particularly because the candidate process name was recovered from volatile memory and no corresponding path or disk artifact was available\.

## Evidence spans

- `Se77223761f656bccf8cdef39` from [call_aWrX9WEYr0p9ymq3VDBspZLT], artifact `ea5e9a2d18f5cc9b4fa48a266e9be5a43d6b0bef9d50a0642f46cbc37fcaad1e`, bytes 4051:4174, occurrences 1
  - Evidence text: \\\&quot\;ImageFileName\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;\,\\\&quot\;Offset\(V\)\\\&quot\;\:246292267448576\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;PPID\\\&quot\;\:452\,\\\&quot\;Path\\\&quot\;\:\\\&quot\;C\:\\\\\\\\Windows\\\\\\\\System32\\\\\\\\spoolsv\.exe\\\&quot\;
- `Sc272bf780bd4c2000b75e18f` from [call_seBSqqV33GWbBEjOLgdgGPm5], artifact `c0ae7ba27657d7b166993c465c55fe7fe7edde2bef0319dcf651cc7901e4f104`, bytes 4168:4371, occurrences 1
  - Evidence text: \\\&quot\;Hexdump\\\&quot\;\:\\\&quot\;fc 48 89 ce 48 81 ec 00 20 00 00 48 83 e4 f0 e8 cc 00 00 00 41 51 41 50 52 51 56 48 31 d2 65 48 8b 52 60 48 8b 52 18 48 8b 52 20 48 8b 72 50 48 0f b7 4a 4a 4d 31 c9 48 31 c0 ac 3c 61 7c 02 2c\\\&quot\;
- `S009d6882de3732e5af5e8bb1` from [call_seBSqqV33GWbBEjOLgdgGPm5], artifact `c0ae7ba27657d7b166993c465c55fe7fe7edde2bef0319dcf651cc7901e4f104`, bytes 5008:5118, occurrences 3
  - Evidence text: \\\&quot\;Notes\\\&quot\;\:\\\&quot\;MZ header\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;PrivateMemory\\\&quot\;\:1\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;\,\\\&quot\;Protection\\\&quot\;\:\\\&quot\;PAGE\_EXECUTE\_READWRITE\\\&quot\;
- `Sd852075ce534b2a089016745` from [call_YpxMbPCbSUO0RmyIXwpDUAAZ], artifact `27c61e09c990f16517ae75ee31d7cb43693f4400ab27c880b42e89fa8077b4ed`, bytes 5939:6136, occurrences 1
  - Evidence text: \\\&quot\;CreateTime\\\&quot\;\:\\\&quot\;2020\-09\-19T03\:56\:37\+00\:00\\\&quot\;\,\\\&quot\;ExitTime\\\&quot\;\:\\\&quot\;2020\-09\-19T03\:56\:52\+00\:00\\\&quot\;\,\\\&quot\;File output\\\&quot\;\:\\\&quot\;Disabled\\\&quot\;\,\\\&quot\;Handles\\\&quot\;\:null\,\\\&quot\;ImageFileName\\\&quot\;\:\\\&quot\;coreupdater\.ex\\\&quot\;\,\\\&quot\;Offset\(V\)\\\&quot\;\:545441536\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;PPID\\\&quot\;\:2244
- `Sbe6e45e70e8c79623198193d` from [call_hg8h31KWsN3X0LEIiiU0Fi4e], artifact `39e498916d1be8e28d79cb6137380aeb02104ee025c144995489d7090110212e`, bytes 724:812, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;Remote Interactive Logon\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;coreupdater\.ex\\\&quot\;\,\\\&quot\;SID\\\&quot\;\:\\\&quot\;S\-1\-5\-14\\\&quot\;
- `S72cbcedc40085c03114c7618` from [call_hg8h31KWsN3X0LEIiiU0Fi4e], artifact `39e498916d1be8e28d79cb6137380aeb02104ee025c144995489d7090110212e`, bytes 1494:1608, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;Domain Admins\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;coreupdater\.ex\\\&quot\;\,\\\&quot\;SID\\\&quot\;\:\\\&quot\;S\-1\-5\-21\-2232410529\-1445159330\-2725690660\-512\\\&quot\;
- `S0c6eb0e2de77fb210c213373` from [call_hg8h31KWsN3X0LEIiiU0Fi4e], artifact `39e498916d1be8e28d79cb6137380aeb02104ee025c144995489d7090110212e`, bytes 2134:2222, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;High Mandatory Level\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;coreupdater\.ex\\\&quot\;\,\\\&quot\;SID\\\&quot\;\:\\\&quot\;S\-1\-16\-12288\\\&quot\;
- `Sa155948718fbba7dc3f81200` from [call_vSkdiUTqADdz97KWkCHOwV7N], artifact `ee5bfa841cc003e93cc729c6618218dfdaead50656f39a1c9df3c5ac7e8cd4ce`, bytes 3053:3183, occurrences 1
  - Evidence text: \\\&quot\;Attributes\\\&quot\;\:\\\&quot\;Present\,Enabled\\\&quot\;\,\\\&quot\;Description\\\&quot\;\:\\\&quot\;Debug programs\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;Privilege\\\&quot\;\:\\\&quot\;SeDebugPrivilege\\\&quot\;\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;coreupdater\.ex\\\&quot\;
- `Sc92767857e938b236485aec0` from [call_sYArmqYcWJPDl7gksUbiLZdn], artifact `4a939973aa50b39942baffd55aa2784e4621cd1fffc976d805681aa935ed839b`, bytes 46:99, occurrences 1
  - Evidence text: \\\&quot\;output\\\&quot\;\:\[\]\,\\\&quot\;record\_count\\\&quot\;\:0\,\\\&quot\;tool\_name\\\&quot\;\:\\\&quot\;vol\_envars\\\&quot\;
- `S601531e9f7ffc946727ffda2` from [call_5Pc6suWYDyQDHJCtmJfhDXM8], artifact `a8a97a4b292a85a5e823e691f0a2e3bb692c19ae308afe19be413d22b7ab5ce5`, bytes 47:101, occurrences 1
  - Evidence text: \\\&quot\;output\\\&quot\;\:\[\]\,\\\&quot\;record\_count\\\&quot\;\:0\,\\\&quot\;tool\_name\\\&quot\;\:\\\&quot\;vol\_dlllist\\\&quot\;
- `Sa348cbd20d729ccc8d63fb0d` from [call_m3LAFPx2BXvlnAeBuuvFPCZA], artifact `25c09ad24ddadd5b8c48ce27d2c5fba79e0f61825e896c44f26fc35ddb3c7ead`, bytes 48:102, occurrences 1
  - Evidence text: \\\&quot\;output\\\&quot\;\:\[\]\,\\\&quot\;record\_count\\\&quot\;\:0\,\\\&quot\;tool\_name\\\&quot\;\:\\\&quot\;vol\_handles\\\&quot\;
- `Sfe4f342a020ff42102fc282d` from [call_P8LYdSDp7R5NWuF9ztuskWea], artifact `0ba99ab3ae727ecb4a7b526b640c2007888b7cedf798f7d38d49541ce6cc0022`, bytes 46:100, occurrences 1
  - Evidence text: \\\&quot\;output\\\&quot\;\:\[\]\,\\\&quot\;record\_count\\\&quot\;\:0\,\\\&quot\;tool\_name\\\&quot\;\:\\\&quot\;vol\_cmdline\\\&quot\;
- `Se507d0f0d7f955a710e469d0` from [call_pQdoXUv4Owc3L5RyQpS6cGaK], artifact `cae15b4306d516a7c9a79c5113098f1d05e410876afcef8b57eef31122c0bad5`, bytes 47:101, occurrences 1
  - Evidence text: \\\&quot\;output\\\&quot\;\:\[\]\,\\\&quot\;record\_count\\\&quot\;\:0\,\\\&quot\;tool\_name\\\&quot\;\:\\\&quot\;vol\_getsids\\\&quot\;

## Limitations

- Analysis was effectively memory\-only\; the disk container was raw\-only\/mount\-unavailable in the supplied profile\.
- The attempted MFT analysis failed because no Volatility plugin was mapped \[call\_nFTGNgt1IC1i6z3Nqylv4YMx\]\.
- No cross\-domain corroboration was possible\.
- Payload family\, injector\, remote peer\, and persistence mechanism remain unresolved\.
- Large network and file\-scan outputs were not sufficient to attribute a peer or payload path\.
- Memory evidence alone does not identify the payload family\, source file\, or injector\.
- No disk\-domain corroboration was available\.
- No recovered path\, command line\, process handle\, or direct relation to PID 3724\.
- Privilege demonstrates capability\, not use\.
- Zero recovered records may reflect process termination and artifact loss\; they do not prove benign activity or that objects never existed\.
- Single\-domain memory finding\; no disk corroboration\.
- The supplied span does not explicitly identify PPID 452 as services\.exe\.
- Capability is not causation\.
- No direct relation to spoolsv\.exe PID 3724 is supplied\.
- Single\-domain memory evidence\.
- Zero\-record results are non\-affirmative\.
- Process termination or artifact loss may explain missing records\.
- No direct injector artifact is supplied\.
- The effective analysis domain was memory\. The disk container could not be mounted or resolved\, the attempted filesystem metadata analysis had no mapped capability\, and no cross\-domain corroboration was available\. Missing records from targeted memory queries are inherently inconclusive\, especially for terminated processes\. The payload family and source\, responsible injector\, candidate executable path and purpose\, identity of the reported parent\, remote peer\, persistence mechanism\, and any command\-and\-control activity remain unresolved\. Available network and file\-scan results were insufficient to attribute a peer or payload path\.
- Offline bundle verification cannot authenticate self-recorded provider IDs.
- Recorded custody verification is not a fresh rehash of originals by an offline recipient.

## Unresolved questions

- What payload or family occupies the private executable regions in PID 3724\?
- Who or what injected or reflectively loaded the spooler payload\?
- What was the executable path and purpose of coreupdater\.exe PID 3644\?
- What process was parent PID 2244\?
- Was there persistence or external command\-and\-control activity\?
