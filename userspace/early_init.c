/* SPDX-License-Identifier: MIT
 * Host-testable early Linux PID 1 for the A14 bring-up project.
 * This program is not an A14 kernel, exploit, bootloader, or device driver.
 *
 * The initial RAM filesystem intentionally has no /bin/sh. This PID 1
 * demonstrates an ARM64 static executable and console diagnostics only.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/utsname.h>
#include <unistd.h>

static int mount_optional(const char *source, const char *target, const char *type)
{
    if (mount(source, target, type, MS_NOSUID | MS_NOEXEC | MS_NODEV, NULL) == 0)
        return 0;
    fprintf(stderr, "early-init: mount %s failed: %s\n", target, strerror(errno));
    return -1;
}

int main(int argc, char **argv)
{
    struct utsname info;
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    /*
     * QEMU user mode test proves that this is executable AArch64 Linux
     * userspace, NOT that an iPhone kernel or its console can boot.
     */
    if (argc == 2 && strcmp(argv[1], "--self-test") == 0) {
        puts("A14_HOST_EARLY_INIT_SELF_TEST_OK");
        return 0;
    }

    puts("early-init: started; no A14 boot support implied");
    if (uname(&info) == 0)
        printf("early-init: kernel=%s machine=%s\n", info.release, info.machine);
    else
        fprintf(stderr, "early-init: uname failed: %s\n", strerror(errno));

    mount_optional("proc", "/proc", "proc");
    mount_optional("sysfs", "/sys", "sysfs");
    /* devtmpfs needs real device support; failure is logged, not hidden. */
    if (mount("devtmpfs", "/dev", "devtmpfs", MS_NOSUID, NULL) != 0)
        fprintf(stderr, "early-init: devtmpfs unavailable: %s\n", strerror(errno));

    /*
     * A shell/SSH and networking are deferred until a supported kernel
     * and real serial/USB debugging exist. PID 1 must not exit on failure.
     */
    puts("early-init: no shell in this proof-of-build image; maintaining PID 1");
    for (;;)
        sleep(30);
}
