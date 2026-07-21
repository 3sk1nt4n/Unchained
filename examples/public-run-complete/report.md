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

The memory review supports privileged in\-memory compromise of PID 3724\, spoolsv\.exe\. The process used the expected System32 image identity\, yet contained private executable\-read\-write memory and repeated MZ\-header indications while running as Local System\. A short\-lived\, highly privileged process associated with coreupdater\.exe is a credible investigative lead\, but the available evidence does not establish malicious conduct or a causal relationship to the spooler compromise\. Broader conclusions were constrained by memory\-only evidence and unsuccessful disk and timeline corroboration\.

## Investigative narrative (model-authored, nonauthoritative)

The host evidence identified Active Directory Domain Services\, although the supplied passage does not establish that the service was running\. Within PID 3724\, the expected spoolsv\.exe System32 path was present\. Memory analysis identified private executable\-read\-write regions and repeated MZ\-header annotations\, and the process token showed Local System membership\. These facts support the conclusion that a highly privileged service process contained anomalous executable content\. The supplied passages do not expose the asserted shellcode bytes\, identify the payloads\, or establish how the content entered the process\.\\n\\nPID 3644\, shown as coreupdater\.ex with an audit path ending in coreupdater\.exe\, existed for approximately 15 seconds\. Its token reflected the built\-in Administrator identity\, Domain Admins and Enterprise Admins memberships\, and enabled SeDebugPrivilege\. This establishes substantial access and technical capability\, but not malicious purpose\, injection activity\, or linkage to PID 3724\. Schema Admin membership was not demonstrated by the supplied evidence\, and the executable path could not be validated against a disk file\, signature\, or hash\.\\n\\nThe reviewed spooler artifacts included an expected command line\, expected spoolsv\.exe and ntdll\.dll loader entries\, and a routine\-looking RouterPreInitEvent handle\. These scoped examples do not exhaustively exclude masquerading or a loader\-linked rogue module\, and they do not prove manual mapping\. Accordingly\, the conventional rogue\-DLL or masquerading hypothesis was not affirmatively established or eliminated by the available passages\.\\n\\nTwo intended corroboration routes did not complete\: the filescan worker returned an error\, and the requested MFT scan lacked a mapped Volatility plugin\. These failures document unavailable results from those methods\, but do not demonstrate that every possible corroboration method was exhausted\.

## Findings

| ID | Finding | Severity | Investigator | Judge | Tool calls | Evidence spans |
|---|---|---|---|---|---|---|
| F\-001 | Private executable payloads in SYSTEM spoolsv\.exe on a domain controller | CRITICAL | CONFIRMED | CONFIRMED | [call_Qen5TG5rgblsG89hSbVk0aC5] [call_djYKowIct7A13ZEK8ktvN73s] [call_JZD6wOvLZMULlOPRrnjkuSXH] [call_YI6sBmsQBYBQZxTpi2hOfsUd] | `S2bbeb6f412828da8b9d0409d` `S40c277cc4905b1579b6e0c87` `S923301e1f2154978d350cfbb` `S5d46ac1351402cda0d6b93bc` `S73a31bec65df9e6f3439d3ae` `Sde22253318cf49d9d12d95dc` |
| F\-002 | Highly privileged short\-lived coreupdater\.exe is a credible but unlinked precursor | HIGH | NEEDS-REVIEW | NEEDS-REVIEW | [call_19UWjHJjNeOqBgAvvdDD0G5y] [call_djYKowIct7A13ZEK8ktvN73s] [call_sJSVDkSBa13vTxusIVfttZj5] [call_lzWgd6jrTfAcISaUvlqdMU7G] | `S68332cb89ae783ab900d3d18` `S8b36e04350af11b4a8f43ee1` `S40a5711f6e37ae922d2a5458` `Sfb79b25752523032fdfebf9e` `Sf0b040056b8a0196d9bf141c` `S586afb1720e61168858edba3` |
| F\-003 | Conventional spooler masquerading or loader\-linked rogue DLL hypothesis not supported | INFORMATIONAL | UNSUPPORTED | UNSUPPORTED | [call_69Pg38WAL5sr8z4cTS4f7zj1] [call_sj0bigduEMv5o00IZ2XTXUjP] [call_JmaDTqVTNYKzDfZx1jFHMHw7] | `S84a23da33e4f4d2f129be2a2` `S78c427587f2992490de24c59` `S89e0e260bd3498121954fa53` `S935d75848e65dac2bba0ed26` |
| F\-004 | Disk and memory\-timeline corroboration could not be completed | INFORMATIONAL | NEEDS-REVIEW | NEEDS-REVIEW | [call_5GBEodP5tpzoVBvWRDteFCIW] [call_vorq76abso1Fib9TP3lVWL8K] | `S26346b8023ac736faee91d4f` `S1aa1d41b987b233741e8e5d3` |

