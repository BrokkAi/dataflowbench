/*
 * Source-only C self-test for darwin_native_provider.c.
 *
 * Build only after independent review and root authorization. Macro
 * redirection replaces the three OS-facing calls before the production C
 * body is included. This file is a separate test executable; it adds no
 * hooks or alternate entry points to the provider dylib.
 */
#define sysctl dfb_test_sysctl
#define proc_pidpath dfb_test_proc_pidpath
#define getpid dfb_test_getpid
#include "darwin_native_provider.c"
#undef sysctl
#undef proc_pidpath
#undef getpid

#include <stdio.h>

#define TEST_FIXTURE_ROWS 4u

typedef struct test_table_fixture {
	struct kinfo_proc rows[TEST_FIXTURE_ROWS];
	size_t row_count;
	int override_returned_length;
	size_t returned_length;
	int error_errno;
} test_table_fixture;

static test_table_fixture g_tables[2];
static int g_self_pid = 70001;
static int g_sysctl_calls;
static int g_path_calls;
static int g_path_fallback_pid = -1;
static int g_path_fallback_errno;
static int g_path_negative_pid = -1;
static int g_path_positive_error_pid = -1;
static int g_path_unterminated_pid = -1;
static int g_path_overbound_pid = -1;
static int g_failures;
static int g_passes;
static dfb_native_row_v4 *g_output_rows;

int
dfb_test_sysctl(int *name, u_int name_length,
	void *old_value, size_t *old_length, void *new_value, size_t new_length)
{
	test_table_fixture *fixture;
	size_t actual_length;
	size_t returned_length;
	size_t copy_length;
	int call_index = g_sysctl_calls++;

	(void)new_value;
	(void)new_length;
	if (name == NULL || name_length != 3 || name[0] != CTL_KERN ||
	    name[1] != KERN_PROC || name[2] != KERN_PROC_ALL ||
	    old_value == NULL || old_length == NULL || call_index > 1) {
		errno = EINVAL;
		return -1;
	}
	fixture = &g_tables[call_index];
	if (fixture->error_errno != 0) {
		errno = fixture->error_errno;
		return -1;
	}
	actual_length = fixture->row_count * sizeof(struct kinfo_proc);
	returned_length = fixture->override_returned_length ?
	    fixture->returned_length : actual_length;
	if (returned_length > *old_length) {
		*old_length = returned_length;
		errno = ENOMEM;
		return -1;
	}
	copy_length = actual_length < returned_length ? actual_length : returned_length;
	if (copy_length != 0) {
		memcpy(old_value, fixture->rows, copy_length);
	}
	*old_length = returned_length;
	errno = 0;
	return 0;
}

int
dfb_test_proc_pidpath(int pid, void *buffer, uint32_t buffer_size)
{
	char path[64];
	int length;

	g_path_calls++;
	if (pid == g_path_fallback_pid) {
		errno = g_path_fallback_errno;
		return 0;
	}
	if (pid == g_path_negative_pid) {
		errno = EPERM;
		return -1;
	}
	if (pid == g_path_overbound_pid) {
		errno = 0;
		return (int)buffer_size + 1;
	}
	length = snprintf(path, sizeof(path), "/synthetic/%d", pid);
	if (length < 0 || (size_t)length >= sizeof(path) ||
	    (uint32_t)length >= buffer_size) {
		errno = ENAMETOOLONG;
		return 0;
	}
	memcpy(buffer, path, (size_t)length + 1u);
	if (pid == g_path_unterminated_pid) {
		((char *)buffer)[length] = 'x';
	}
	errno = pid == g_path_positive_error_pid ? EIO : 0;
	return length;
}

pid_t
dfb_test_getpid(void)
{
	return (pid_t)g_self_pid;
}

static void
reset_fixtures(void)
{
	memset(g_tables, 0, sizeof(g_tables));
	g_sysctl_calls = 0;
	g_path_calls = 0;
	g_path_fallback_pid = -1;
	g_path_fallback_errno = 0;
	g_path_negative_pid = -1;
	g_path_positive_error_pid = -1;
	g_path_unterminated_pid = -1;
	g_path_overbound_pid = -1;
}

