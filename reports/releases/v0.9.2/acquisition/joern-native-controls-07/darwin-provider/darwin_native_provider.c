#define _DARWIN_C_SOURCE 1

#include <errno.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/proc.h>
#include <sys/sysctl.h>
#include <sys/types.h>
#include <libproc.h>
#include "darwin_native_provider.h"

#if !defined(__APPLE__) || !defined(__LP64__)
#error "This provider supports only LP64 macOS"
#endif

#define DFB_HASH_SLOTS (DFB_MAX_ROWS * 2u)

_Static_assert(sizeof(void *) == 8, "expected LP64 pointers");
_Static_assert(sizeof(pid_t) <= sizeof(int32_t), "pid_t must fit the fixed ABI");
_Static_assert(sizeof(((struct extern_proc *)0)->p_comm) == MAXCOMLEN + 1,
    "unexpected SDK p_comm layout");
_Static_assert(sizeof(struct kinfo_proc) <= SIZE_MAX / DFB_MAX_ROWS,
    "fixed process table allocation size overflows size_t");
_Static_assert(DFB_COMMAND_CAPACITY > MAXCOMLEN + 1,
    "command output must hold the SDK short-name fallback");
_Static_assert((DFB_HASH_SLOTS & (DFB_HASH_SLOTS - 1u)) == 0,
    "hash slot count must be a power of two");

_Static_assert(sizeof(((dfb_native_row_v3 *)0)->command) == DFB_COMMAND_CAPACITY,
    "fixed command field size changed");
_Static_assert(sizeof(((dfb_native_meta_v2 *)0)->status) == sizeof(int32_t),
    "fixed status field size changed");
_Static_assert(sizeof(((dfb_native_row_v3 *)0)->native_snapshot_origin) == sizeof(uint32_t),
	"snapshot-origin field size changed");
_Static_assert(sizeof(((dfb_native_row_v3 *)0)->revalidation_witness) == sizeof(uint32_t),
	"revalidation-witness field size changed");

DFB_EXPORT uint32_t
dfb_native_abi_version(void)
{
	return DFB_ABI_VERSION;
}

DFB_EXPORT uint32_t
dfb_native_max_rows(void)
{
	return DFB_MAX_ROWS;
}

DFB_EXPORT uint32_t
dfb_native_max_command_bytes(void)
{
	return DFB_MAX_COMMAND_BYTES;
}

DFB_EXPORT uint32_t
dfb_native_max_short_comm_bytes(void)
{
	return MAXCOMLEN;
}

DFB_EXPORT uint32_t
dfb_native_row_size(void)
{
	return (uint32_t)sizeof(dfb_native_row_v3);
}

DFB_EXPORT uint32_t
dfb_native_meta_size(void)
{
	return (uint32_t)sizeof(dfb_native_meta_v2);
}

static void
set_failure(dfb_native_meta_v2 *meta, int32_t status, int32_t api,
    int saved_errno, int32_t pid, int32_t returned, uint32_t expected)
{
	meta->status = status;
	meta->api = api;
	meta->error_errno = saved_errno;
	meta->error_pid = pid;
	meta->error_returned = returned;
	meta->error_expected = expected;
	meta->output_row_count = 0;
	meta->revalidated_row_count = 0;
}

static int
fetch_all(struct kinfo_proc *buffer, size_t capacity_bytes,
    uint64_t *returned_bytes, int *saved_errno)
{
	int mib[3] = { CTL_KERN, KERN_PROC, KERN_PROC_ALL };
	size_t length = capacity_bytes;
	int rc;

	errno = 0;
	rc = sysctl(mib, (u_int)(sizeof(mib) / sizeof(mib[0])), buffer,
	    &length, NULL, 0);
	*saved_errno = errno;
	*returned_bytes = (uint64_t)length;
	return rc;
}

static uint32_t
pid_hash(int32_t pid)
{
	return ((uint32_t)pid * 2654435761u) & (DFB_HASH_SLOTS - 1u);
}