## IOC list

| Finding | IOC |
|---|---|
| F\-001 | spoolsv\.exe |
| F\-001 | PID 3724 |
| F\-001 | C\:\\\\Windows\\\\System32\\\\spoolsv\.exe |
| F\-001 | RWX VPN 322054520832 |
| F\-001 | RWX VPN 322055897088 |
| F\-001 | RWX VPN 322057469952 |
| F\-001 | RWX VPN 322057928704 |
| F\-002 | coreupdater\.exe |
| F\-002 | coreupdater\.ex |
| F\-002 | PID 3644 |
| F\-002 | \\\\Device\\\\HarddiskVolume2\\\\Windows\\\\System32\\\\coreupdater\.exe |
| F\-002 | S\-1\-5\-21\-2232410529\-1445159330\-2725690660\-500 |

The principal investigative focus is the anomalous executable memory within the privileged spooler process and the separate short\-lived coreupdater process\. These artifacts should be used as pivots for payload recovery\, process\-interaction analysis\, file validation\, execution\-history review\, and persistence hunting if additional evidence becomes available\.

## Evidence spans

- `S2bbeb6f412828da8b9d0409d` from [call_Qen5TG5rgblsG89hSbVk0aC5], artifact `6eeeb2fa7bbb767ff454fa7d2a94519dba41490f5f6afbadc0ce76b44f6791fd`, bytes 12885:12985, occurrences 2
  - Evidence text: \\\&quot\;Display\\\&quot\;\:\\\&quot\;Active Directory Domain Services\\\&quot\;\,\\\&quot\;Dll\\\&quot\;\:\\\&quot\;\%systemroot\%\\\\\\\\system32\\\\\\\\ntdsa\.dll\\\&quot\;\,\\\&quot\;Name\\\&quot\;\:\\\&quot\;NTDS\\\&quot\;
- `S40c277cc4905b1579b6e0c87` from [call_djYKowIct7A13ZEK8ktvN73s], artifact `0cca024efa7f1255c98aa63461bae5fed9b824cc669c8de190b22fdbf099198e`, bytes 4051:4174, occurrences 1
  - Evidence text: \\\&quot\;ImageFileName\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;\,\\\&quot\;Offset\(V\)\\\&quot\;\:246292267448576\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;PPID\\\&quot\;\:452\,\\\&quot\;Path\\\&quot\;\:\\\&quot\;C\:\\\\\\\\Windows\\\\\\\\System32\\\\\\\\spoolsv\.exe\\\&quot\;
- `S923301e1f2154978d350cfbb` from [call_JZD6wOvLZMULlOPRrnjkuSXH], artifact `ecea9451f2c28e5e0dd12f06034344ba6857cc3f931aa82a75fb11611a103d16`, bytes 4385:4475, occurrences 4
  - Evidence text: \\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;PrivateMemory\\\&quot\;\:1\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;\,\\\&quot\;Protection\\\&quot\;\:\\\&quot\;PAGE\_EXECUTE\_READWRITE\\\&quot\;
- `S5d46ac1351402cda0d6b93bc` from [call_JZD6wOvLZMULlOPRrnjkuSXH], artifact `ecea9451f2c28e5e0dd12f06034344ba6857cc3f931aa82a75fb11611a103d16`, bytes 5008:5080, occurrences 3
  - Evidence text: \\\&quot\;Notes\\\&quot\;\:\\\&quot\;MZ header\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;PrivateMemory\\\&quot\;\:1\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;
- `S73a31bec65df9e6f3439d3ae` from [call_YI6sBmsQBYBQZxTpi2hOfsUd], artifact `0708ffef002728f2a985a4b074b584d2d7f2764650a3fe2a640694c65352368c`, bytes 58:131, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;Local System\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;\,\\\&quot\;SID\\\&quot\;\:\\\&quot\;S\-1\-5\-18\\\&quot\;
- `Sde22253318cf49d9d12d95dc` from [call_YI6sBmsQBYBQZxTpi2hOfsUd], artifact `0708ffef002728f2a985a4b074b584d2d7f2764650a3fe2a640694c65352368c`, bytes 1329:1408, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;Administrators\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;\,\\\&quot\;SID\\\&quot\;\:\\\&quot\;S\-1\-5\-32\-544\\\&quot\;
- `S68332cb89ae783ab900d3d18` from [call_19UWjHJjNeOqBgAvvdDD0G5y], artifact `bbd36150f366514a58fab45b9c0b82c5ff55a183b643d5f44e51a0738a1b8398`, bytes 5939:6018, occurrences 2
  - Evidence text: \\\&quot\;CreateTime\\\&quot\;\:\\\&quot\;2020\-09\-19T03\:56\:37\+00\:00\\\&quot\;\,\\\&quot\;ExitTime\\\&quot\;\:\\\&quot\;2020\-09\-19T03\:56\:52\+00\:00\\\&quot\;