static void
set_row(test_table_fixture *table, size_t index, int pid, int ppid,
	int64_t seconds, int64_t microseconds, int state, const char *comm)
{
	struct kinfo_proc *record = &table->rows[index];

	memset(record, 0, sizeof(*record));
	record->kp_proc.p_pid = (pid_t)pid;
	record->kp_eproc.e_ppid = (pid_t)ppid;
	record->kp_proc.p_starttime.tv_sec = (time_t)seconds;
	record->kp_proc.p_starttime.tv_usec = (suseconds_t)microseconds;
	record->kp_proc.p_stat = (char)state;
	if (comm != NULL) {
		(void)snprintf(record->kp_proc.p_comm,
		    sizeof(record->kp_proc.p_comm), "%s", comm);
	}
	if (index >= table->row_count) {
		table->row_count = index + 1u;
	}
}

static void
set_standard_pair(void)
{
	reset_fixtures();
	g_self_pid = 70001;
	set_row(&g_tables[0], 0, g_self_pid, 1, 1700000000, 10, SIDL,
	    "synthetic-self");
	set_row(&g_tables[0], 1, 70002, g_self_pid, 1700000001, 20, SRUN,
	    "synthetic-worker");
	set_row(&g_tables[0], 2, 70003, g_self_pid, 1700000002, 30, SZOMB,
	    "synthetic-zombie");
	g_tables[1] = g_tables[0];
}

static int
expect_status(const char *label, int expected_status, int expected_sysctl_calls)
{
	dfb_native_meta_v3 meta;
	int result;

	g_sysctl_calls = 0;
	g_path_calls = 0;
	memset(g_output_rows, 0xa5, DFB_MAX_ROWS * sizeof(*g_output_rows));
	result = dfb_native_snapshot_v4(g_output_rows, DFB_MAX_ROWS, &meta);
	if (result != expected_status || meta.status != expected_status ||
	    g_sysctl_calls != expected_sysctl_calls ||
	    (expected_status != DFB_STATUS_OK && g_output_rows[0].pid != 0)) {
		(void)fprintf(stderr,
		    "FAIL %s status=%d meta=%d sysctl_calls=%d expected=%d/%d\n",
		    label, result, meta.status, g_sysctl_calls, expected_status,
		    expected_sysctl_calls);
		g_failures++;
		return 0;
	}
	(void)printf("PASS %s\n", label);
	g_passes++;
	return 1;
}

