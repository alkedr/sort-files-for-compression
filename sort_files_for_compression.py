import math
import os
import random
import sys
import tarfile
import magic


with tarfile.open(fileobj=sys.stdin.buffer, mode='r:', ignore_zeros=True) as input_tar:
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w:') as output_tar:
        members = [
            (
                # Put hard links at the end because to create a hard link, target must already exist.
                member.islnk(),

                # Group by type (regular file, dir, symlink, hardlink etc).
                # tar blocks with symlinks, hardlinks, devices etc are likely to have something in common.
                # member.type,

                magic.from_buffer(buffer=input_tar.extractfile(member=member).read(), mime=True).split('/')[0] if member.isfile() else '',

                # Binaries
                # os.path.dirname(member.name).endswith('/bin'),
                #
                # # .so
                # '.so' in os.path.basename(member.name),
                #
                # # Group by file extension.
                # # Files with the same extension are likely to have something in common.
                # # os.path.splitext(member.name)[1],
                #
                # # Group into buckets by size.
                # int(math.log(member.size + 1, 1024)),

                # Group by full path.
                # Files in the same directory are likely to have something in common.
                # This key also doubles as a catch-all comparison key that will prevent comparing member objects.
                # Technically tar supports multiple files with the same name but this script doesn't support it.
                member.name,

                member,
            )
            for member in input_tar.getmembers()
        ]

        mime_to_members = {}
        for member in members:
            if member[1] not in mime_to_members:
                mime_to_members[member[1]] = []
            mime_to_members[member[1]].append(member)

        for mime in sorted(mime_to_members):
            print(
                f'{mime} {len(mime_to_members[mime])}, {sum([member[-1].size for member in mime_to_members[mime]]):_}',
                file=sys.stderr,
            )
            for member in random.choices(mime_to_members[mime], k=min(5, len(mime_to_members[mime]))):
                print(f'  {member[-1].name}', file=sys.stderr)

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
