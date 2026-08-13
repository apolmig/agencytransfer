# Controlled evidence archive recipient

`wave1a-recipient.pem` is the public X.509 recipient certificate for encrypted
Wave 1A evidence. Its matching private key is held outside GitHub in the
project owner's private Library; it must never be committed or copied into an
Actions log.

The controlled workflow scans the plaintext evidence, packages it as a ZIP,
and encrypts it as CMS AuthEnvelopedData with AES-256-GCM before uploading a
content-addressed ciphertext to the private control repository. Receipts bind
the plaintext ZIP, ciphertext, certificate, public code commit, private
control-plane commit, source revision, and workflow run.

Certificate SHA-256:

`95526ff55bc63558ceea06aaa0e1b2dc2fcb9c62c9efae78b93e366f9604619a`

Certificate fingerprint:

`A2:98:D4:44:12:1A:49:8B:FB:B0:5C:0A:59:7E:8C:1A:88:75:10:C3:B2:25:DE:9E:C9:70:F0:27:F4:B4:C9:14`

The certificate expires on 10 August 2036. Actions artifacts are temporary
operational copies, not the durable archive and not publication permission.