static void
test_complete_positive_and_legacy_states(void)
{
	dfb_native_meta_v3 meta;
	int result;

	set_standard_pair();
	g_path_fallback_pid = 70002;
	g_sysctl_calls = 0;
	g_path_calls = 0;
	result = dfb_native_snapshot_v4(g_output_rows, DFB_MAX_ROWS, &meta);
	if (result != DFB_STATUS_OK || meta.status != DFB_STATUS_OK ||
	    g_sysctl_calls != 2 || g_path_calls != 3 ||
	    meta.output_row_count != 3 || meta.revalidated_row_count != 3 ||
	    meta.additional_second_pid_count != 0 ||
	    g_output_rows[0].pid != 70001 || g_output_rows[0].ppid != 1 ||
	    g_output_rows[0].birth_seconds != 1700000000 ||
	    g_output_rows[0].birth_microseconds != 10 ||
	    g_output_rows[0].state != DFB_STATE_R ||
	    g_output_rows[0].native_snapshot_origin != DFB_NATIVE_ORIGIN_FIRST_TABLE ||
	    g_output_rows[0].revalidation_witness != DFB_REVALIDATION_MATCHED_SECOND_TABLE ||
	    g_output_rows[0].command_length != strlen("/synthetic/70001") ||
	    g_output_rows[0].command_path_status != DFB_COMMAND_PATH_RESOLVED ||
	    g_output_rows[1].state != DFB_STATE_S ||
	    g_output_rows[1].pid != 70002 || g_output_rows[1].ppid != 70001 ||
	    g_output_rows[1].birth_seconds != 1700000001 ||
	    g_output_rows[1].birth_microseconds != 20 ||
	    g_output_rows[1].command_length != strlen("synthetic-worker") ||
	    g_output_rows[1].command_path_status != DFB_COMMAND_PATH_SHORT_COMM_FALLBACK ||
	    g_output_rows[1].native_snapshot_origin != DFB_NATIVE_ORIGIN_FIRST_TABLE ||
	    g_output_rows[1].revalidation_witness != DFB_REVALIDATION_MATCHED_SECOND_TABLE ||
	    g_output_rows[2].state != DFB_STATE_Z ||
	    g_output_rows[2].pid != 70003 || g_output_rows[2].ppid != 70001 ||
	    g_output_rows[2].birth_seconds != 1700000002 ||
	    g_output_rows[2].birth_microseconds != 30 ||
	    g_output_rows[2].command_length != strlen("/synthetic/70003") ||
	    g_output_rows[2].command_path_status != DFB_COMMAND_PATH_RESOLVED ||
	    g_output_rows[0].command_source != DFB_COMMAND_SOURCE_PROC_PIDPATH ||
	    g_output_rows[1].command_source != DFB_COMMAND_SOURCE_KINFO_P_COMM ||
	    g_output_rows[2].command_source != DFB_COMMAND_SOURCE_PROC_PIDPATH ||
	    strcmp(g_output_rows[0].command, "/synthetic/70001") != 0 ||
	    strcmp(g_output_rows[1].command, "synthetic-worker") != 0 ||
	    strcmp(g_output_rows[2].command, "/synthetic/70003") != 0) {
		(void)fprintf(stderr, "FAIL complete-positive/legacy-state-map\n");
		g_failures++;
		return;
	}
	(void)printf("PASS complete-positive/legacy-state-map\n");
	g_passes++;
}

static void
test_sstop_maps_to_t(void)
{
	dfb_native_meta_v3 meta;
	int result;

	reset_fixtures();
	g_self_pid = 70005;
	set_row(&g_tables[0], 0, g_self_pid, 1, 1700000005, 50, SSTOP,
	    "synthetic-stopped");
	g_tables[1] = g_tables[0];
	result = dfb_native_snapshot_v4(g_output_rows, DFB_MAX_ROWS, &meta);
	if (result != DFB_STATUS_OK || meta.status != DFB_STATUS_OK ||
	    meta.output_row_count != 1 || g_output_rows[0].pid != g_self_pid ||
	    g_output_rows[0].state != DFB_STATE_T ||
	    g_output_rows[0].command_path_status != DFB_COMMAND_PATH_RESOLVED) {
		(void)fprintf(stderr, "FAIL sstop-maps-to-t\n");
		g_failures++;
		return;
	}
	(void)printf("PASS sstop-maps-to-t\n");
	g_passes++;
}

static void
test_short_table(void)
{
	set_standard_pair();
	g_tables[0].override_returned_length = 1;
	g_tables[0].returned_length = 0;
	(void)expect_status("short-empty-first-table", DFB_STATUS_FIRST_ROW, 1);
}

static void
test_misaligned_table(void)
{
	set_standard_pair();
	g_tables[0].override_returned_length = 1;
	g_tables[0].returned_length = sizeof(struct kinfo_proc) - 1u;
	(void)expect_status("misaligned-first-table", DFB_STATUS_FIRST_ALIGNMENT, 1);
}

static void
test_first_enomem(void)
{
	set_standard_pair();
	g_tables[0].error_errno = ENOMEM;
	(void)expect_status("first-kern-proc-all-enomem", DFB_STATUS_FIRST_SYSCTL, 1);
}

static void
test_second_enomem(void)
{
	set_standard_pair();
	g_tables[1].error_errno = ENOMEM;
	(void)expect_status("revalidation-kern-proc-all-enomem",
	    DFB_STATUS_REVALIDATION_SYSCTL, 2);
}

