/*
 * Bounded diagnostic for the KERN_PROC_PID record ABI only.
 * This is not a process-table provider or a cleanup/qualification tool.
 */
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <sys/proc.h>
#include <sys/sysctl.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <unistd.h>

#if !defined(__APPLE__) || !defined(__LP64__)
#error "This diagnostic supports only LP64 macOS"
#endif

_Static_assert(sizeof(void *) == 8, "expected LP64 pointers");
_Static_assert(sizeof(pid_t) <= sizeof(int), "KERN_PROC_PID MIB must carry pid_t");

static int
valid_birth(const struct timeval *start)
{
    return start->tv_sec > 0 &&
           start->tv_usec >= 0 &&
           start->tv_usec < 1000000;
}

static int
probe_pid(pid_t requested_pid)
{
    int mib[] = { CTL_KERN, KERN_PROC, KERN_PROC_PID, (int)requested_pid };
    struct kinfo_proc row;
    size_t returned_bytes = sizeof(row);
    int rc;
    int saved_errno;
    int valid;
    size_t i;

    memset(&row, 0, sizeof(row));
    errno = 0;
    rc = sysctl(mib, (u_int)(sizeof(mib) / sizeof(mib[0])),
                &row, &returned_bytes, NULL, 0);
    saved_errno = errno;

    printf("query requested_pid=%ld rc=%d errno=%d returned_bytes=%zu record_size=%zu\n",
           (long)requested_pid, rc, saved_errno, returned_bytes, sizeof(row));
    if (rc != 0) {
        return 1;
    }
    if (returned_bytes != sizeof(row)) {
        printf("reject reason=record_length_mismatch\n");
        return 1;
    }

    printf("row pid=%ld ppid=%ld start_sec=%lld start_usec=%lld state=%u p_comm_hex=",
           (long)row.kp_proc.p_pid,
           (long)row.kp_eproc.e_ppid,
           (long long)row.kp_proc.p_starttime.tv_sec,
           (long long)row.kp_proc.p_starttime.tv_usec,
           (unsigned int)(unsigned char)row.kp_proc.p_stat);
    for (i = 0; i < sizeof(row.kp_proc.p_comm); ++i) {
        printf("%02x", (unsigned int)(unsigned char)row.kp_proc.p_comm[i]);
    }
    putchar('\n');

    valid = row.kp_proc.p_pid == requested_pid &&
            row.kp_proc.p_pid > 0 &&
            row.kp_eproc.e_ppid >= 0 &&
            valid_birth(&row.kp_proc.p_starttime) &&
            row.kp_proc.p_stat >= SIDL && row.kp_proc.p_stat <= SZOMB &&
            row.kp_proc.p_comm[0] != '\0' &&
            memchr(row.kp_proc.p_comm, '\0', sizeof(row.kp_proc.p_comm)) != NULL;
    if (!valid) {
        printf("reject reason=row_identity_or_required_field_invalid\n");
        return 1;
    }
    printf("accept exact_single_record=1\n");
    return 0;
}

int
main(void)
{
    struct utsname system_info;
    pid_t requested[2];
    int failures = 0;

    if (sizeof(void *) != 8 || uname(&system_info) != 0) {
        perror("platform_metadata");
        return 2;
    }
    printf("platform=macOS kernel_release=%s kernel_version=%s machine=%s lp64=1 pointer_bytes=%zu kinfo_proc_bytes=%zu\n",
           system_info.release, system_info.version, system_info.machine,
           sizeof(void *), sizeof(struct kinfo_proc));

    requested[0] = (pid_t)10491;
    requested[1] = getpid();
    failures |= probe_pid(requested[0]);
    failures |= probe_pid(requested[1]);
    return failures ? 1 : 0;
}
