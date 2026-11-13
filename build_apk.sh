#!/usr/bin/env bash
# Buduje APK MultiSnake dla obu architektur: armeabi-v7a (32-bit)
# i arm64-v8a (64-bit). Wynik: bin/multisnake-0.1-<arch>-debug.apk
#
# Użycie:  ./build_apk.sh           — oba buildy
#          ./build_apk.sh arm64-v8a — tylko jeden arch

set -u
cd "$(dirname "$0")"

SPEC=buildozer.spec
ORIG_ARCH=$(grep -oP '^android\.archs = \K.*' "$SPEC")

ARCHS=("$@")
[ ${#ARCHS[@]} -eq 0 ] && ARCHS=(armeabi-v7a arm64-v8a)

restore_spec() { sed -i "s/^android\.archs = .*/android.archs = $ORIG_ARCH/" "$SPEC"; }
trap restore_spec EXIT

export PATH="$HOME/.local/bin:$PATH"
export PIP_BREAK_SYSTEM_PACKAGES=1
export JAVA_HOME="$HOME/.local/jdks/jdk-21.0.13+9"

FAILED=()
for arch in "${ARCHS[@]}"; do
    echo "========== BUILD: $arch =========="
    sed -i "s/^android\.archs = .*/android.archs = $arch/" "$SPEC"
    if ~/.local/bin/buildozer android debug; then
        echo "========== OK: bin/multisnake-0.1-$arch-debug.apk =========="
    else
        echo "========== FAIL: $arch =========="
        FAILED+=("$arch")
    fi
done

echo
echo "======= PODSUMOWANIE ======="
ls -lh bin/*.apk 2>/dev/null
if [ ${#FAILED[@]} -gt 0 ]; then
    echo "Nieudane: ${FAILED[*]}"
    exit 1
fi
echo "Wszystkie buildy OK."