static void
test_capacity_bound(void)
{
	set_standard_pair();
	g_tables[0].row_count = 0;
	g_tables[0].override_returned_length = 1;
	g_tables[0].returned_length =
	    (size_t)DFB_MAX_ROWS * sizeof(struct kinfo_proc);
	(void)expect_status("exact-row-capacity-fails-closed",
	    DFB_STATUS_FIRST_CAPACITY, 1);
}

static void
test_duplicate_pid(void)
{
	set_standard_pair();
	g_tables[0].rows[1].kp_proc.p_pid = g_self_pid;
	(void)expect_status("duplicate-first-table-pid",
	    DFB_STATUS_FIRST_DUPLICATE, 1);
}

static void
test_bad_birth(void)
{
	set_standard_pair();
	g_tables[0].rows[1].kp_proc.p_starttime.tv_sec = 0;
	(void)expect_status("invalid-birth-time", DFB_STATUS_FIRST_ROW, 1);
}

static void
test_bad_parent(void)
{
	set_standard_pair();
	g_tables[0].rows[1].kp_eproc.e_ppid = (pid_t)-1;
	(void)expect_status("invalid-parent-pid", DFB_STATUS_FIRST_ROW, 1);
}

static void
test_bad_state(void)
{
	set_standard_pair();
	g_tables[0].rows[1].kp_proc.p_stat = (char)(SZOMB + 1);
	(void)expect_status("invalid-process-state", DFB_STATUS_FIRST_ROW, 1);
}

static void
test_bad_comm(void)
{
	set_standard_pair();
	memset(g_tables[0].rows[1].kp_proc.p_comm, 'x',
	    sizeof(g_tables[0].rows[1].kp_proc.p_comm));
	(void)expect_status("unterminated-short-command", DFB_STATUS_FIRST_ROW, 1);
}

static void
test_path_fallback_errno(void)
{
	set_standard_pair();
	g_path_fallback_pid = 70002;
	g_path_fallback_errno = ENOENT;
	{
		dfb_native_meta_v3 meta;
		int result = dfb_native_snapshot_v4(g_output_rows, DFB_MAX_ROWS, &meta);
		if (result != DFB_STATUS_OK || meta.status != DFB_STATUS_OK ||
		    g_sysctl_calls != 2 || g_path_calls != 3 ||
		    meta.output_row_count != 3 || g_output_rows[1].pid != 70002 ||
		    g_output_rows[1].ppid != 70001 ||
		    g_output_rows[1].birth_seconds != 1700000001 ||
		    g_output_rows[1].birth_microseconds != 20 ||
		    g_output_rows[1].command_source != DFB_COMMAND_SOURCE_KINFO_P_COMM ||
		    g_output_rows[1].command_path_status != DFB_COMMAND_PATH_SHORT_COMM_FALLBACK ||
		    g_output_rows[1].native_snapshot_origin != DFB_NATIVE_ORIGIN_FIRST_TABLE ||
		    g_output_rows[1].revalidation_witness != DFB_REVALIDATION_MATCHED_SECOND_TABLE ||
		    g_output_rows[1].command_path_errno != ENOENT ||
		    strcmp(g_output_rows[1].command, "synthetic-worker") != 0) {
			(void)fprintf(stderr, "FAIL zero-path-enoent-fallback-retains-identity\n");
			g_failures++;
			return;
		}
	}
	(void)printf("PASS zero-path-enoent-fallback-retains-identity\n");
	g_passes++;
}

static void
test_negative_path_result(void)
{
	set_standard_pair();
	g_path_negative_pid = 70001;
	(void)expect_status("negative-proc-pidpath-result-fails",
	    DFB_STATUS_PROC_PIDPATH, 1);
}

static void
test_path_with_errno(void)
{
	set_standard_pair();
	g_path_positive_error_pid = 70001;
	(void)expect_status("positive-path-with-errno-fails",
	    DFB_STATUS_PROC_PIDPATH, 1);
}