- `S8b36e04350af11b4a8f43ee1` from [call_djYKowIct7A13ZEK8ktvN73s], artifact `0cca024efa7f1255c98aa63461bae5fed9b824cc669c8de190b22fdbf099198e`, bytes 13075:13157, occurrences 1
  - Evidence text: \\\&quot\;Audit\\\&quot\;\:\\\&quot\;\\\\\\\\Device\\\\\\\\HarddiskVolume2\\\\\\\\Windows\\\\\\\\System32\\\\\\\\coreupdater\.exe\\\&quot\;\,\\\&quot\;Cmd\\\&quot\;\:null
- `S40a5711f6e37ae922d2a5458` from [call_sJSVDkSBa13vTxusIVfttZj5], artifact `84307469bb6a7fcfd1b243cfe5cc3994232cc08f32e544c38cc6f9db34f9e57a`, bytes 58:118, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;Administrator\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;coreupdater\.ex\\\&quot\;
- `Sfb79b25752523032fdfebf9e` from [call_sJSVDkSBa13vTxusIVfttZj5], artifact `84307469bb6a7fcfd1b243cfe5cc3994232cc08f32e544c38cc6f9db34f9e57a`, bytes 1494:1554, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;Domain Admins\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;coreupdater\.ex\\\&quot\;
- `Sf0b040056b8a0196d9bf141c` from [call_sJSVDkSBa13vTxusIVfttZj5], artifact `84307469bb6a7fcfd1b243cfe5cc3994232cc08f32e544c38cc6f9db34f9e57a`, bytes 1756:1820, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;Enterprise Admins\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;coreupdater\.ex\\\&quot\;
- `S586afb1720e61168858edba3` from [call_lzWgd6jrTfAcISaUvlqdMU7G], artifact `d816de445694dd96a505855290174553cdacb6e258df43eab295c03cf061b067`, bytes 3053:3156, occurrences 1
  - Evidence text: \\\&quot\;Attributes\\\&quot\;\:\\\&quot\;Present\,Enabled\\\&quot\;\,\\\&quot\;Description\\\&quot\;\:\\\&quot\;Debug programs\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3644\,\\\&quot\;Privilege\\\&quot\;\:\\\&quot\;SeDebugPrivilege\\\&quot\;
- `S84a23da33e4f4d2f129be2a2` from [call_69Pg38WAL5sr8z4cTS4f7zj1], artifact `5e708db2a2cd98d478c0c3f46799dea1221120fbd96badfa9f7c7011de39df3b`, bytes 3497:3575, occurrences 1
  - Evidence text: \\\&quot\;Args\\\&quot\;\:\\\&quot\;C\:\\\\\\\\Windows\\\\\\\\System32\\\\\\\\spoolsv\.exe\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;
- `S78c427587f2992490de24c59` from [call_sj0bigduEMv5o00IZ2XTXUjP], artifact `199e04f0a33cdf2b28ea3eb65b441dce7aeb9dd397b2ec4035cb4f31bbfc1bd9`, bytes 160:235, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;Path\\\&quot\;\:\\\&quot\;C\:\\\\\\\\Windows\\\\\\\\System32\\\\\\\\spoolsv\.exe\\\&quot\;
- `S89e0e260bd3498121954fa53` from [call_sj0bigduEMv5o00IZ2XTXUjP], artifact `199e04f0a33cdf2b28ea3eb65b441dce7aeb9dd397b2ec4035cb4f31bbfc1bd9`, bytes 392:463, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;ntdll\.dll\\\&quot\;\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;Path\\\&quot\;\:\\\&quot\;C\:\\\\\\\\Windows\\\\\\\\SYSTEM32\\\\\\\\ntdll\.dll\\\&quot\;
- `S935d75848e65dac2bba0ed26` from [call_JmaDTqVTNYKzDfZx1jFHMHw7], artifact `fb0888f674bf760f19b4e25be40c1e3e75a86d168866fc94d16833a7b0993df2`, bytes 13684:13771, occurrences 1
  - Evidence text: \\\&quot\;Name\\\&quot\;\:\\\&quot\;RouterPreInitEvent\\\&quot\;\,\\\&quot\;Offset\\\&quot\;\:246292217987872\,\\\&quot\;PID\\\&quot\;\:3724\,\\\&quot\;Process\\\&quot\;\:\\\&quot\;spoolsv\.exe\\\&quot\;
