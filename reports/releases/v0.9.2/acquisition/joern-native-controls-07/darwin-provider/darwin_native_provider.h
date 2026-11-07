#ifndef DFB_DARWIN_NATIVE_PROVIDER_H
#define DFB_DARWIN_NATIVE_PROVIDER_H

#include <stdint.h>

#if defined(__clang__) || defined(__GNUC__)
#define DFB_EXPORT __attribute__((visibility("default")))
#else
#define DFB_EXPORT
#endif

#define DFB_ABI_VERSION 3u
#define DFB_MAX_ROWS 8192u
#define DFB_MAX_COMMAND_BYTES 4096u
#define DFB_COMMAND_CAPACITY (DFB_MAX_COMMAND_BYTES + 1u)

enum dfb_state_v1 {
	DFB_STATE_R = 'R',
	DFB_STATE_S = 'S',
	DFB_STATE_T = 'T',
	DFB_STATE_Z = 'Z'
};

enum dfb_command_source_v3 {
	DFB_COMMAND_SOURCE_PROC_PIDPATH = 1,
	DFB_COMMAND_SOURCE_KINFO_P_COMM = 2,
	DFB_COMMAND_SOURCE_KINFO_SECOND_TABLE_NEW = 3
};

enum dfb_command_path_status_v1 {
	DFB_COMMAND_PATH_RESOLVED = 1,
	DFB_COMMAND_PATH_SHORT_COMM_FALLBACK = 2,
	DFB_COMMAND_PATH_NOT_ATTEMPTED_SECOND_TABLE_NEW = 3
};

enum dfb_native_snapshot_origin_v1 {
	DFB_NATIVE_ORIGIN_FIRST_TABLE = 1,
	DFB_NATIVE_ORIGIN_SECOND_TABLE_ONLY = 2
};

enum dfb_revalidation_witness_v1 {
	DFB_REVALIDATION_MATCHED_SECOND_TABLE = 1,
	DFB_REVALIDATION_SECOND_TABLE_ONLY_UNVERIFIED = 2
};

#define DFB_PATH_ERRNO_NOT_ATTEMPTED (-1)

enum dfb_api_v1 {
	DFB_API_NONE = 0,
	DFB_API_FIRST_KERN_PROC_ALL = 1,
	DFB_API_PROC_PIDPATH = 2,
	DFB_API_REVALIDATION_KERN_PROC_ALL = 3,
	DFB_API_ROW_VALIDATION = 4,
	DFB_API_ALLOCATION = 5,
	DFB_API_ARGUMENT_VALIDATION = 6
};

enum dfb_status_v1 {
	DFB_STATUS_OK = 0,
	DFB_STATUS_INVALID_ARGUMENT = 1,
	DFB_STATUS_ALLOCATION = 2,
	DFB_STATUS_FIRST_SYSCTL = 3,
	DFB_STATUS_FIRST_CAPACITY = 4,
	DFB_STATUS_FIRST_ALIGNMENT = 5,
	DFB_STATUS_FIRST_ROW = 6,
	DFB_STATUS_FIRST_DUPLICATE = 7,
	DFB_STATUS_PROC_PIDPATH = 8,
	DFB_STATUS_REVALIDATION_SYSCTL = 9,
	DFB_STATUS_REVALIDATION_CAPACITY = 10,
	DFB_STATUS_REVALIDATION_ALIGNMENT = 11,
	DFB_STATUS_REVALIDATION_ROW = 12,
	DFB_STATUS_REVALIDATION_DUPLICATE = 13,
	DFB_STATUS_REVALIDATION_MISSING = 14,
	DFB_STATUS_REVALIDATION_CHANGED = 15
};

typedef struct dfb_native_row_v3 {
	int32_t pid;
	int32_t ppid;
	uint64_t birth_seconds;
	uint32_t birth_microseconds;
	uint32_t state;
	uint32_t command_source;
	uint32_t command_length;
	int32_t command_path_errno;
	uint32_t command_path_status;
	uint32_t native_snapshot_origin;
	uint32_t revalidation_witness;
	char command[DFB_COMMAND_CAPACITY];
} dfb_native_row_v3;

typedef struct dfb_native_meta_v2 {
	uint32_t abi_version;
	uint32_t struct_size;
	int32_t status;
	int32_t api;
	int32_t error_errno;
	int32_t error_pid;
	int32_t error_returned;
	uint32_t error_expected;
	uint64_t first_bytes;
	uint64_t second_bytes;
	uint64_t table_capacity_bytes;
	uint32_t record_size;
	uint32_t first_record_count;
	uint32_t second_record_count;
	uint32_t output_row_count;
	uint32_t revalidated_row_count;
	uint32_t additional_second_pid_count;
	uint32_t excluded_pid0_count;
	uint32_t second_excluded_pid0_count;
} dfb_native_meta_v2;

DFB_EXPORT uint32_t dfb_native_abi_version(void);
DFB_EXPORT uint32_t dfb_native_max_rows(void);
DFB_EXPORT uint32_t dfb_native_max_command_bytes(void);
DFB_EXPORT uint32_t dfb_native_max_short_comm_bytes(void);
DFB_EXPORT uint32_t dfb_native_row_size(void);
DFB_EXPORT uint32_t dfb_native_meta_size(void);
DFB_EXPORT int32_t dfb_native_snapshot_v3(dfb_native_row_v3 *rows,
	uint32_t capacity, dfb_native_meta_v2 *meta);

#endif