static void
test_unterminated_path(void)
{
	set_standard_pair();
	g_path_unterminated_pid = 70001;
	(void)expect_status("unterminated-proc-pidpath-fails",
	    DFB_STATUS_PROC_PIDPATH, 1);
}

static void
test_overbound_path(void)
{
	set_standard_pair();
	g_path_overbound_pid = 70001;
	(void)expect_status("overbound-proc-pidpath-fails",
	    DFB_STATUS_PROC_PIDPATH, 1);
}

static void
test_second_missing_pid(void)
{
	dfb_native_meta_v3 meta;
	int result;

	set_standard_pair();
	g_tables[1].row_count = 0;
	set_row(&g_tables[1], 0, 70001, 1, 1700000000, 10, SIDL,
	    "synthetic-self");
	set_row(&g_tables[1], 1, 70003, 70001, 1700000002, 30, SZOMB,
	    "synthetic-zombie");
	set_row(&g_tables[1], 2, 70004, 1, 1700000004, 40, SRUN,
	    "new-observation");
	result = dfb_native_snapshot_v4(g_output_rows, DFB_MAX_ROWS, &meta);
	if (result != DFB_STATUS_OK || meta.status != DFB_STATUS_OK ||
	    g_sysctl_calls != 2 || g_path_calls != 3 ||
	    meta.first_record_count != 3 || meta.second_record_count != 3 ||
	    meta.revalidated_row_count != 2 ||
	    meta.first_table_only_pid_count != 1 ||
	    meta.additional_second_pid_count != 1 || meta.output_row_count != 4 ||
	    g_output_rows[1].pid != 70002 || g_output_rows[1].ppid != 70001 ||
	    g_output_rows[1].birth_seconds != 1700000001 ||
	    g_output_rows[1].birth_microseconds != 20 ||
	    g_output_rows[1].state != DFB_STATE_S ||
	    g_output_rows[1].command_source != DFB_COMMAND_SOURCE_KINFO_FIRST_TABLE_ONLY ||
	    g_output_rows[1].command_length != strlen("synthetic-worker") ||
	    g_output_rows[1].command_path_errno != 0 ||
	    g_output_rows[1].command_path_status != DFB_COMMAND_PATH_DISCARDED_UNREVALIDATED_FIRST_TABLE_ONLY ||
	    g_output_rows[1].native_snapshot_origin != DFB_NATIVE_ORIGIN_FIRST_TABLE_ONLY ||
	    g_output_rows[1].revalidation_witness != DFB_REVALIDATION_FIRST_TABLE_ONLY_UNVERIFIED ||
	    strcmp(g_output_rows[1].command, "synthetic-worker") != 0 ||
	    g_output_rows[2].pid != 70003 ||
	    g_output_rows[2].revalidation_witness != DFB_REVALIDATION_MATCHED_SECOND_TABLE ||
	    g_output_rows[3].pid != 70004 ||
	    g_output_rows[3].revalidation_witness != DFB_REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED) {
		(void)fprintf(stderr, "FAIL first-table-only-row-keeps-kernel-identity-not-path\n");
		g_failures++;
		return;
	}
	(void)printf("PASS first-table-only-row-keeps-kernel-identity-not-path\n");
	g_passes++;
}

static void
test_first_only_errno_from_attempt_is_retained(void)
{
	dfb_native_meta_v3 meta;
	int result;

	set_standard_pair();
	g_tables[1].row_count = 1;
	g_path_fallback_pid = 70002;
	g_path_fallback_errno = ENOENT;
	result = dfb_native_snapshot_v4(g_output_rows, DFB_MAX_ROWS, &meta);
	if (result != DFB_STATUS_OK || g_path_calls != 3 ||
	    meta.first_table_only_pid_count != 2 ||
	    g_output_rows[1].pid != 70002 ||
	    g_output_rows[1].command_source != DFB_COMMAND_SOURCE_KINFO_FIRST_TABLE_ONLY ||
	    g_output_rows[1].command_path_status != DFB_COMMAND_PATH_DISCARDED_UNREVALIDATED_FIRST_TABLE_ONLY ||
	    g_output_rows[1].command_path_errno != ENOENT ||
	    strcmp(g_output_rows[1].command, "synthetic-worker") != 0) {
		(void)fprintf(stderr, "FAIL first-only-retains-actual-path-attempt-errno\n");
		g_failures++;
		return;
	}
	(void)printf("PASS first-only-retains-actual-path-attempt-errno\n");
	g_passes++;
}

