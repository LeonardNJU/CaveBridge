/*
 * SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
 * SPDX-License-Identifier: BSD-2-Clause
 *
 * Minimal readline()/add_history() replacement for builds without libedit
 * (e.g. native Windows). Enabled only with -DADVENT_NO_EDITLINE; the default
 * build still uses <editline/readline.h> and is byte-for-byte unchanged.
 *
 * CaveBridge drives the engine over a pipe and provides line-editing itself,
 * so interactive editing is unused here — a plain line read is equivalent.
 */
#ifndef ADVENT_EDITLINE_SHIM_H
#define ADVENT_EDITLINE_SHIM_H

#include <stdio.h>
#include <stdlib.h>

/* Read one line from stdin. Returns a malloc'd string without the trailing
 * newline, or NULL at end-of-input (matching readline()'s contract). */
static inline char *readline(const char *prompt) {
	if (prompt != NULL) {
		fputs(prompt, stdout);
		fflush(stdout);
	}
	size_t cap = 256, len = 0;
	char *buf = (char *)malloc(cap);
	if (buf == NULL) {
		return NULL;
	}
	int c;
	while ((c = getchar()) != EOF && c != '\n') {
		if (len + 1 >= cap) {
			cap *= 2;
			char *grown = (char *)realloc(buf, cap);
			if (grown == NULL) {
				free(buf);
				return NULL;
			}
			buf = grown;
		}
		buf[len++] = (char)c;
	}
	if (c == EOF && len == 0) {
		free(buf);
		return NULL;
	}
	buf[len] = '\0';
	return buf;
}

static inline void add_history(const char *line) { (void)line; }

#endif /* ADVENT_EDITLINE_SHIM_H */