- `S26346b8023ac736faee91d4f` from [call_5GBEodP5tpzoVBvWRDteFCIW], artifact `6c4db43ecc6f39de75a0f09ff9d87a4456911f6b49c5ab7b379f2da54d396b85`, bytes 1:78, occurrences 1
  - Evidence text: \\\&quot\;error\\\&quot\;\:\\\&quot\;isolated Qwen worker exited without a response \(1\)\\\&quot\;\,\\\&quot\;status\\\&quot\;\:\\\&quot\;error\\\&quot\;
- `S1aa1d41b987b233741e8e5d3` from [call_vorq76abso1Fib9TP3lVWL8K], artifact `25da21d0598b6f90d3cd4e55c87d8200e281479821ada1c8bb6bbb34a6ce690c`, bytes 1:83, occurrences 1
  - Evidence text: \\\&quot\;error\\\&quot\;\:\\\&quot\;ValueError\: No Volatility plugin mapped for vol\_mftscan\\\&quot\;\,\\\&quot\;status\\\&quot\;\:\\\&quot\;error\\\&quot\;

## Limitations

- E002 was recognized as a disk container but had no resolved filesystem\, so no cross\-domain corroboration was possible\.
- The investigation was limited to a single memory snapshot\; exited\-process metadata was incomplete\.
- Network output was extremely large and did not yield a reliable PID 3724 endpoint attribution\.
- Payload identity\, injector\, persistence\, external peer\, and parent PID 2244 remain unresolved\.
- Payloads were not dumped or identified\.
- No disk\, persistence\, or network\-peer corroboration was available\.
- The exact injector and injection technique remain unknown\.
- No command line\, modules\, handles\, environment\, or recoverable parent context established its purpose\.
- No direct process\-handle\, thread\, or memory evidence linked PID 3644 to PID 3724\.
- The System32 path was not validated by hash or signature\.
- Loader and handle review cannot exclude unlinked\/manual\-mapped code\.
- Absence of an obvious rogue DLL is not evidence that the process was benign\.
- E002\&\#x27\;s filesystem was unresolved and no disk artifact tools were available\.
- Memory\-only conclusions cannot establish on\-disk provenance\, persistence\, hashes\, or signatures\.
- NTDS running state is not shown in the supplied span\.
- The quoted spans do not show the underlying shellcode\-like bytes\.
- No usable disk\-domain corroboration was available\.
- No supplied span demonstrates Schema Admin membership\.
- Privilege and path establish capability\, not malicious conduct or linkage\.
- Evidence is memory\-only and the executable was not validated on disk\.
- Selected benign\-looking entries cannot prove the absence of rogue entries\.
- The supplied passages are scoped evidence\, not an exhaustive review of native outputs\.
- The errors establish failed attempts\, not exhaustive unavailability of all corroboration methods\.
- The unresolved disk filesystem is described in the case profile but not demonstrated by these two tool\-output spans\.
- The investigation relied primarily on one memory snapshot\. The recognized disk container had no resolved filesystem\, preventing practical cross\-domain validation during this review\. The anomalous memory regions were not dumped or identified\, and no reliable external endpoint attribution was recovered for PID 3724\. The injector\, injection technique\, persistence mechanism\, payload identities\, external peer\, provenance and legitimacy of coreupdater\.exe\, and the identity of PID 2244 remain unresolved\. Selected benign\-looking loader and handle entries cannot establish the absence of malicious entries\, while the failed filescan and MFT attempts do not prove exhaustive unavailability of every alternative method\.
- Offline bundle verification cannot authenticate self-recorded provider IDs.
- Recorded custody verification is not a fresh rehash of originals by an offline recipient.

## Unresolved questions

- What are the identities and hashes of the three PE\-like private mappings and shellcode in PID 3724\?
- Did PID 3644 open or manipulate PID 3724\, and what was PID 2244\?
- How was \`coreupdater\.exe\` introduced\, and is its System32 file signed or persistent\?
- Did PID 3724 communicate externally before acquisition\?
- What persistence or execution artifacts exist on E002\?
