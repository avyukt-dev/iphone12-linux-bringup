/* SPDX-License-Identifier: MIT
 * Host-testable early Linux PID 1 for the iPhone 12 bring-up project.
 * This is NOT an A14 kernel, bootloader, driver or verified boot path.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <termios.h>
#include <unistd.h>

static void mount_optional(const char *source, const char *target, const char *type)
{
    if (mount(source, target, type, MS_NOSUID | MS_NOEXEC | MS_NODEV, NULL) != 0)
        fprintf(stderr, "early-init: mount %s failed: %s\n", target, strerror(errno));
}

static void run_console_shell(void)
{
    /* A child shell may exit without killing PID 1. Do not claim SSH/networking. */
    for (;;) {
        pid_t child = fork();
        if (child < 0) {
            fprintf(stderr, "early-init: fork failed: %s\n", strerror(errno));
            sleep(5);
            continue;
        }
        if (child == 0) {
            (void)setsid();
            int fd = open("/dev/console", O_RDWR);
            if (fd < 0) {
                fprintf(stderr, "early-init: cannot open /dev/console: %s\n", strerror(errno));
                _exit(127);
            }
            (void)ioctl(fd, TIOCSCTTY, 0);
            if (dup2(fd, STDIN_FILENO) < 0 ||
                dup2(fd, STDOUT_FILENO) < 0 ||
                dup2(fd, STDERR_FILENO) < 0)
                _exit(127);
            if (fd > STDERR_FILENO)
                close(fd);
            (void)setenv("PATH", "/bin", 1);
            (void)setenv("HOME", "/", 1);
            execl("/bin/sh", "sh", "-i", (char *)NULL);
            fprintf(stderr, "early-init: exec /bin/sh failed: %s\n", strerror(errno));
            _exit(127);
        }
        int status;
        while (waitpid(child, &status, 0) == -1 && errno == EINTR) {
        }
        fprintf(stderr, "early-init: shell exited; restarting\n");
        sleep(2);
    }
}

int main(int argc, char **argv)
{
    struct utsname info;
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    if (argc == 2 && strcmp(argv[1], "--self-test") == 0) {
        puts("A14_HOST_EARLY_INIT_SELF_TEST_OK");
        return 0;
    }
    puts("early-init: starting host-built ARM64 userspace; A14 boot unverified");
    if (uname(&info) == 0)
        printf("early-init: kernel=%s machine=%s\n", info.release, info.machine);
    mount_optional("proc", "/proc", "proc");
    mount_optional("sysfs", "/sys", "sysfs");
    if (mount("devtmpfs", "/dev", "devtmpfs", MS_NOSUID, NULL) != 0)
        fprintf(stderr, "early-init: devtmpfs unavailable: %s\n", strerror(errno));

    if (access("/bin/sh", X_OK) == 0) {
        puts("early-init: launching interactive /dev/console shell; networking is not configured");
        run_console_shell();
    }
    puts("early-init: /bin/sh not available; keeping PID 1 alive");
    for (;;)
        sleep(30);
}