static void
test_two_first_only_rows_are_explicitly_counted(void)
{
	dfb_native_meta_v3 meta;
	int result;

	set_standard_pair();
	g_tables[1].row_count = 1;
	result = dfb_native_snapshot_v4(g_output_rows, DFB_MAX_ROWS, &meta);
	if (result != DFB_STATUS_OK || meta.first_table_only_pid_count != 2 ||
	    meta.revalidated_row_count != 1 || meta.output_row_count != 3 ||
	    g_output_rows[1].native_snapshot_origin != DFB_NATIVE_ORIGIN_FIRST_TABLE_ONLY ||
	    g_output_rows[2].native_snapshot_origin != DFB_NATIVE_ORIGIN_FIRST_TABLE_ONLY) {
		(void)fprintf(stderr, "FAIL multiple-first-only-rows-remain-explicit\n");
		g_failures++;
		return;
	}
	(void)printf("PASS multiple-first-only-rows-remain-explicit\n");
	g_passes++;
}

static void
test_pid_reuse(void)
{
	set_standard_pair();
	g_tables[1].rows[1].kp_proc.p_starttime.tv_sec++;
	(void)expect_status("revalidation-birth-identity-changed",
	    DFB_STATUS_REVALIDATION_CHANGED, 2);
}

static void
test_parent_change(void)
{
	set_standard_pair();
	g_tables[1].rows[1].kp_eproc.e_ppid = 42;
	(void)expect_status("revalidation-parent-changed",
	    DFB_STATUS_REVALIDATION_CHANGED, 2);
}

static void
test_additional_second_table_pid(void)
{
	dfb_native_meta_v3 meta;
	int result;

	reset_fixtures();
	g_self_pid = 70001;
	set_row(&g_tables[0], 0, g_self_pid, 1, 1700000000, 10, SIDL,
	    "synthetic-self");
	set_row(&g_tables[1], 0, g_self_pid, 1, 1700000000, 10, SIDL,
	    "synthetic-self");
	set_row(&g_tables[1], 1, 70004, 1, 1700000003, 40, SRUN,
	    "new-observation");
	g_sysctl_calls = 0;
	g_path_calls = 0;
	result = dfb_native_snapshot_v4(g_output_rows, DFB_MAX_ROWS, &meta);
	if (result != DFB_STATUS_OK || meta.status != DFB_STATUS_OK ||
	    g_sysctl_calls != 2 || g_path_calls != 1 || meta.output_row_count != 2 ||
	    meta.revalidated_row_count != 1 || meta.first_record_count != 1 ||
	    meta.second_record_count != 2 || meta.additional_second_pid_count != 1 ||
	    meta.excluded_pid0_count != 0 || meta.second_excluded_pid0_count != 0 ||
	    g_output_rows[0].pid != g_self_pid ||
	    g_output_rows[1].pid != 70004 || g_output_rows[1].ppid != 1 ||
	    g_output_rows[1].birth_seconds != 1700000003 ||
	    g_output_rows[1].birth_microseconds != 40 ||
	    g_output_rows[1].state != DFB_STATE_S ||
	    g_output_rows[1].command_source != DFB_COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW ||
	    g_output_rows[1].command_length != strlen("new-observation") ||
	    g_output_rows[1].command_path_errno != DFB_PATH_ERRNO_NOT_ATTEMPTED ||
	    g_output_rows[1].command_path_status != DFB_COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW ||
	    g_output_rows[1].native_snapshot_origin != DFB_NATIVE_ORIGIN_SECOND_TABLE_ONLY ||
	    g_output_rows[1].revalidation_witness != DFB_REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED ||
	    strcmp(g_output_rows[1].command, "new-observation") != 0) {
		(void)fprintf(stderr, "FAIL additional-second-table-pid-retained-with-typed-identity\n");
		g_failures++;
		return;
	}
	(void)printf("PASS additional-second-table-pid-retained-with-typed-identity\n");
	g_passes++;
}

