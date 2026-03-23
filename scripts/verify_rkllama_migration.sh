#!/usr/bin/env sh
set -eu

API_URL="${1:-http://127.0.0.1:11435}"
LEGACY_ROOT="${2:-/root/.ollama/models/manifests}"

echo "Checking RKLLama migration status"
echo "API URL: ${API_URL}"
echo "Legacy manifests: ${LEGACY_ROOT}"

if [ ! -d "${LEGACY_ROOT}" ]; then
  echo "Legacy manifest directory not found. Nothing to compare."
  exit 0
fi

LEGACY_MODELS=$(find "${LEGACY_ROOT}" -type f | sed 's#\\#/#g' | awk -F'/manifests/' 'NF>1 {print $2}' | awk -F'/' '
  {
    if (NF >= 3) {
      tag=$NF
      model=$(NF-1)
      if ($(NF-2) != "library") {
        model=$(NF-2) "/" model
      }
      print model ":" tag
    }
  }
' | sort -u)

if [ -z "${LEGACY_MODELS}" ]; then
  echo "No legacy model names discovered in manifests."
  exit 0
fi

TAGS_JSON=$(curl -fsS "${API_URL}/api/tags" || true)
if [ -z "${TAGS_JSON}" ]; then
  echo "Could not query ${API_URL}/api/tags"
  exit 1
fi
TAGS_COMPACT=$(echo "${TAGS_JSON}" | tr -d '[:space:]')

echo ""
echo "Legacy model names:"
echo "${LEGACY_MODELS}" | sed 's/^/  - /'

echo ""
echo "Migration check results:"
MISSING=0
for model in ${LEGACY_MODELS}; do
  if [ -z "${model}" ]; then
    continue
  fi
  if echo "${TAGS_COMPACT}" | grep -Fq "\"name\":\"${model}\""; then
    echo "  OK      ${model}"
  else
    echo "  MISSING ${model}"
    MISSING=1
  fi
done

if [ "${MISSING}" -eq 1 ]; then
  echo ""
  echo "One or more models are missing in RKLLama."
  echo "Try manual pull with:"
  echo "  curl -X POST ${API_URL}/api/pull -H Content-Type:application/json -d '{\"model\":\"MODEL:TAG\",\"stream\":false}'"
  exit 2
fi

echo ""
echo "All discovered legacy model names are present in RKLLama."
