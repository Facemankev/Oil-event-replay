#!/usr/bin/env bash
# Market Ripple guardrails. The repo is public, so anything committed, pushed
# or posted to GitHub can be read by anyone, forever.
#
#   bash .claude/hooks/guard.sh          Claude Code runs this before every shell
#                                        command (see .claude/settings.json).
#                                        Exit 2 blocks the command and tells
#                                        Claude why.
#   bash .claude/hooks/guard.sh scan     Scans this branch's changes against
#                                        main. Used by the GitHub privacy check.
#
# Personal words to block (surnames, street names, phone numbers...) go in
# .claude/private-words.txt, one per line. That file is never committed.
# Matches that are genuinely public go in .claude/allowed-words.txt (committed),
# one exact match per line, added only by a partner.

root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
words_file="$root/.claude/private-words.txt"
allowed_file="$root/.claude/allowed-words.txt"

secret_re='(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(api[_-]?key|secret|password|passwd|token)[\\"'"'"' ]*[:=][\\"'"'"' ]*[A-Za-z0-9/+_-]{12,})'
email_re='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
phone_re='(\+44 ?7[0-9]{3}|07[0-9]{3}) ?[0-9]{3} ?[0-9]{3}'

# Prints anything private found in $1, shortened so the secret isn't repeated.
find_private() {
  {
    printf '%s\n' "$1" | grep -oiE "$secret_re"
    printf '%s\n' "$1" | grep -oE "$email_re" | grep -viE 'noreply|@example\.(com|org)$'
    printf '%s\n' "$1" | grep -oE "$phone_re"
    if [ -s "$words_file" ]; then
      printf '%s\n' "$1" | grep -oiF -f <(grep -vE '^[[:space:]]*(#|$)' "$words_file")
    fi
  } | sort -u | allowed_only | sed -E 's/^(.{4}).+/\1…/' | tr '\n' ' '
}

# Drops matches the partners have agreed are public (.claude/allowed-words.txt).
allowed_only() {
  if [ -s "$allowed_file" ]; then
    grep -viF -x -f <(grep -vE '^[[:space:]]*(#|$)' "$allowed_file")
  else
    cat
  fi
}

# Lines added by a diff, without the file headers.
added_lines() {
  git -C "$root" diff -U0 "$@" 2>/dev/null | grep '^+' | grep -v '^+++'
}

branch_base() {
  git -C "$root" merge-base HEAD origin/main 2>/dev/null || echo origin/main
}

block() {
  echo "Blocked by Market Ripple guardrails: $1" >&2
  exit 2
}

check_text() { # $1 = text, $2 = what it is
  local found
  found="$(find_private "$1")"
  [ -n "$found" ] && block "$2 contains what looks private ($found). The repo is public. Remove it. If it is genuinely public (for example a data provider's published address), ask the person; only they can add it to .claude/allowed-words.txt."
  return 0
}

if [ "${1:-}" = "scan" ]; then
  found="$(find_private "$(added_lines "$(branch_base)" HEAD)")"
  if [ -n "$found" ]; then
    echo "Possible private information added on this branch: $found" >&2
    exit 1
  fi
  echo "No private information found."
  exit 0
fi

input="$(cat)"
branch="$(git -C "$root" branch --show-current 2>/dev/null)"

case "$input" in
  *"gh repo edit"*"--visibility"*|*"gh repo delete"*|*"gh repo archive"*|*"gh repo rename"*)
    block "repository settings are changed by the owner by hand, not by the AI." ;;
esac

if printf '%s' "$input" | grep -qE 'git (-C [^ ]+ )?commit'; then
  [ "$branch" = "main" ] && block "never commit to main. Create a person/topic branch first (for example brendan/chart-colours)."
  check_text "$(added_lines --cached)" "The staged changes"
  check_text "$input" "The commit message"
fi

if printf '%s' "$input" | grep -qE 'git (-C [^ ]+ )?push'; then
  printf '%s' "$input" | grep -qE 'git (-C [^ ]+ )?push[^"]*([ :]|refs/heads/)main([ "]|$)' && block "never push to main. Push the person/topic branch and open a pull request."
  [ "$branch" = "main" ] && block "never push from main. Switch to a person/topic branch."
  printf '%s' "$input" | grep -qE -- '--mirror|--all' && block "push one branch at a time."
  check_text "$(added_lines "$(branch_base)" HEAD)" "This branch's changes"
fi

if printf '%s' "$input" | grep -qE 'gh (pr|issue|release|gist|api)'; then
  printf '%s' "$input" | grep -qE 'gh pr merge[^"]*--admin' && block "never merge with --admin. The other partner must approve."
  if printf '%s' "$input" | grep -qE 'gh pr merge'; then
    pr="$(printf '%s' "$input" | grep -oE 'gh pr merge +[0-9]+' | grep -oE '[0-9]+$')"
    decision="$(gh pr view $pr --json reviewDecision -q .reviewDecision 2>/dev/null)"
    [ "$decision" = "APPROVED" ] || block "this pull request hasn't been approved by the other partner yet (status: ${decision:-unknown})."
  fi
  check_text "$input" "This GitHub post"
  body_file="$(printf '%s' "$input" | grep -oE -- '--body-file[= ]+[^ "]+' | sed -E 's/--body-file[= ]+//')"
  [ -n "$body_file" ] && [ -f "$body_file" ] && check_text "$(cat "$body_file")" "The GitHub post's text file"
fi

exit 0
