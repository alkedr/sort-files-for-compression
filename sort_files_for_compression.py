import math
import os
import sys
import tarfile


with tarfile.open(fileobj=sys.stdin.buffer, mode='r:', ignore_zeros=True) as input_tar:
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w:') as output_tar:
        members = [
            (
                # Put hard links at the end because to create a hard link, target must already exist.
                member.islnk(),

                # Group by type (regular file, dir, symlink, hardlink etc).
                # tar blocks with symlinks, hardlinks, devices etc are likely to have something in common.
                member.type,

                # Group by file extension.
                # Files with the same extension are likely to have something in common.
                os.path.splitext(member.name)[1],

                # Group into buckets by size.
                int(math.log(member.size + 1, 1024)),

                # Group by full path.
                # Files in the same directory are likely to have something in common.
                # This key also doubles as a catch-all comparison key that will prevent comparing member objects.
                # Technically tar supports multiple files with the same name but this script doesn't support it.
                member.name,

                member,
            )
            for member in input_tar.getmembers()
        ]
        sorted_members = [
            member[-1]
            for member in sorted(members)
        ]
        for member in sorted_members:
            # print(member, file=sys.stderr)
            output_tar.addfile(
                tarinfo=member,
                fileobj=input_tar.extractfile(member=member) if member.isfile() else None,
            )