static int
validate_record(const struct kinfo_proc *record, int32_t *pid_out,
    int32_t *ppid_out, uint64_t *seconds_out, uint32_t *microseconds_out,
    uint32_t *state_out, size_t *comm_length_out)
{
	int32_t pid = (int32_t)record->kp_proc.p_pid;
	int32_t ppid = (int32_t)record->kp_eproc.e_ppid;
	int64_t seconds = (int64_t)record->kp_proc.p_starttime.tv_sec;
	int64_t microseconds = (int64_t)record->kp_proc.p_starttime.tv_usec;
	int state = (unsigned char)record->kp_proc.p_stat;
	const char *comm = record->kp_proc.p_comm;
	size_t comm_length;

	if (pid <= 0 || ppid < 0 || seconds <= 0 || microseconds < 0 ||
	    microseconds >= 1000000 || state < SIDL || state > SZOMB) {
		return 0;
	}
	comm_length = strnlen(comm, sizeof(record->kp_proc.p_comm));
	if (comm_length == 0 || comm_length >= sizeof(record->kp_proc.p_comm) ||
	    comm_length > DFB_MAX_COMMAND_BYTES) {
		return 0;
	}

	*pid_out = pid;
	*ppid_out = ppid;
	*seconds_out = (uint64_t)seconds;
	*microseconds_out = (uint32_t)microseconds;
	if (state == SIDL) {
		*state_out = DFB_STATE_R;
	} else if (state == SSTOP) {
		*state_out = DFB_STATE_T;
	} else if (state == SZOMB) {
		*state_out = DFB_STATE_Z;
	} else {
		*state_out = DFB_STATE_S;
	}
	*comm_length_out = comm_length;
	return 1;
}

static int
insert_pid(int32_t *slots, uint32_t *indices, int32_t pid,
	uint32_t record_index, uint32_t *slot_out)
{
	uint32_t slot = pid_hash(pid);
	uint32_t probes;

	for (probes = 0; probes < DFB_HASH_SLOTS; ++probes) {
		if (slots[slot] == 0) {
			slots[slot] = pid;
			indices[slot] = record_index + 1u;
			*slot_out = slot;
			return 1;
		}
		if (slots[slot] == pid) {
			return 0;
		}
		slot = (slot + 1u) & (DFB_HASH_SLOTS - 1u);
	}
	return 0;
}

static int
find_pid_record(const int32_t *slots, const uint32_t *indices,
	int32_t pid, uint32_t *record_index_out)
{
	uint32_t slot = pid_hash(pid);
	uint32_t probes;

	for (probes = 0; probes < DFB_HASH_SLOTS; ++probes) {
		if (slots[slot] == 0) {
			return 0;
		}
		if (slots[slot] == pid) {
			*record_index_out = indices[slot] - 1u;
			return 1;
		}
		slot = (slot + 1u) & (DFB_HASH_SLOTS - 1u);
	}
	return 0;
}

static void
clear_rows(dfb_native_row_v3 *rows, uint32_t capacity)
{
	if (rows != NULL && capacity <= DFB_MAX_ROWS) {
		memset(rows, 0, (size_t)capacity * sizeof(*rows));
	}
}