static void
test_duplicate_second_table_pid(void)
{
	set_standard_pair();
	set_row(&g_tables[1], 3, 70002, 70001, 1700000001, 20, SRUN,
	    "synthetic-worker");
	(void)expect_status("duplicate-revalidation-table-pid",
	    DFB_STATUS_REVALIDATION_DUPLICATE, 2);
}

static void
test_bad_second_only_fields(void)
{
	set_standard_pair();
	set_row(&g_tables[1], 3, 70004, 1, 1700000004, 40, SRUN, "new-worker");
	g_tables[1].rows[3].kp_proc.p_starttime.tv_sec = 0;
	(void)expect_status("invalid-second-only-birth", DFB_STATUS_REVALIDATION_ROW, 2);

	set_standard_pair();
	set_row(&g_tables[1], 3, 70004, 1, 1700000004, 40, SRUN, "new-worker");
	g_tables[1].rows[3].kp_eproc.e_ppid = (pid_t)-1;
	(void)expect_status("invalid-second-only-parent", DFB_STATUS_REVALIDATION_ROW, 2);

	set_standard_pair();
	set_row(&g_tables[1], 3, 70004, 1, 1700000004, 40, SZOMB + 1, "new-worker");
	(void)expect_status("invalid-second-only-state", DFB_STATUS_REVALIDATION_ROW, 2);

	set_standard_pair();
	set_row(&g_tables[1], 3, 70004, 1, 1700000004, 40, SRUN, "new-worker");
	memset(g_tables[1].rows[3].kp_proc.p_comm, 'x',
	    sizeof(g_tables[1].rows[3].kp_proc.p_comm));
	(void)expect_status("invalid-second-only-short-comm", DFB_STATUS_REVALIDATION_ROW, 2);
}

static void
test_second_table_capacity_bound(void)
{
	set_standard_pair();
	g_tables[1].row_count = 0;
	g_tables[1].override_returned_length = 1;
	g_tables[1].returned_length =
	    (size_t)DFB_MAX_ROWS * sizeof(struct kinfo_proc);
	(void)expect_status("exact-revalidation-row-capacity-fails-closed",
	    DFB_STATUS_REVALIDATION_CAPACITY, 2);
}

int
main(void)
{
	g_output_rows = calloc(DFB_MAX_ROWS, sizeof(*g_output_rows));
	if (g_output_rows == NULL) {
		(void)fprintf(stderr, "FAIL output allocation\n");
		return 2;
	}
	test_complete_positive_and_legacy_states();
	test_sstop_maps_to_t();
	test_short_table();
	test_misaligned_table();
	test_first_enomem();
	test_second_enomem();
	test_capacity_bound();
	test_duplicate_pid();
	test_bad_birth();
	test_bad_parent();
	test_bad_state();
	test_bad_comm();
	test_path_fallback_errno();
	test_negative_path_result();
	test_path_with_errno();
	test_unterminated_path();
	test_overbound_path();
	test_second_missing_pid();
	test_first_only_errno_from_attempt_is_retained();
	test_two_first_only_rows_are_explicitly_counted();
	test_pid_reuse();
	test_parent_change();
	test_additional_second_table_pid();
	test_duplicate_second_table_pid();
	test_bad_second_only_fields();
	test_second_table_capacity_bound();
	free(g_output_rows);
	(void)printf("%d passed, %d failed\n", g_passes, g_failures);
	return g_failures == 0 ? 0 : 1;
}
