# Lossless v0.14.4 control capture copy

The detailed original capture is preserved byte for byte in the gzip tar part.
All members were decompressed and hashed against manifest.json. Original
capture paths remain intact. This is storage, not qualification.

Concatenate the ordered parts to a new archive, then extract into a new empty
directory. The sole part is listed in manifest.json. Compare every extracted
member against its recorded SHA-256. Never extract over retained originals.