DFB_EXPORT int32_t
dfb_native_snapshot_v3(dfb_native_row_v3 *rows, uint32_t capacity,
	dfb_native_meta_v2 *meta)
{
	struct kinfo_proc *first = NULL;
	struct kinfo_proc *second = NULL;
	int32_t first_slots[DFB_HASH_SLOTS] = { 0 };
	int32_t second_slots[DFB_HASH_SLOTS] = { 0 };
	uint32_t first_indices[DFB_HASH_SLOTS] = { 0 };
	uint32_t second_indices[DFB_HASH_SLOTS] = { 0 };
	size_t table_bytes;
	uint64_t returned_bytes = 0;
	size_t record_count;
	size_t second_count;
	size_t output_count = 0;
	size_t revalidated_count = 0;
	size_t additional_count = 0;
	uint32_t pid0_count = 0;
	uint32_t second_pid0_count = 0;
	uint32_t i;
	int saved_errno = 0;
	int rc;
	int32_t self_pid = (int32_t)getpid();
	int self_seen = 0;

	if (meta == NULL) {
		return DFB_STATUS_INVALID_ARGUMENT;
	}
	memset(meta, 0, sizeof(*meta));
	meta->abi_version = DFB_ABI_VERSION;
	meta->struct_size = (uint32_t)sizeof(*meta);
	meta->record_size = (uint32_t)sizeof(struct kinfo_proc);

	if (rows == NULL || capacity != DFB_MAX_ROWS) {
		set_failure(meta, DFB_STATUS_INVALID_ARGUMENT, DFB_API_ARGUMENT_VALIDATION,
		    0, 0, (int32_t)capacity, DFB_MAX_ROWS);
		return meta->status;
	}
	clear_rows(rows, capacity);
	table_bytes = (size_t)DFB_MAX_ROWS * sizeof(struct kinfo_proc);
	meta->table_capacity_bytes = (uint64_t)table_bytes;
	first = calloc(DFB_MAX_ROWS, sizeof(*first));
	second = calloc(DFB_MAX_ROWS, sizeof(*second));
	if (first == NULL || second == NULL) {
		saved_errno = errno;
		set_failure(meta, DFB_STATUS_ALLOCATION, DFB_API_ALLOCATION,
		    saved_errno, 0, 0, (uint32_t)table_bytes);
		goto done;
	}

	rc = fetch_all(first, table_bytes, &returned_bytes, &saved_errno);
	meta->first_bytes = returned_bytes;
	if (rc != 0) {
		set_failure(meta, DFB_STATUS_FIRST_SYSCTL,
		    DFB_API_FIRST_KERN_PROC_ALL, saved_errno, 0,
		    (int32_t)(returned_bytes > INT32_MAX ? INT32_MAX : returned_bytes),
		    (uint32_t)(table_bytes > UINT32_MAX ? UINT32_MAX : table_bytes));
		goto done;
	}
	if (returned_bytes > table_bytes) {
		set_failure(meta, DFB_STATUS_FIRST_CAPACITY,
		    DFB_API_FIRST_KERN_PROC_ALL, 0, 0,
		    (int32_t)(returned_bytes > INT32_MAX ? INT32_MAX : returned_bytes),
		    (uint32_t)(table_bytes > UINT32_MAX ? UINT32_MAX : table_bytes));
		goto done;
	}
	if (returned_bytes % sizeof(struct kinfo_proc) != 0) {
		set_failure(meta, DFB_STATUS_FIRST_ALIGNMENT,
		    DFB_API_FIRST_KERN_PROC_ALL, 0, 0,
		    (int32_t)(returned_bytes > INT32_MAX ? INT32_MAX : returned_bytes),
		    (uint32_t)sizeof(struct kinfo_proc));
		goto done;
	}
	record_count = (size_t)(returned_bytes / sizeof(struct kinfo_proc));
	if (record_count >= DFB_MAX_ROWS) {
		set_failure(meta, DFB_STATUS_FIRST_CAPACITY,
		    DFB_API_FIRST_KERN_PROC_ALL, 0, 0, (int32_t)record_count,
		    DFB_MAX_ROWS);
		goto done;
	}
	meta->first_record_count = (uint32_t)record_count;

	for (i = 0; i < record_count; ++i) {
		const struct kinfo_proc *record = &first[i];
		int32_t pid = (int32_t)record->kp_proc.p_pid;
		int32_t ppid;
		uint64_t seconds;
		uint32_t microseconds;
		uint32_t state;
		size_t comm_length;
		dfb_native_row_v3 *row;
		uint32_t slot;
		char path[DFB_COMMAND_CAPACITY];
		int path_length;
		int path_errno;
		size_t command_length;

		if (pid == 0) {
			pid0_count++;
			if (pid0_count > 1) {
				set_failure(meta, DFB_STATUS_FIRST_DUPLICATE,
				    DFB_API_ROW_VALIDATION, 0, 0, (int32_t)i, 1);
				goto done;
			}
			continue;
		}
		if (!validate_record(record, &pid, &ppid, &seconds,
		    &microseconds, &state, &comm_length)) {
			set_failure(meta, DFB_STATUS_FIRST_ROW, DFB_API_ROW_VALIDATION,
			    0, pid, (int32_t)i, (uint32_t)record_count);
			goto done;
		}
		if (!insert_pid(first_slots, first_indices, pid, i, &slot)) {
			set_failure(meta, DFB_STATUS_FIRST_DUPLICATE, DFB_API_ROW_VALIDATION,
			    0, pid, (int32_t)i, DFB_MAX_ROWS);
			goto done;
		}
		if (pid == self_pid) {
			self_seen++;
		}

		row = &rows[output_count++];
		row->pid = pid;
		row->ppid = ppid;
		row->birth_seconds = seconds;
		row->birth_microseconds = microseconds;
		row->state = state;
		row->native_snapshot_origin = DFB_NATIVE_ORIGIN_FIRST_TABLE;
		row->revalidation_witness = DFB_REVALIDATION_MATCHED_SECOND_TABLE;

		memset(path, 0, sizeof(path));
		errno = 0;
		path_length = proc_pidpath(pid, path, DFB_MAX_COMMAND_BYTES);
		path_errno = errno;
		if (path_length < 0 || path_length > (int)DFB_MAX_COMMAND_BYTES ||
		    path_errno < 0 || (path_length > 0 && path_errno != 0)) {
			set_failure(meta, DFB_STATUS_PROC_PIDPATH, DFB_API_PROC_PIDPATH,
			    path_errno, pid, path_length, DFB_MAX_COMMAND_BYTES);
			goto done;
		}
		row->command_path_errno = path_errno;
		if (path_length == 0) {
			command_length = comm_length;
			memcpy(row->command, record->kp_proc.p_comm, command_length);
			row->command_source = DFB_COMMAND_SOURCE_KINFO_P_COMM;
			row->command_path_status = DFB_COMMAND_PATH_SHORT_COMM_FALLBACK;
		} else {
			if ((size_t)path_length >= sizeof(path) ||
			    path[path_length] != '\0' ||
			    memchr(path, '\0', (size_t)path_length) != NULL) {
				set_failure(meta, DFB_STATUS_PROC_PIDPATH, DFB_API_PROC_PIDPATH,
				    0, pid, path_length, DFB_MAX_COMMAND_BYTES);
				goto done;
			}
			command_length = (size_t)path_length;
			memcpy(row->command, path, command_length);
			row->command_source = DFB_COMMAND_SOURCE_PROC_PIDPATH;
			row->command_path_status = DFB_COMMAND_PATH_RESOLVED;
		}
		if (command_length == 0 || command_length > DFB_MAX_COMMAND_BYTES) {
			set_failure(meta, DFB_STATUS_FIRST_ROW, DFB_API_ROW_VALIDATION,
			    0, pid, (int32_t)command_length, DFB_MAX_COMMAND_BYTES);
			goto done;
		}
		row->command[command_length] = '\0';
		row->command_length = (uint32_t)command_length;
		(void)slot;
	}
	meta->excluded_pid0_count = pid0_count;
	if (self_seen != 1) {
		set_failure(meta, DFB_STATUS_FIRST_ROW, DFB_API_ROW_VALIDATION,
		    0, self_pid, self_seen, 1);
		goto done;
	}
	meta->output_row_count = (uint32_t)output_count;

	rc = fetch_all(second, table_bytes, &returned_bytes, &saved_errno);
	meta->second_bytes = returned_bytes;
	if (rc != 0) {
		set_failure(meta, DFB_STATUS_REVALIDATION_SYSCTL,
		    DFB_API_REVALIDATION_KERN_PROC_ALL, saved_errno, 0,
		    (int32_t)(returned_bytes > INT32_MAX ? INT32_MAX : returned_bytes),
		    (uint32_t)(table_bytes > UINT32_MAX ? UINT32_MAX : table_bytes));
		goto done;
	}
	if (returned_bytes > table_bytes) {
		set_failure(meta, DFB_STATUS_REVALIDATION_CAPACITY,
		    DFB_API_REVALIDATION_KERN_PROC_ALL, 0, 0,
		    (int32_t)(returned_bytes > INT32_MAX ? INT32_MAX : returned_bytes),
		    (uint32_t)(table_bytes > UINT32_MAX ? UINT32_MAX : table_bytes));
		goto done;
	}
	if (returned_bytes % sizeof(struct kinfo_proc) != 0) {
		set_failure(meta, DFB_STATUS_REVALIDATION_ALIGNMENT,
		    DFB_API_REVALIDATION_KERN_PROC_ALL, 0, 0,
		    (int32_t)(returned_bytes > INT32_MAX ? INT32_MAX : returned_bytes),
		    (uint32_t)sizeof(struct kinfo_proc));
		goto done;
	}
	second_count = (size_t)(returned_bytes / sizeof(struct kinfo_proc));
	if (second_count >= DFB_MAX_ROWS) {
		set_failure(meta, DFB_STATUS_REVALIDATION_CAPACITY,
		    DFB_API_REVALIDATION_KERN_PROC_ALL, 0, 0,
		    (int32_t)second_count, DFB_MAX_ROWS);
		goto done;
	}
	meta->second_record_count = (uint32_t)second_count;

	for (i = 0; i < second_count; ++i) {
		const struct kinfo_proc *record = &second[i];
		int32_t pid = (int32_t)record->kp_proc.p_pid;
		int32_t ppid;
		uint64_t seconds;
		uint32_t microseconds;
		uint32_t state;
		size_t comm_length;
		uint32_t slot;

		if (pid == 0) {
			second_pid0_count++;
			if (second_pid0_count > 1) {
				set_failure(meta, DFB_STATUS_REVALIDATION_DUPLICATE,
				    DFB_API_ROW_VALIDATION, 0, 0, (int32_t)i, 1);
				goto done;
			}
			continue;
		}
		if (!validate_record(record, &pid, &ppid, &seconds,
		    &microseconds, &state, &comm_length)) {
			set_failure(meta, DFB_STATUS_REVALIDATION_ROW,
			    DFB_API_ROW_VALIDATION, 0, pid, (int32_t)i,
			    (uint32_t)second_count);
			goto done;
		}
		if (!insert_pid(second_slots, second_indices, pid, i, &slot)) {
			set_failure(meta, DFB_STATUS_REVALIDATION_DUPLICATE,
			    DFB_API_ROW_VALIDATION, 0, pid, (int32_t)i, DFB_MAX_ROWS);
			goto done;
		}
		(void)ppid;
		(void)seconds;
		(void)microseconds;
		(void)state;
		(void)comm_length;
	}
	meta->second_excluded_pid0_count = second_pid0_count;

	for (i = 0; i < output_count; ++i) {
		const dfb_native_row_v3 *row = &rows[i];
		const struct kinfo_proc *after_record;
		uint32_t second_index;
		int32_t after_pid;
		int32_t after_ppid;
		uint64_t after_seconds;
		uint32_t after_microseconds;
		uint32_t after_state;
		size_t after_comm_length;

		if (!find_pid_record(second_slots, second_indices, row->pid,
		    &second_index)) {
			set_failure(meta, DFB_STATUS_REVALIDATION_MISSING,
			    DFB_API_REVALIDATION_KERN_PROC_ALL, 0, row->pid,
			    (int32_t)i, (uint32_t)output_count);
			goto done;
		}
		after_record = &second[second_index];
		if (!validate_record(after_record, &after_pid, &after_ppid,
		    &after_seconds, &after_microseconds, &after_state,
		    &after_comm_length)) {
			set_failure(meta, DFB_STATUS_REVALIDATION_ROW,
			    DFB_API_ROW_VALIDATION, 0, row->pid, (int32_t)i, 1);
			goto done;
		}
		if (after_pid != row->pid || after_ppid != row->ppid ||
		    after_seconds != row->birth_seconds ||
		    after_microseconds != row->birth_microseconds) {
			set_failure(meta, DFB_STATUS_REVALIDATION_CHANGED,
			    DFB_API_REVALIDATION_KERN_PROC_ALL, 0, row->pid,
			    (int32_t)i, (uint32_t)output_count);
			goto done;
		}
		(void)after_state;
		(void)after_comm_length;
		revalidated_count++;
	}

	for (i = 0; i < second_count; ++i) {
		const struct kinfo_proc *record = &second[i];
		int32_t pid = (int32_t)record->kp_proc.p_pid;
		uint32_t slot;
		int32_t ppid;
		uint64_t seconds;
		uint32_t microseconds;
		uint32_t state;
		size_t comm_length;
		dfb_native_row_v3 *row;

		if (pid == 0) {
			continue;
		}
		if (find_pid_record(first_slots, first_indices, pid, &slot)) {
			continue;
		}
		if (!validate_record(record, &pid, &ppid, &seconds,
		    &microseconds, &state, &comm_length)) {
			set_failure(meta, DFB_STATUS_REVALIDATION_ROW,
			    DFB_API_ROW_VALIDATION, 0, pid, (int32_t)i,
			    (uint32_t)second_count);
			goto done;
		}
		if (output_count + 1u >= DFB_MAX_ROWS) {
			set_failure(meta, DFB_STATUS_REVALIDATION_CAPACITY,
			    DFB_API_REVALIDATION_KERN_PROC_ALL, 0, pid,
			    (int32_t)output_count, DFB_MAX_ROWS - 1u);
			goto done;
		}
		row = &rows[output_count++];
		row->pid = pid;
		row->ppid = ppid;
		row->birth_seconds = seconds;
		row->birth_microseconds = microseconds;
		row->state = state;
		row->command_source = DFB_COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW;
		row->command_length = (uint32_t)comm_length;
		row->command_path_errno = DFB_PATH_ERRNO_NOT_ATTEMPTED;
		row->command_path_status = DFB_COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW;
		row->native_snapshot_origin = DFB_NATIVE_ORIGIN_SECOND_TABLE_ONLY;
		row->revalidation_witness = DFB_REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED;
		memcpy(row->command, record->kp_proc.p_comm, comm_length);
		row->command[comm_length] = '\0';
		additional_count++;
	}
	meta->additional_second_pid_count = (uint32_t)additional_count;
	meta->output_row_count = (uint32_t)output_count;
	meta->revalidated_row_count = (uint32_t)revalidated_count;
	meta->status = DFB_STATUS_OK;
	meta->api = DFB_API_NONE;
	meta->error_errno = 0;
	meta->error_pid = 0;
	meta->error_returned = 0;
	meta->error_expected = 0;

done:
	free(first);
	free(second);
	if (meta->status != DFB_STATUS_OK) {
		clear_rows(rows, capacity);
	}
	return meta->status;
}
